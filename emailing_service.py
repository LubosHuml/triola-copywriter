# -*- coding: utf-8 -*-
"""
Emailing pro Triolu — příprava zadání a náhledů rozesílek.

Zdroje:
  1. Plán kampaní: list "Emailing" v tabulce Triola_CZ_retail plan
  2. Produktová databáze z XML feedu (názvy, ceny, odkazy, barvy)
  3. Naučená struktura zadání ze složky Emailing na Google Drive

Výstupy (tři soubory, jak je zvyklá marketingová podpora):
  - ZADANI_<datum>_<tema>.pdf     — zadání pro grafika a copy (CZ + SK)
  - ROZESILKA_CZ_<...>.pdf        — textový náhled e-mailu, bez obrázků
  - ROZESILKA_SK_<...>.pdf        — totéž slovensky
"""
import os
import re
import json
import logging
import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "emailing_vystupy")

# Tabulka s plánem kampaní (list "Emailing")
PLAN_SPREADSHEET_ID = "1FHHcEKTCUFDlgkOGtBpBP0fbDLvR8XtgAsnSNE0ZdyQ"
PLAN_SHEET = "Emailing"
PLAN_HEADER_ROW = 4          # hlavička je na 4. řádku

# Mapování sloupců plánu (0-based, podle hlavičky)
PLAN_COLUMNS = {
    "stav": "stav",
    "datum": "datum",
    "pm": "pm",
    "den": "den",
    "téma": "tema",
    "segmentace": "segmentace",
    "kod vybrane produkty": "produkty",
    "interní linky": "linky",
    "zadání grafika / copy": "zadani_grafika",
    "specifikace produktu": "specifikace",
    "komentář": "komentar",
    "grafika": "grafika",
}


# ---------------------------------------------------------------- plán kampaní

def load_campaigns(limit=60, only_future=False):
    """Načte plánované e-maily z listu Emailing. Vrací seznam dict."""
    import sheets_service as ss
    svc = ss.get_service()
    resp = ss.api_call(svc.spreadsheets().values().get(
        spreadsheetId=PLAN_SPREADSHEET_ID,
        range=f"{ss._quote(PLAN_SHEET)}!A1:Z400"), "čtení plánu emailingu")
    values = resp.get("values", [])
    if len(values) < PLAN_HEADER_ROW:
        return []

    hdr = values[PLAN_HEADER_ROW - 1]
    idx = {}
    for i, h in enumerate(hdr):
        key = PLAN_COLUMNS.get(str(h).strip().lower())
        if key and key not in idx:
            idx[key] = i

    def cell(row, key):
        i = idx.get(key, -1)
        if i == -1 or i >= len(row):
            return ""
        v = row[i]
        return str(v).strip() if v is not None else ""

    today = datetime.date.today()
    out = []
    for r_i in range(PLAN_HEADER_ROW, len(values)):
        row = values[r_i]
        tema = cell(row, "tema")
        datum = cell(row, "datum")
        if not tema or len(tema) < 3:
            continue
        d = _parse_date(datum)
        if only_future and d and d < today:
            continue
        out.append({
            "row_num": r_i + 1,
            "datum": datum,
            "datum_iso": d.isoformat() if d else "",
            "den": cell(row, "den"),
            "tema": tema,
            "segmentace": cell(row, "segmentace"),
            "produkty": cell(row, "produkty"),
            "linky": cell(row, "linky"),
            "zadani_grafika": cell(row, "zadani_grafika"),
            "specifikace": cell(row, "specifikace"),
            "komentar": cell(row, "komentar"),
            "pm": cell(row, "pm"),
            "stav": cell(row, "stav"),
        })
    # Nejdriv kampane s datem (od nejnovejsi), az potom radky bez data
    s_dated = sorted([c for c in out if c["datum_iso"]],
                     key=lambda x: x["datum_iso"], reverse=True)
    s_undated = [c for c in out if not c["datum_iso"]]
    return (s_dated + s_undated)[:limit]


def _parse_date(text):
    """'17.03.2026' / '17. 3. 2026' -> date, jinak None."""
    m = re.search(r"(\d{1,2})\s*\.\s*(\d{1,2})\s*\.\s*(\d{4})", str(text or ""))
    if not m:
        return None
    try:
        return datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


