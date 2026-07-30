# -*- coding: utf-8 -*-
"""
Automatické doplňování copywritingu do hlavní tabulky Triola.

Co dělá:
  1. Najde AKTUÁLNÍ listy (sezóna 26/27 + trvalé kolekce) - staré sezóny ignoruje.
  2. V každém listu najde řádky, které mají podklady (typ produktu + prodejní argumenty),
     ale chybí jim některý z copywriting textů.
  3. Texty vygeneruje a doplní JEN do prázdných buněk - hotový text nikdy nepřepíše.

Bezpečnostní pojistky:
  - only_fill_empty=True  -> existující texty zůstávají nedotčené
  - řádek bez prodejních argumentů se přeskočí (nemá z čeho psát)
  - --limit           tvrdý strop počtu řádků za jeden běh (default 80)
  - --dry-run         jen vypíše, co by udělal; NIC nezapisuje ani negeneruje
  - kompletní log do auto_generate.log + JSON souhrn na stdout

Použití:
    python auto_generate.py --dry-run              # náhled, co je k doplnění
    python auto_generate.py                        # ostrý běh
    python auto_generate.py --sheet "Triola JL 26" # jen jeden list
    python auto_generate.py --limit 20 --model claude-opus-4-8
"""
import os
import sys
import json
import time
import argparse
import logging
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "auto_generate.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
)

# Pole, ktera se povazuji za povinny vystup. Chybi-li nektere, radek je "k doplneni".
REQUIRED_OUTPUTS = [
    "eshop_name", "short_name", "eshop_desc1", "eshop_desc2", "meta_title", "meta_desc",
    "eshop_name_sk", "short_name_sk", "eshop_desc1_sk", "eshop_desc2_sk",
    "meta_title_sk", "meta_desc_sk",
]
MIN_ARGUMENTS_LEN = 15      # kratsi "argumenty" jsou spis poznamka nez podklad


def row_needs_work(row, row_values, columns):
    """
    Vraci (potreba: bool, duvod: str, chybejici: list).
    Radek potrebuje praci, pokud ma podklady a zaroven mu chybi nejaky vystup.
    """
    if not row.get("model_code"):
        return False, "chybí kód produktu", []
    args = (row.get("arguments") or "").strip()
    if len(args) < MIN_ARGUMENTS_LEN:
        return False, "chybí prodejní argumenty", []
    brand = (row.get("brand") or "").strip().lower()
    if not (row.get("product_name") or "").strip() and brand not in ("", "triola"):
        # U cizi znacky neumime typ odvodit z kodu - bez sloupce PRODUKT radek preskocime.
        return False, "chybí typ produktu", []

    # kod s kodem barvy (/88...), ale barva neni ani v listu, ani v ciselniku BARVY
    import re as _re
    if not (row.get("color_name") or "").strip() and _re.search(r"/\d{2,3}\s*$", row.get("model_code", "")):
        return False, "chybí barva (kód není v listu BARVY)", []

    missing = []
    for key in REQUIRED_OUTPUTS:
        col = columns.get(key, -1)
        if col == -1:
            missing.append(key)                      # sloupec v listu jeste neexistuje
            continue
        val = row_values[col] if col < len(row_values) else ""
        if str(val).strip() == "":
            missing.append(key)
    if not missing:
        return False, "vše vyplněno", []
    return True, f"chybí {len(missing)} polí", missing


