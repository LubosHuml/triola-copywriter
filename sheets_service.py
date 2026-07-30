# -*- coding: utf-8 -*-
"""
Google Sheets integrace pro Triola copywriting.

BEZPECNOSTNI ZARUKY (tvrde vynucene v kodu):
  1. Zapisuje se VYHRADNE do sloupcu uvedenych v WRITABLE_COLUMNS (copywriting vystupy).
     Jakykoli jiny sloupec je pro zapis nedostupny - viz _assert_writable().
  2. NIKDY se nemaze radek, sloupec ani list. Pouzivaji se pouze operace values.update
     (prepis konkretnich bunek) a appendDimension/update hlavicky pri pridani sloupce.
  3. Chybejici vystupni sloupec se PRIDA na konec hlavicky, stavajici sloupce se neposouvaji.
  4. Cte se pres values.get, zapisuje pres values.batchUpdate s explicitnim vyctem bunek.

Autentizace: service account JSON.
  - lokalne: soubor google_service_account.json v adresari projektu
  - na Renderu: promenna prostredi GOOGLE_SERVICE_ACCOUNT_JSON (cely obsah JSON)
"""
import os
import json
import logging
import time

from batch_service import detect_header_mapping

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "google_service_account.json")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Hlavni tabulka Triola (nativni Google Sheet, prevedeno z .xlsx 29.7.2026)
DEFAULT_SPREADSHEET_ID = "1al2pCplzQfo0w66rdcXhhe6Tgy8kaNtRutpv4CsTcN8"

# JEDINE sloupce, do kterych smi aplikace zapsat. Klic = klic ve vysledku generovani.
WRITABLE_COLUMNS = {
    "eshop_name":     ["E-SHOP NÁZEV", "Název E-shop", "E-shop název"],
    "short_name":     ["E-SHOP KRÁTKÝ NÁZEV", "E-shop krátký název", "Krátký název"],
    "eshop_desc1":    ["TRIOLA ESHOP POPIS", "Dlouhý popis (HTML)", "Popis 1"],
    "eshop_desc2":    ["TRIOLA ESHOP POPIS 2", "Popis 2"],
    "meta_title":     ["ESHOP META TITLE", "Meta Title", "Meta title"],
    "meta_desc":      ["ESHOP META DESCRIPTION", "Meta Description", "Meta description"],
    "eshop_name_sk":  ["E-SHOP NÁZEV SK", "E-shop název SK"],
    "short_name_sk":  ["E-SHOP KRÁTKÝ NÁZEV SK", "E-shop krátký název SK"],
    "eshop_desc1_sk": ["TRIOLA ESHOP POPIS SK", "Popis 1 SK"],
    "eshop_desc2_sk": ["TRIOLA ESHOP POPIS 2 SK", "Popis 2 SK"],
    "meta_title_sk":  ["ESHOP META TITLE SK", "Meta Title SK"],
    "meta_desc_sk":   ["ESHOP META DESCRIPTION SK", "Meta Description SK"],
}

_service_cache = [None]


# ---------------------------------------------------------------- autentizace

def get_credentials_info():
    """Vraci dict se service account udaji, nebo vyhodi srozumitelnou vyjimku."""
    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if raw:
        try:
            return json.loads(raw)
        except Exception as e:
            raise RuntimeError(f"GOOGLE_SERVICE_ACCOUNT_JSON neni platny JSON: {e}")
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, encoding="utf-8") as f:
            return json.load(f)
    raise RuntimeError(
        "Chybi přihlašovací údaje pro Google Sheets. Ulož service account JSON jako "
        f"'{CREDENTIALS_FILE}' nebo nastav proměnnou GOOGLE_SERVICE_ACCOUNT_JSON."
    )


def get_service():
    """Vraci autorizovanou instanci Sheets API v4."""
    if _service_cache[0] is not None:
        return _service_cache[0]
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    info = get_credentials_info()
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    _service_cache[0] = build("sheets", "v4", credentials=creds, cache_discovery=False)
    return _service_cache[0]


def get_service_account_email():
    """E-mail service accountu - uzivatel mu musi nasdilet tabulku."""
    try:
        return get_credentials_info().get("client_email", "")
    except Exception:
        return ""


# ---------------------------------------------------------------- pomocne