# ---------------------------------------------------------------- produkty

def parse_product_codes(text):
    """
    Z pole 'Kod vybrane produkty' vytáhne kódy produktů.
    Zvládá zápisy: 'f29890-86-75E; f32890-86-80', 'DOR1B066+DOR2A026, DOR1A061'
    Dvojice spojené '+' drží pohromadě jako set.
    """
    raw = str(text or "")
    groups = []
    for chunk in re.split(r"[;,\n]+", raw):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = [p.strip() for p in chunk.split("+") if p.strip()]
        codes = []
        for p in parts:
            m = re.match(r"^[A-Za-z]{0,4}\s*[\w./-]+", p)
            if m:
                codes.append(m.group(0).strip())
        if codes:
            groups.append(codes)
    return groups


def lookup_products(groups, products_db):
    """Ke kódům dohledá data z feedu (název, cena, odkaz). Nic si nevymýšlí."""
    out = []
    for codes in groups:
        items = []
        for code in codes:
            digits = re.sub(r"^\D+", "", code).split("-")[0].split("/")[0].strip()
            p = products_db.get(digits)
            items.append({
                "kod": code,
                "nalezen": bool(p),
                "nazev": (p or {}).get("generic_title", ""),
                "cena": (p or {}).get("base_price", ""),
                "akcni_cena": (p or {}).get("sale_price", ""),
                "odkaz": ((p or {}).get("all_links") or [""])[0],
                "barvy": (p or {}).get("all_colors", []),
                "strih": (p or {}).get("cut_name", ""),
            })
        out.append(items)
    return out


# ---------------------------------------------------------------- export

BRAND = (142, 42, 74)          # vinova Triola
INK = (38, 30, 34)
MUTED = (125, 108, 115)


def _new_pdf():
    """Zaklad PDF s fontem, ktery umi diakritiku."""
    from fpdf import FPDF
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    font = "helvetica"
    for reg, bold in ((r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
                      ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                       "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")):
        if os.path.exists(reg):
            try:
                pdf.add_font("main", "", reg)
                pdf.add_font("main", "B", bold if os.path.exists(bold) else reg)
                font = "main"
                break
            except Exception:
                pass
    return pdf, font


_EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u2190-\u21FF]+")


def _txt(s, font):
    s = _EMOJI.sub("", str(s or ""))
    if font == "helvetica":
        import unicodedata
        s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return s


def _parse_lines(text):
    """Rozdeli vygenerovany text na (uroven, obsah)."""
    out = []
    for raw in str(text or "").splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("### "):
            out.append(("h3", line[4:]))
        elif line.startswith("## "):
            out.append(("h2", line[3:]))
        elif line.startswith("# "):
            out.append(("h1", line[2:]))
        elif line.strip() in ("---", "___"):
            out.append(("hr", ""))
        elif line.lstrip().startswith(("- ", "• ", "● ")):
            out.append(("li", line.lstrip()[2:]))
        elif line.strip().startswith("[") and line.strip().endswith("]"):
            out.append(("cta", line.strip()[1:-1].strip()))
        else:
            out.append(("p", line))
    return out


