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

def _pdf(title, blocks, path):
    """
    Vytvoří jednoduché textové PDF (bez obrázků) s diakritikou.
    blocks: seznam (styl, text), styl = h1|h2|h3|p|small|hr
    """
    from fpdf import FPDF

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    font = "helvetica"
    for cand in (r"C:\Windows\Fonts\arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(cand):
            try:
                pdf.add_font("main", "", cand)
                bold = cand.replace("arial.ttf", "arialbd.ttf").replace("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")
                pdf.add_font("main", "B", bold if os.path.exists(bold) else cand)
                font = "main"
                break
            except Exception:
                pass

    import re as _re
    _emoji = _re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u2190-\u21FF]+")

    def txt(s):
        s = _emoji.sub("", str(s or ""))
        if font == "helvetica":      # bez unicode fontu odstranit diakritiku
            import unicodedata
            s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
        return s

    styles = {
        "h1": (16, "B", 6, (142, 42, 74)),
        "h2": (13, "B", 4, (142, 42, 74)),
        "h3": (11, "B", 3, (60, 40, 48)),
        "p":  (10.5, "", 2, (30, 30, 30)),
        "small": (8.5, "", 2, (110, 110, 110)),
    }
    for style, text in blocks:
        if style == "hr":
            pdf.set_draw_color(220, 200, 210)
            y = pdf.get_y() + 2
            pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
            pdf.ln(6)
            continue
        size, weight, gap, color = styles.get(style, styles["p"])
        pdf.set_font(font, weight, size)
        pdf.set_text_color(*color)
        pdf.multi_cell(0, size * 0.55, txt(text))
        pdf.ln(gap)

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

    zadani = _pdf(f"Zadání pro emailing — {campaign.get('tema','')}",
                  _text_to_blocks(brief_text, campaign),
                  os.path.join(outdir, f"ZADANI_{base}.pdf"))
    cz = _pdf(f"Náhled rozesílky CZ — {campaign.get('tema','')}",
              _text_to_blocks(preview_cz, campaign),
              os.path.join(outdir, f"ROZESILKA_CZ_{base}.pdf"))
    sk = _pdf(f"Náhled rozesílky SK — {campaign.get('tema','')}",
              _text_to_blocks(preview_sk, campaign),
              os.path.join(outdir, f"ROZESILKA_SK_{base}.pdf"))
    return {"zadani": zadani, "cz": cz, "sk": sk}


def _text_to_blocks(text, campaign):
    """Rozdělí vygenerovaný text na bloky pro PDF podle jednoduchých značek."""
    blocks = [("h1", campaign.get("tema", "Emailing Triola")),
              ("small", f"{campaign.get('datum','')} · {campaign.get('den','')} · "
                        f"segmentace: {campaign.get('segmentace','—')}"),
              ("hr", "")]
    for line in str(text or "").splitlines():
        s = line.rstrip()
        if not s.strip():
            continue
        if s.startswith("### "):
            blocks.append(("h3", s[4:]))
        elif s.startswith("## "):
            blocks.append(("h2", s[3:]))
        elif s.startswith("# "):
            blocks.append(("h2", s[2:]))
        elif s.strip() in ("---", "___"):
            blocks.append(("hr", ""))
        else:
            blocks.append(("p", s))
    blocks.append(("hr", ""))
    blocks.append(("small", "Vygenerováno aplikací Triola Copywriter · "
                            f"{datetime.datetime.now():%d.%m.%Y %H:%M}"))
    return blocks