def process_sheet(sheet_name, model_key, tone_key, limit, dry_run, sleep_s=1.0):
    """Zpracuje jeden list. Vraci souhrn dict."""
    import sheets_service as ss
    from app import build_product_info
    from ai_service import generate_batch_row_data

    summary = {"sheet": sheet_name, "candidates": 0, "generated": 0, "failed": 0,
               "skipped": 0, "cells_written": 0, "created_columns": [], "errors": []}

    # JEDNO cteni listu - klicove pro rate limit Google API (60 cteni/min)
    data = ss.read_sheet_bundle(sheet_name)
    if not data["rows"]:
        logging.info(f"[{sheet_name}] žádné produktové řádky - přeskakuji")
        return summary

    all_vals = data["values"]
    columns = data["output_columns"]
    missing_cols = data["missing_columns"]

    todo = []
    for row in data["rows"]:
        rv = all_vals[row["row_num"] - 1] if row["row_num"] - 1 < len(all_vals) else []
        need, reason, missing = row_needs_work(row, rv, columns)
        if need:
            todo.append((row, rv, missing))
        else:
            summary["skipped"] += 1

    summary["candidates"] = len(todo)
    if not todo:
        logging.info(f"[{sheet_name}] nic k doplnění ({summary['skipped']} řádků v pořádku)")
        return summary

    logging.info(f"[{sheet_name}] k doplnění: {len(todo)} řádků "
                 f"(přeskočeno {summary['skipped']})")

    # chybejici vystupni sloupce zaloz teprve az kdyz vime, ze je co zapisovat
    if missing_cols and not dry_run:
        columns, created = ss.create_missing_columns(
            sheet_name, data["headers"], columns, missing_cols, data["header_row"])
        summary["created_columns"] = created
    elif missing_cols:
        summary["created_columns"] = [ss.WRITABLE_COLUMNS[k][0] for k in missing_cols]

    for row, rv, missing in todo[:limit]:
        label = f"{sheet_name} r.{row['row_num']} {row['model_code']}"
        if dry_run:
            logging.info(f"  [DRY-RUN] {label}: doplnil bych {len(missing)} polí "
                         f"({', '.join(missing[:4])}{'…' if len(missing) > 4 else ''})")
            summary["generated"] += 1
            continue
        try:
            info = build_product_info(
                model_code=row["model_code"], color_name=row["color_name"],
                arguments=row["arguments"], product_name=row["product_name"],
                design_name=row["design_name"], row_brand=row["brand"],
                material=row["material"], size=row["size"])
            results = generate_batch_row_data(info, model_key, tone_key)
            written = ss.write_row_results(
                sheet_name, row["row_num"], results, columns,
                only_fill_empty=True, existing_row=rv)
            summary["generated"] += 1
            summary["cells_written"] += len(written)
            logging.info(f"  OK {label}: zapsáno {len(written)} buněk "
                         f"({', '.join(w['cell'] for w in written[:6])}…)")
        except Exception as e:
            summary["failed"] += 1
            summary["errors"].append(f"{label}: {str(e)[:160]}")
            logging.error(f"  CHYBA {label}: {str(e)[:200]}")
        time.sleep(sleep_s)

    return summary