def _pdf_brief(campaign, text, path):
    """
    ZADÁNÍ — vypada jako interni pracovni dokument:
    tmavy hlavickovy pruh, stitek, levá barevná linka u sekci, popisky polí.
    """
    pdf, font = _new_pdf()
    W = pdf.w - pdf.l_margin - pdf.r_margin

    # hlavickovy pruh
    pdf.set_fill_color(*BRAND)
    pdf.rect(0, 0, pdf.w, 30, "F")
    pdf.set_xy(pdf.l_margin, 8)
    pdf.set_font(font, "B", 15)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, _txt("ZADÁNÍ PRO EMAILING", font))
    pdf.set_xy(pdf.l_margin, 17)
    pdf.set_font(font, "", 9.5)
    pdf.cell(0, 5, _txt(f"{campaign.get('datum','')}  ·  {campaign.get('tema','')}", font))
    pdf.set_y(38)

    # meta box
    pdf.set_fill_color(250, 244, 247)
    pdf.set_draw_color(228, 208, 217)
    meta = [("Datum odeslání", f"{campaign.get('datum','—')} {campaign.get('den','')}"),
            ("Segmentace", campaign.get("segmentace") or "všichni CZ SK"),
            ("PM", campaign.get("pm") or "—")]
    y0 = pdf.get_y()
    pdf.rect(pdf.l_margin, y0, W, 7 * len(meta) + 4, "DF")
    pdf.set_y(y0 + 2)
    for label, val in meta:
        pdf.set_x(pdf.l_margin + 3)
        pdf.set_font(font, "B", 9)
        pdf.set_text_color(*BRAND)
        pdf.cell(34, 6, _txt(label, font))
        pdf.set_font(font, "", 9)
        pdf.set_text_color(*INK)
        pdf.multi_cell(W - 40, 6, _txt(val, font))
    pdf.ln(6)

    for kind, content in _parse_lines(text):
        if kind == "hr":
            pdf.ln(2)
            continue
        if kind in ("h1", "h2"):
            pdf.ln(3)
            y = pdf.get_y()
            pdf.set_fill_color(*BRAND)
            pdf.rect(pdf.l_margin, y, 2.2, 7, "F")       # levá barevná linka
            pdf.set_x(pdf.l_margin + 5)
            pdf.set_font(font, "B", 12)
            pdf.set_text_color(*BRAND)
            pdf.multi_cell(W - 5, 7, _txt(content, font))
            pdf.ln(1.5)
        elif kind == "h3":
            pdf.set_font(font, "B", 10)
            pdf.set_text_color(*INK)
            pdf.set_fill_color(244, 238, 241)
            pdf.multi_cell(W, 6.5, _txt("  " + content, font), fill=True)
            pdf.ln(1)
        elif kind == "li":
            pdf.set_font(font, "", 9.5)
            pdf.set_text_color(*INK)
            pdf.set_x(pdf.l_margin + 4)
            pdf.multi_cell(W - 4, 5.4, _txt("•  " + content, font))
        elif kind == "cta":
            pdf.set_font(font, "B", 9.5)
            pdf.set_text_color(*BRAND)
            pdf.multi_cell(W, 5.6, _txt("[ " + content + " ]", font))
        else:
            pdf.set_font(font, "", 9.5)
            pdf.set_text_color(*INK)
            pdf.multi_cell(W, 5.4, _txt(content, font))
            pdf.ln(0.8)

    pdf.ln(5)
    pdf.set_font(font, "", 7.5)
    pdf.set_text_color(*MUTED)
    pdf.multi_cell(W, 4, _txt("Interní podklad pro grafika a copy · vygenerovala aplikace "
                              f"Triola Copywriter {datetime.datetime.now():%d.%m.%Y %H:%M}", font))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pdf.output(path)
    return path


def _pdf_preview(campaign, text, lang, path):
    """
    NÁHLED ROZESÍLKY — vypada jako e-mail: uzsi sloupec, ramecek schranky,
    predmet v hlavicce, CTA jako tlacitko.
    """
    pdf, font = _new_pdf()
    full = pdf.w - pdf.l_margin - pdf.r_margin
    pad = 12                                    # uzsi sloupec = dojem e-mailu
    x0 = pdf.l_margin + pad
    W = full - 2 * pad

    pdf.set_xy(pdf.l_margin, 12)
    pdf.set_font(font, "", 8.5)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 5, _txt(f"NÁHLED ROZESÍLKY · {lang.upper()} · {campaign.get('datum','')}", font))
    pdf.ln(8)

    pdf.set_draw_color(226, 226, 226)
    top = pdf.get_y()
    pdf.set_x(x0)

    for kind, content in _parse_lines(text):
        pdf.set_x(x0)
        if kind == "hr":
            y = pdf.get_y() + 1
            pdf.set_draw_color(232, 226, 229)
            pdf.line(x0, y, x0 + W, y)
            pdf.ln(5)
        elif kind == "h1":                       # predmet
            pdf.set_fill_color(247, 241, 244)
            pdf.set_font(font, "B", 12.5)
            pdf.set_text_color(*INK)
            pdf.multi_cell(W, 8, _txt(content, font), fill=True)
            pdf.ln(1)
        elif kind == "h2":                       # sekce e-mailu
            pdf.ln(2)
            pdf.set_font(font, "B", 8.5)
            pdf.set_text_color(*MUTED)
            pdf.multi_cell(W, 5, _txt(content.upper(), font))
            pdf.ln(0.5)
        elif kind == "h3":                       # produkt
            pdf.set_font(font, "B", 10.5)
            pdf.set_text_color(*BRAND)
            pdf.multi_cell(W, 6, _txt(content, font))
        elif kind == "cta":                      # tlacitko
            pdf.ln(1)
            y = pdf.get_y()
            bw = min(W, max(52, len(content) * 2.3 + 16))
            pdf.set_fill_color(*BRAND)
            pdf.rect(x0, y, bw, 9, "F")
            pdf.set_xy(x0, y + 1.4)
            pdf.set_font(font, "B", 9.5)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(bw, 6, _txt(content, font), align="C")
            pdf.set_y(y + 12)
        elif kind == "li":
            pdf.set_font(font, "", 10)
            pdf.set_text_color(*INK)
            pdf.multi_cell(W, 5.6, _txt("•  " + content, font))
        else:
            pdf.set_font(font, "", 10)
            pdf.set_text_color(*INK)
            pdf.multi_cell(W, 5.8, _txt(content, font))
            pdf.ln(1.2)

    pdf.ln(4)
    pdf.set_x(x0)
    pdf.set_font(font, "", 7.5)
    pdf.set_text_color(*MUTED)
    pdf.multi_cell(W, 4, _txt("Textový náhled bez obrázků · Triola Copywriter "
                              f"{datetime.datetime.now():%d.%m.%Y %H:%M}", font))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pdf.output(path)
    return path