def col_letter(idx_zero_based):
    """0 -> A, 25 -> Z, 26 -> AA"""
    n = idx_zero_based + 1
    out = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        out = chr(65 + rem) + out
    return out


def _quote(sheet_name):
    """Nazev listu do A1 notace (apostrofy se zdvojuji)."""
    return "'" + str(sheet_name).replace("'", "''") + "'"


def _is_sk_header(h):
    hl = str(h).lower().strip()
    return hl.endswith(" sk") or hl.endswith("_sk") or hl.endswith("-sk")


# ---------------------------------------------------------------- znacka z nazvu listu

# Listy, ktere nejsou produktove nebo obsahuji mix znacek -> znacku neurcujeme
NON_BRAND_SHEETS = {"ostatní značky", "seznam kw dle zboží", "kakw", "dr.nap", "automatika"}

# Tokeny sezon/kolekci, ktere se z nazvu listu odstranuji
_SEASON_TOKENS = {
    "aw", "ss", "jl", "pz", "swim", "basic", "basic+", "plavky", "xmas",
    "lingerie", "stálá", "stala", "kolekce", "collection",
}


def brand_from_sheet_name(sheet_name):
    """
    Odvodi nazev znacky z nazvu listu: 'SASSA basic+AW26' -> 'Sassa',
    'BABELL AW26' -> 'Babell', 'Triola JL 26' -> 'Triola', 'LadyBelty AW2025' -> 'LadyBelty'.
    Vraci "" pokud znacku nelze urcit (mix znacek, pomocne listy).
    """
    import re as _re
    name = str(sheet_name or "").strip()
    if name.lower() in NON_BRAND_SHEETS:
        return ""
    # rozdel na slova, zahod sezonni tokeny, roky a cisla
    words = [w for w in _re.split(r"[\s+/,]+", name) if w]
    keep = []
    for w in words:
        base = _re.sub(r"[0-9]+$", "", w)           # 'AW26' -> 'AW'
        if not base:
            continue                                # ciste cislo (rok)
        if base.lower() in _SEASON_TOKENS:
            continue
        if _re.fullmatch(r"(?i)(aw|ss)\d*", w):
            continue
        keep.append(w)
        if len(keep) >= 2:                          # znacka je max 2 slova
            break
    if not keep:
        return ""

    def _norm(w):
        # SASSA -> Sassa, COTONELLA -> Cotonella; LadyBelty a Dorina zustavaji
        return w.capitalize() if w.isupper() else w

    return " ".join(_norm(w) for w in keep)


# Zaloha: odvozeni znacky z prefixu kodu produktu (kdyz nazev listu nepomuze)
CODE_PREFIX_BRANDS = (("SAS", "Sassa"),)


def brand_from_code(model_code):
    up = str(model_code or "").upper()
    for prefix, brand in CODE_PREFIX_BRANDS:
        if up.startswith(prefix):
            return brand
    return ""


# ---------------------------------------------------------------- retry pri rate limitu

def api_call(request, what="Sheets API", max_tries=6):
    """
    Provede request.execute() s exponencialnim backoffem pri 429 (kvota) a 5xx.
    Google Sheets API ma limit 60 cteni/min a 60 zapisu/min na uzivatele.
    """
    import random
    delay = 2.0
    last = None
    for attempt in range(1, max_tries + 1):
        try:
            return request.execute()
        except Exception as e:
            last = e
            code = getattr(getattr(e, "resp", None), "status", None)
            msg = str(e)
            transient = (code in (429, 500, 502, 503, 504)
                         or "Quota exceeded" in msg or "rateLimitExceeded" in msg)
            if not transient or attempt == max_tries:
                raise
            wait = delay + random.uniform(0, 1.5)
            logging.warning(f"{what}: limit/chyba ({code}) - čekám {wait:.1f}s "
                            f"(pokus {attempt}/{max_tries})")
            time.sleep(wait)
            delay = min(delay * 2, 60)
    raise last