def main():
    ap = argparse.ArgumentParser(description="Automatické doplnění copywritingu do Google Sheets")
    ap.add_argument("--dry-run", action="store_true", help="jen náhled, nic negeneruje ani nezapisuje")
    ap.add_argument("--limit", type=int, default=80, help="max řádků celkem za běh (default 80)")
    ap.add_argument("--per-sheet", type=int, default=40, help="max řádků na jeden list (default 40)")
    ap.add_argument("--sheet", action="append", help="zpracovat jen tento list (lze zadat víckrát)")
    ap.add_argument("--model", default="claude-opus-5", help="AI model")
    ap.add_argument("--tone", default="empaticky", help="tón textů")
    ap.add_argument("--no-basic", action="store_true", help="vynechat trvalé kolekce (bez roku)")
    ap.add_argument("--force", action="store_true", help="spustit i při VYPNUTÉ automatice")
    ap.add_argument("--no-feed-update", action="store_true", help="nestahovat čerstvý XML feed")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    started = datetime.datetime.now()
    logging.info("=" * 70)
    logging.info(f"AUTOMATICKÉ DOPLNĚNÍ COPYWRITINGU {'(DRY-RUN)' if args.dry_run else ''} "
                 f"— {started:%d.%m.%Y %H:%M}")

    import sheets_service as ss

    # 0a. Respektuj prepinac automatiky (list AUTOMATIKA v hlavni tabulce)
    try:
        ss.ensure_control_sheet()
        enabled = ss.get_automation_enabled()
    except Exception as e:
        logging.error(f"Nelze přečíst stav automatiky: {e}")
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
    if not enabled and not args.force:
        logging.info("Automatika je VYPNUTA (list AUTOMATIKA, buňka B2) - končím bez práce.")
        try:
            ss.append_run_log("automatický" if not args.dry_run else "náhled", args.model,
                              0, 0, 0, 0, "Přeskočeno - automatika vypnuta")
        except Exception:
            pass
        print(json.dumps({"ok": True, "skipped": True,
                          "reason": "automatika vypnuta"}, ensure_ascii=False))
        sys.exit(0)

    # 0b. Cerstvy XML feed produktu (aby nove produkty byly v databazi)
    if not args.no_feed_update:
        try:
            import feed_parser
            db = feed_parser.build_and_cache_products(force_update=True)
            logging.info(f"XML feed aktualizován: {len(db)} produktů.")
        except Exception as e:
            logging.warning(f"Aktualizace XML feedu selhala ({str(e)[:120]}) - "
                            f"pokračuji se stávající cache.")

    try:
        sheets = args.sheet or ss.list_current_sheets(include_basic=not args.no_basic)
    except Exception as e:
        logging.error(f"Nelze načíst seznam listů: {e}")
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)

    logging.info(f"Aktuální listy ({len(sheets)}): {', '.join(sheets)}")

    total = {"sheets": 0, "candidates": 0, "generated": 0, "failed": 0,
             "skipped": 0, "cells_written": 0, "created_columns": [], "errors": []}
    remaining = args.limit
    per_sheet_summaries = []

    for name in sheets:
        if remaining <= 0:
            logging.info(f"Dosažen limit {args.limit} řádků - další listy zpracuje příští běh.")
            break
        try:
            s = process_sheet(name, args.model, args.tone,
                              min(args.per_sheet, remaining), args.dry_run)
        except Exception as e:
            logging.error(f"[{name}] selhalo celé zpracování listu: {str(e)[:200]}")
            total["errors"].append(f"{name}: {str(e)[:160]}")
            continue
        per_sheet_summaries.append(s)
        time.sleep(0.4)   # slusnost k API kvote
        total["sheets"] += 1
        for k in ("candidates", "generated", "failed", "skipped", "cells_written"):
            total[k] += s[k]
        total["created_columns"] += s["created_columns"]
        total["errors"] += s["errors"]
        if not args.dry_run:
            remaining -= s["generated"]

    dur = (datetime.datetime.now() - started).total_seconds()
    logging.info("-" * 70)
    logging.info(f"HOTOVO za {dur:.0f}s | listů: {total['sheets']} | "
                 f"{'k doplnění' if args.dry_run else 'vygenerováno'}: {total['generated']} | "
                 f"buněk zapsáno: {total['cells_written']} | chyb: {total['failed']}")
    if total["errors"]:
        for e in total["errors"][:10]:
            logging.info(f"  ! {e}")

    # zapis vysledku do historie na ridicim listu
    try:
        mode = "náhled (dry-run)" if args.dry_run else ("ruční" if args.sheet else "automatický")
        note = "; ".join(total["errors"][:3]) if total["errors"] else "OK"
        ss.append_run_log(mode, args.model, total["sheets"],
                          total["generated"], total["cells_written"],
                          total["failed"], note)
    except Exception as e:
        logging.warning(f"Zápis do historie běhů selhal: {e}")

    print(json.dumps({"ok": total["failed"] == 0, "dry_run": args.dry_run,
                      "duration_s": round(dur), "total": total,
                      "sheets": per_sheet_summaries}, ensure_ascii=False, indent=1))
    sys.exit(0 if total["failed"] == 0 else 2)


if __name__ == "__main__":
    main()