def _safe(text, maxlen=48):
    s = re.sub(r"[^\w\s-]", "", str(text or ""), flags=re.UNICODE).strip()
    s = re.sub(r"\s+", "_", s)
    return s[:maxlen] or "emailing"


def export_all(campaign, brief_text, preview_cz, preview_sk, outdir=None):
    """Uloží tři soubory a vrátí jejich cesty."""
    outdir = outdir or OUTPUT_DIR
    os.makedirs(outdir, exist_ok=True)
    d = campaign.get("datum_iso") or datetime.date.today().isoformat()
    base = f"{d}_{_safe(campaign.get('tema'))}"

    zadani = _pdf_brief(campaign, brief_text,
                        os.path.join(outdir, f"ZADANI_{base}.pdf"))
    cz = _pdf_preview(campaign, preview_cz, "cz",
                      os.path.join(outdir, f"ROZESILKA_CZ_{base}.pdf"))
    sk = _pdf_preview(campaign, preview_sk, "sk",
                      os.path.join(outdir, f"ROZESILKA_SK_{base}.pdf"))
    return {"zadani": zadani, "cz": cz, "sk": sk}

# ---------------------------------------------------------------- Google Drive

# Rodicovska slozka na Disku, do ktere se zakladaji slozky "Rozesílky <datum>".
# Musi byt nasdilena service accountu jako Editor.
DRIVE_PARENT_ENV = "EMAILING_DRIVE_FOLDER_ID"
DRIVE_PARENT_DEFAULT = "15k_PuLcp1ZJqBtjJpbZ8BivdKMBjFlZU"   # složka Emailing


def drive_parent_id():
    return os.getenv(DRIVE_PARENT_ENV) or DRIVE_PARENT_DEFAULT


def ensure_drive_folder(name, parent_id=None):
    """Najde nebo zalozi slozku daneho jmena. Vraci (id, url)."""
    import sheets_service as ss
    drive = ss.get_drive_service()
    parent = parent_id or drive_parent_id()
    safe = name.replace("'", "\\'")
    q = (f"name = '{safe}' and mimeType = 'application/vnd.google-apps.folder' "
         f"and '{parent}' in parents and trashed = false")
    res = ss.api_call(drive.files().list(q=q, fields="files(id,webViewLink)",
                                         supportsAllDrives=True), "hledání složky")
    files = res.get("files", [])
    if files:
        return files[0]["id"], files[0].get("webViewLink", "")
    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent]}
    f = ss.api_call(drive.files().create(body=meta, fields="id,webViewLink",
                                         supportsAllDrives=True), "vytvoření složky")
    logging.info(f"Vytvořena složka na Disku: {name}")
    return f["id"], f.get("webViewLink", "")