def read_sheet_bundle(sheet_name, spreadsheet_id=DEFAULT_SPREADSHEET_ID, max_rows=2000):
    """
    JEDNO cteni listu -> vse potrebne pro automatiku.
    Vraci {values, header_row, mapping, headers, rows, output_columns, missing_columns}.
    Dulezite pro rate limit: nahrazuje read_sheet + resolve_output_columns + cteni hodnot.
    """
    svc = get_service()
    req = svc.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=f"{_quote(sheet_name)}!A1:ZZ{max_rows}",
        valueRenderOption="UNFORMATTED_VALUE")
    values = api_call(req, f"čtení listu '{sheet_name}'").get("values", [])
    if not values:
        return {"values": [], "header_row": 1, "mapping": {}, "headers": [],
                "rows": [], "output_columns": {}, "missing_columns": []}

    header_row, mapping = detect_header_mapping(values)
    hdr = values[header_row - 1] if header_row - 1 < len(values) else []
    n_cols = max((len(r) for r in values), default=0)
    headers = [str(hdr[i]).strip() if i < len(hdr) and hdr[i] is not None else ""
               for i in range(n_cols)]

    def cell(row, idx):
        if idx is None or idx < 0 or idx >= len(row):
            return ""
        v = row[idx]
        return str(v).strip() if v is not None else ""

    sheet_brand = brand_from_sheet_name(sheet_name)
    rows = []
    for r_i in range(header_row, len(values)):
        row = values[r_i]
        code = cell(row, mapping.get("code", -1))
        if code.endswith(".0"):
            code = code[:-2]
        if not code:
            continue
        color_raw = cell(row, mapping.get("color", -1))
        if color_raw.endswith(".0"):
            color_raw = color_raw[:-2]
        rows.append({
            "row_num": r_i + 1,
            "model_code": code,
            "color_name": color_raw,
            "arguments": cell(row, mapping.get("arguments", -1)),
            "product_name": cell(row, mapping.get("product_name", -1)),
            "design_name": cell(row, mapping.get("design_name", -1)),
            "brand": (cell(row, mapping.get("brand", -1)) or sheet_brand
                      or brand_from_code(code)),
            "material": cell(row, mapping.get("material", -1)),
            "size": cell(row, mapping.get("size", -1)),
            "has_output": bool(cell(row, mapping.get("eshop_name", -1))),
        })

    # mapovani vystupnich sloupcu ze stejnych hlavicek (bez dalsiho cteni)
    columns, used, missing = {}, set(), []
    for key, names in WRITABLE_COLUMNS.items():
        want_sk = key.endswith("_sk")
        found = -1
        for i, h in enumerate(headers):
            if i in used or not h or _is_sk_header(h) != want_sk:
                continue
            if any(n.lower().strip() == h.lower().strip() for n in names):
                found = i
                break
        if found == -1:
            for i, h in enumerate(headers):
                if i in used or not h or _is_sk_header(h) != want_sk:
                    continue
                hl = h.lower().strip()
                if any(n.lower().strip() in hl or hl in n.lower().strip() for n in names):
                    found = i
                    break
        if found != -1:
            used.add(found)
        else:
            missing.append(key)
        columns[key] = found

    return {"values": values, "header_row": header_row, "mapping": mapping,
            "headers": headers, "rows": rows, "output_columns": columns,
            "missing_columns": missing}


def create_missing_columns(sheet_name, headers, columns, missing, header_row,
                           spreadsheet_id=DEFAULT_SPREADSHEET_ID):
    """Zaklada chybejici vystupni sloupce na KONEC hlavicky. Vraci (columns, created)."""
    if not missing:
        return columns, []
    svc = get_service()
    next_col = len(headers)
    created, cells = [], []
    for key in missing:
        names = WRITABLE_COLUMNS[key]
        columns[key] = next_col
        created.append(names[0])
        cells.append({"range": f"{_quote(sheet_name)}!{col_letter(next_col)}{header_row}",
                      "values": [[names[0]]]})
        next_col += 1
    req = svc.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"valueInputOption": "RAW", "data": cells})
    api_call(req, f"přidání sloupců v '{sheet_name}'")
    logging.info(f"Přidány nové sloupce do listu '{sheet_name}': {created}")
    return columns, created


# ---------------------------------------------------------------- aktualni listy (pro automatiku)

def current_year_tokens(now=None):
    """Dvojciselne tokeny aktualniho a nasledujiciho roku: 2026 -> ('26', '27')."""
    import datetime
    now = now or datetime.date.today()
    y = now.year
    return (str(y)[2:], str(y + 1)[2:])


def is_current_sheet(sheet_name, tokens=None, include_basic=True):
    """
    Je list aktualni? Ano, pokud nazev obsahuje rok aktualni nebo nasledujici sezony
    (napr. 'Triola PZ 26', 'Dorina SS2026', 'SASSA basic+AW26').
    Pokud include_basic, berou se i trvale kolekce bez roku ('SLOGGI Basic',
    'Triola stálá kolekce') - ty se doplnuji prubezne.
    """
    import re as _re
    name = str(sheet_name or "").strip()
    if not name or name.lower() in NON_BRAND_SHEETS:
        return False
    tokens = tokens or current_year_tokens()
    for t in tokens:
        if _re.search(r"(?<!\d)(?:20)?" + _re.escape(t) + r"(?!\d)", name):
            return True
    if include_basic:
        low = name.lower()
        if _re.search(r"(?<!\d)(?:20)?\d{2}(?!\d)", name):
            return False          # ma rok, ale jiny -> stara sezona
        if "basic" in low or "stálá" in low or "stala" in low or "kolekce" in low:
            return True
    return False


def list_current_sheets(spreadsheet_id=DEFAULT_SPREADSHEET_ID, include_basic=True):
    """Vraci nazvy listu, ktere jsou aktualni pro dnesni datum."""
    info = list_sheets(spreadsheet_id)
    toks = current_year_tokens()
    return [s["title"] for s in info["sheets"]
            if is_current_sheet(s["title"], toks, include_basic)]


# ---------------------------------------------------------------- cteni

def list_sheets(spreadsheet_id=DEFAULT_SPREADSHEET_ID):
    """Vraci [{title, sheetId, rows, cols}] pro vsechny listy tabulky."""
    svc = get_service()
    meta = api_call(svc.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        fields="properties.title,sheets.properties"), "seznam listů")
    out = []
    for sh in meta.get("sheets", []):
        p = sh["properties"]
        grid = p.get("gridProperties", {})
        out.append({
            "title": p["title"],
            "sheet_id": p["sheetId"],
            "index": p.get("index", 0),
            "rows": grid.get("rowCount", 0),
            "cols": grid.get("columnCount", 0),
        })
    return {"spreadsheet_title": meta.get("properties", {}).get("title", ""), "sheets": out}


def read_sheet(sheet_name, spreadsheet_id=DEFAULT_SPREADSHEET_ID, max_rows=2000):
    """
    Nacte list a vrati:
      header_row (1-based), mapping (0-based indexy), headers (list nazvu),
      rows (list dict s daty produktu pro generovani)
    """
    svc = get_service()
    rng = f"{_quote(sheet_name)}!A1:ZZ{max_rows}"
    resp = svc.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=rng,
        valueRenderOption="UNFORMATTED_VALUE").execute()
    values = resp.get("values", [])
    if not values:
        return {"header_row": 1, "mapping": {}, "headers": [], "rows": []}

    header_row, mapping = detect_header_mapping(values)
    hdr = values[header_row - 1] if header_row - 1 < len(values) else []
    n_cols = max((len(r) for r in values), default=0)
    headers = [str(hdr[i]).strip() if i < len(hdr) and hdr[i] is not None else "" for i in range(n_cols)]

    def cell(row, idx):
        if idx is None or idx < 0 or idx >= len(row):
            return ""
        v = row[idx]
        return str(v).strip() if v is not None else ""

    sheet_brand = brand_from_sheet_name(sheet_name)

    rows = []
    for r_i in range(header_row, len(values)):
        row = values[r_i]
        code = cell(row, mapping.get("code", -1))
        if code.endswith(".0"):
            code = code[:-2]
        if not code:
            continue

        color_raw = cell(row, mapping.get("color", -1))
        if color_raw.endswith(".0"):
            color_raw = color_raw[:-2]

        # znacka: sloupec > nazev listu > prefix kodu (jinak prazdne = Triola)
        row_brand = (cell(row, mapping.get("brand", -1))
                     or sheet_brand
                     or brand_from_code(code))

        rows.append({
            "row_num": r_i + 1,                       # 1-based cislo radku v listu
            "model_code": code,
            "color_name": color_raw,
            "arguments": cell(row, mapping.get("arguments", -1)),
            "product_name": cell(row, mapping.get("product_name", -1)),
            "design_name": cell(row, mapping.get("design_name", -1)),
            "brand": row_brand,
            "material": cell(row, mapping.get("material", -1)),
            "size": cell(row, mapping.get("size", -1)),
            # nahled, zda uz radek ma vygenerovany nazev
            "has_output": bool(cell(row, mapping.get("eshop_name", -1))),
        })

    return {"header_row": header_row, "mapping": mapping, "headers": headers, "rows": rows}