def upload_pdf(path, folder_id, name=None):
    """Nahraje PDF do slozky a vrati odkaz ke zhlednuti."""
    import sheets_service as ss
    from googleapiclient.http import MediaFileUpload
    drive = ss.get_drive_service()
    name = name or os.path.basename(path)

    # stejnojmenny soubor prepsat, ne zakladat duplicity
    safe = name.replace("'", "\\'")
    q = f"name = '{safe}' and '{folder_id}' in parents and trashed = false"
    old = ss.api_call(drive.files().list(q=q, fields="files(id)", supportsAllDrives=True),
                      "hledání souboru").get("files", [])
    media = MediaFileUpload(path, mimetype="application/pdf", resumable=False)
    if old:
        f = ss.api_call(drive.files().update(fileId=old[0]["id"], media_body=media,
                                             fields="id,webViewLink",
                                             supportsAllDrives=True), "aktualizace PDF")
    else:
        f = ss.api_call(drive.files().create(
            body={"name": name, "parents": [folder_id]}, media_body=media,
            fields="id,webViewLink", supportsAllDrives=True), "nahrání PDF")
    return f.get("webViewLink", "")


def publish_to_drive(campaign, paths, folder_name=None):
    """
    Zalozi slozku 'Rozesílky <datum>' a nahraje do ni tri PDF.
    Vraci {"folder_url":..., "zadani":..., "cz":..., "sk":...}
    """
    d = campaign.get("datum_iso") or datetime.date.today().isoformat()
    name = folder_name or f"Rozesílky {d}"
    folder_id, folder_url = ensure_drive_folder(name)
    out = {"folder_url": folder_url, "folder_id": folder_id}
    for key in ("zadani", "cz", "sk"):
        if paths.get(key) and os.path.exists(paths[key]):
            out[key] = upload_pdf(paths[key], folder_id)
    return out


# ---------------------------------------------------------------- zápis do plánu

AI_COLUMN_HEADER = "ai zadání + náhledy"


def find_ai_column():
    """Index sloupce 'AI zadání + náhledy' v planu (0-based), nebo -1."""
    import sheets_service as ss
    svc = ss.get_service()
    r = ss.api_call(svc.spreadsheets().values().get(
        spreadsheetId=PLAN_SPREADSHEET_ID,
        range=f"{ss._quote(PLAN_SHEET)}!A{PLAN_HEADER_ROW}:AZ{PLAN_HEADER_ROW}"),
        "hlavička plánu")
    hdr = r.get("values", [[]])
    hdr = hdr[0] if hdr else []
    for i, h in enumerate(hdr):
        if str(h).strip().lower() == AI_COLUMN_HEADER:
            return i
    return -1


def write_links_to_plan(row_num, links, col_idx=None):
    """Zapise odkazy na hotove podklady do sloupce 'AI zadání + náhledy'."""
    import sheets_service as ss
    col = col_idx if col_idx is not None else find_ai_column()
    if col == -1:
        raise RuntimeError("Sloupec 'AI zadání + náhledy' nebyl v plánu nalezen.")
    parts = []
    if links.get("folder_url"):
        parts.append(f"Složka: {links['folder_url']}")
    for key, label in (("zadani", "Zadání"), ("cz", "Náhled CZ"), ("sk", "Náhled SK")):
        if links.get(key):
            parts.append(f"{label}: {links[key]}")
    text = "\n".join(parts)
    svc = ss.get_service()
    a1 = f"{ss._quote(PLAN_SHEET)}!{ss.col_letter(col)}{row_num}"
    ss.api_call(svc.spreadsheets().values().update(
        spreadsheetId=PLAN_SPREADSHEET_ID, range=a1, valueInputOption="RAW",
        body={"values": [[text]]}), "zápis odkazů do plánu")
    return text


def campaign_has_links(campaign, col_idx):
    """Uz ma kampan hotove podklady? (bunka ve sloupci AI neni prazdna)"""
    import sheets_service as ss
    if col_idx == -1:
        return False
    svc = ss.get_service()
    a1 = f"{ss._quote(PLAN_SHEET)}!{ss.col_letter(col_idx)}{campaign['row_num']}"
    r = ss.api_call(svc.spreadsheets().values().get(
        spreadsheetId=PLAN_SPREADSHEET_ID, range=a1), "kontrola sloupce AI")
    vals = r.get("values", [])
    return bool(vals and vals[0] and str(vals[0][0]).strip())