# ---------------------------------------------------------------- mapovani vystupnich sloupcu

def resolve_output_columns(sheet_name, spreadsheet_id=DEFAULT_SPREADSHEET_ID, create_missing=False):
    """
    Najde (pripadne zalozi) sloupce pro copywriting vystupy.
    Vraci {"header_row": n, "columns": {key: col_idx_0based}, "created": [nazvy novych sloupcu]}
    Nove sloupce se PRIDAVAJI NA KONEC - stavajici data se neposouvaji ani nemazou.
    """
    svc = get_service()
    resp = svc.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=f"{_quote(sheet_name)}!A1:ZZ20").execute()
    values = resp.get("values", [])
    header_row, _ = detect_header_mapping(values)
    hdr = values[header_row - 1] if header_row - 1 < len(values) else []
    n_cols = max((len(r) for r in values), default=0)
    headers = [str(hdr[i]).strip() if i < len(hdr) and hdr[i] is not None else "" for i in range(n_cols)]

    columns, used, created = {}, set(), []
    for key, names in WRITABLE_COLUMNS.items():
        want_sk = key.endswith("_sk")
        found = -1
        for i, h in enumerate(headers):
            if i in used or not h or _is_sk_header(h) != want_sk:
                continue
            if any(n.lower().strip() == h.lower().strip() for n in names):
                found = i
                break
        if found == -1:
            for i, h in enumerate(headers):
                if i in used or not h or _is_sk_header(h) != want_sk:
                    continue
                hl = h.lower().strip()
                if any(n.lower().strip() in hl or hl in n.lower().strip() for n in names):
                    found = i
                    break
        if found != -1:
            used.add(found)
        columns[key] = found

    if create_missing:
        next_col = len(headers)
        new_cells = []
        for key, names in WRITABLE_COLUMNS.items():
            if columns[key] == -1:
                columns[key] = next_col
                created.append(names[0])
                new_cells.append({
                    "range": f"{_quote(sheet_name)}!{col_letter(next_col)}{header_row}",
                    "values": [[names[0]]],
                })
                next_col += 1
        if new_cells:
            svc.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"valueInputOption": "RAW", "data": new_cells}).execute()
            logging.info(f"Přidány nové sloupce do listu '{sheet_name}': {created}")

    return {"header_row": header_row, "columns": columns, "created": created}


# ---------------------------------------------------------------- zapis

def _assert_writable(key):
    if key not in WRITABLE_COLUMNS:
        raise PermissionError(
            f"Zápis do '{key}' je zakázán. Povolené sloupce: {', '.join(WRITABLE_COLUMNS)}")


def write_row_results(sheet_name, row_num, results, columns,
                      spreadsheet_id=DEFAULT_SPREADSHEET_ID, only_fill_empty=False,
                      existing_row=None):
    """
    Zapise vysledky generovani do jednoho radku.
    Zapisuje POUZE bunky ve sloupcich z 'columns' (= WRITABLE_COLUMNS).
    Nic nemaze; prazdne hodnoty se preskakuji, aby se neprepsal existujici text nicim.
    Vraci seznam zapsanych bunek (pro audit).
    """
    svc = get_service()

    # rezim doplnovani: precti aktualni stav radku a hotove texty nechej byt
    if only_fill_empty and existing_row is None:
        rng = f"{_quote(sheet_name)}!A{row_num}:ZZ{row_num}"
        got = svc.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=rng).execute().get("values", [[]])
        existing_row = got[0] if got else []

    def _has_text(col_idx):
        if not existing_row or col_idx < 0 or col_idx >= len(existing_row):
            return False
        return str(existing_row[col_idx]).strip() != ""

    data, written, skipped = [], [], []
    for key, val in results.items():
        if key not in WRITABLE_COLUMNS:
            continue                       # cizi klic ignorujeme
        _assert_writable(key)
        col = columns.get(key, -1)
        if col == -1 or val is None or str(val).strip() == "":
            continue
        if only_fill_empty and _has_text(col):
            skipped.append(key)            # uz tam text je - nepresahujeme
            continue
        a1 = f"{col_letter(col)}{row_num}"
        data.append({"range": f"{_quote(sheet_name)}!{a1}", "values": [[str(val)]]})
        written.append({"key": key, "cell": a1})

    if skipped:
        logging.info(f"Řádek {row_num}: {len(skipped)} polí přeskočeno (už mají text): "
                     f"{', '.join(skipped)}")
    if not data:
        return []

    api_call(svc.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"valueInputOption": "RAW", "data": data}), f"zápis do '{sheet_name}'")
    logging.info(f"Zapsáno {len(written)} buněk do '{sheet_name}' řádek {row_num}: "
                 f"{', '.join(w['cell'] for w in written)}")
    return written


def check_access(spreadsheet_id=DEFAULT_SPREADSHEET_ID):
    """Rychly test pripojeni a opravneni. Vraci dict se stavem - nic nemeni."""
    result = {"ok": False, "service_account": get_service_account_email(),
              "spreadsheet_id": spreadsheet_id, "can_read": False, "can_write": False,
              "error": "", "sheets": []}
    try:
        info = list_sheets(spreadsheet_id)
        result["can_read"] = True
        result["spreadsheet_title"] = info["spreadsheet_title"]
        result["sheets"] = [s["title"] for s in info["sheets"]]
    except Exception as e:
        result["error"] = f"Čtení selhalo: {e}"
        return result
    # test zapisu: precteme a zpet zapiseme identickou hodnotu do bunky hlavicky
    try:
        svc = get_service()
        first = result["sheets"][0]
        rng = f"{_quote(first)}!A1"
        cur = svc.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=rng).execute()
        val = cur.get("values", [[""]])
        svc.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=rng, valueInputOption="RAW",
            body={"values": val if val else [[""]]}).execute()
        result["can_write"] = True
        result["ok"] = True
    except Exception as e:
        result["error"] = f"Zápis selhal (nasdílej tabulku service accountu jako Editor): {e}"
    return result


# ---------------------------------------------------------------- rizeni automatiky
# List "AUTOMATIKA" v hlavni tabulce = jediny zdroj pravdy pro zapnuto/vypnuto
# a historii behu. Vidi ho aplikace (lokalne i na Renderu) i robot na GitHubu.

CONTROL_SHEET = "AUTOMATIKA"
_LOG_HEADER = ["Datum a čas", "Režim", "Model", "Listů", "Vygenerováno řádků",
               "Zapsáno buněk", "Chyb", "Poznámka"]


def ensure_control_sheet(spreadsheet_id=DEFAULT_SPREADSHEET_ID):
    """Zalozi ridici list AUTOMATIKA, pokud neexistuje. Vraci True, kdyz byl vytvoren."""
    svc = get_service()
    info = list_sheets(spreadsheet_id)
    if any(sh["title"] == CONTROL_SHEET for sh in info["sheets"]):
        return False
    api_call(svc.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": [{"addSheet": {"properties": {"title": CONTROL_SHEET}}}]}),
        "založení listu AUTOMATIKA")
    api_call(svc.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"valueInputOption": "RAW", "data": [
            {"range": f"{_quote(CONTROL_SHEET)}!A1",
             "values": [["AUTOMATICKÉ DOPLŇOVÁNÍ COPYWRITINGU — řídicí list (needitovat ručně kromě B2)"],
                        ["Stav automatiky (ZAPNUTO / VYPNUTO):", "ZAPNUTO"],
                        [""],
                        _LOG_HEADER]}]}),
        "inicializace listu AUTOMATIKA")
    logging.info("Založen řídicí list AUTOMATIKA (stav: ZAPNUTO).")
    return True


def get_automation_enabled(spreadsheet_id=DEFAULT_SPREADSHEET_ID):
    """Precte stav prepinace z B2. Kdyz list chybi, zalozi ho (vychozi ZAPNUTO)."""
    svc = get_service()
    try:
        resp = api_call(svc.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=f"{_quote(CONTROL_SHEET)}!B2"),
            "čtení stavu automatiky")
        val = str(resp.get("values", [[""]])[0][0]).strip().upper()
        return val not in ("VYPNUTO", "OFF", "NE", "FALSE", "0")
    except Exception as e:
        if "Unable to parse range" in str(e) or "not found" in str(e).lower():
            ensure_control_sheet(spreadsheet_id)
            return True
        raise


def set_automation_enabled(enabled, spreadsheet_id=DEFAULT_SPREADSHEET_ID):
    """Zapne/vypne automatiku (zapisuje jen bunku B2 ridiciho listu)."""
    ensure_control_sheet(spreadsheet_id)
    svc = get_service()
    api_call(svc.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, range=f"{_quote(CONTROL_SHEET)}!B2",
        valueInputOption="RAW",
        body={"values": [["ZAPNUTO" if enabled else "VYPNUTO"]]}),
        "přepnutí automatiky")
    logging.info(f"Automatika {'ZAPNUTA' if enabled else 'VYPNUTA'}.")
    return enabled


def append_run_log(mode, model, sheets_count, generated, cells, failed, note="",
                   spreadsheet_id=DEFAULT_SPREADSHEET_ID):
    """Prida radek do historie behu na ridicim listu."""
    import datetime
    ensure_control_sheet(spreadsheet_id)
    svc = get_service()
    row = [datetime.datetime.now().strftime("%d.%m.%Y %H:%M"), mode, model,
           sheets_count, generated, cells, failed, note[:300]]
    api_call(svc.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id, range=f"{_quote(CONTROL_SHEET)}!A4",
        valueInputOption="RAW", insertDataOption="INSERT_ROWS",
        body={"values": [row]}), "zápis do historie běhů")


def get_run_log(limit=20, spreadsheet_id=DEFAULT_SPREADSHEET_ID):
    """Vraci poslednich `limit` behu (nejnovejsi prvni) + aktualni stav."""
    svc = get_service()
    try:
        resp = api_call(svc.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=f"{_quote(CONTROL_SHEET)}!A2:H500"),
            "čtení historie běhů")
    except Exception:
        return {"enabled": True, "runs": [], "control_sheet_exists": False}
    values = resp.get("values", [])
    enabled = True
    if values and len(values[0]) > 1:
        enabled = str(values[0][1]).strip().upper() not in ("VYPNUTO", "OFF", "NE", "FALSE", "0")
    runs = []
    for row in values[3:]:      # od radku 5 dal (za hlavickou logu)
        if not row or not str(row[0]).strip():
            continue
        runs.append({
            "when": row[0] if len(row) > 0 else "",
            "mode": row[1] if len(row) > 1 else "",
            "model": row[2] if len(row) > 2 else "",
            "sheets": row[3] if len(row) > 3 else "",
            "generated": row[4] if len(row) > 4 else "",
            "cells": row[5] if len(row) > 5 else "",
            "failed": row[6] if len(row) > 6 else "",
            "note": row[7] if len(row) > 7 else "",
        })
    runs.reverse()
    return {"enabled": enabled, "runs": runs[:limit], "control_sheet_exists": True}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "check":
        r = check_access()
        print(json.dumps(r, ensure_ascii=False, indent=2))
        if not r["ok"]:
            print("\nKONTROLA SELHALA - oprav pripojeni (viz 'error' vyse).", file=sys.stderr)
            sys.exit(1)
    elif cmd == "sheets":
        print(json.dumps(list_sheets(), ensure_ascii=False, indent=2))
    elif cmd == "read":
        d = read_sheet(sys.argv[2])
        print("header_row:", d["header_row"], "| radku:", len(d["rows"]))
        print("mapping:", d["mapping"])
        for r in d["rows"][:5]:
            print(" ", r)
    elif cmd == "automation":
        sub = sys.argv[2] if len(sys.argv) > 2 else "status"
        if sub == "on":
            set_automation_enabled(True)
        elif sub == "off":
            set_automation_enabled(False)
        print(json.dumps(get_run_log(10), ensure_ascii=False, indent=1))
    elif cmd == "email":
        print(get_service_account_email() or "(chybi credentials)")
