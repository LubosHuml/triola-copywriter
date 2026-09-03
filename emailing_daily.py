# -*- coding: utf-8 -*-
"""
Denní příprava podkladů pro emailing.

Projde plán kampaní, vezme e-maily s datem OD DNEŠKA DÁL, které ještě nemají
vyplněný sloupec "AI zadání + náhledy", a pro každý:
  1. vytvoří zadání pro emailing (CZ + SK)
  2. vytvoří textové náhledy rozesílek CZ a SK
  3. uloží tři PDF do složky "Rozesílky <datum>" na Disku
  4. zapíše odkazy zpět do plánu

Staré kampaně a kampaně, které už odkazy mají, se nikdy nepřepisují.

Použití:
    python emailing_daily.py --dry-run     # jen ukáže, co by připravil
    python emailing_daily.py               # ostrý běh
    python emailing_daily.py --limit 3
"""
import os
import sys
import json
import time
import logging
import argparse
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "emailing_daily.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
)


def main():
    ap = argparse.ArgumentParser(description="Denní podklady pro emailing")
    ap.add_argument("--dry-run", action="store_true", help="jen náhled, nic nevytváří")
    ap.add_argument("--limit", type=int, default=10, help="max kampaní za běh")
    ap.add_argument("--model", default="claude-opus-5")
    ap.add_argument("--days-ahead", type=int, default=0,
                    help="0 = od dneška dál; kladné číslo omezí okno dopředu")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    started = datetime.datetime.now()
    logging.info("=" * 70)
    logging.info(f"EMAILING — příprava podkladů {'(DRY-RUN)' if args.dry_run else ''} "
                 f"— {started:%d.%m.%Y %H:%M}")

    import emailing_service as es
    import app as appmod
    from ai_service import generate_emailing_brief, generate_emailing_preview

    today = datetime.date.today()
    limit_date = (today + datetime.timedelta(days=args.days_ahead)) if args.days_ahead else None

    camps = es.load_campaigns(limit=300)
    ai_col = es.find_ai_column()
    if ai_col == -1:
        logging.error("Sloupec 'AI zadání + náhledy' nebyl v plánu nalezen — končím.")
        print(json.dumps({"ok": False, "error": "chybí sloupec AI zadání + náhledy"},
                         ensure_ascii=False))
        sys.exit(1)

    todo = []
    for c in camps:
        if not c["datum_iso"] or c["datum_iso"] < today.isoformat():
            continue                       # staré kampaně neřešíme
        if limit_date and c["datum_iso"] > limit_date.isoformat():
            continue
        if es.campaign_has_links(c, ai_col):
            continue                       # už má hotové podklady
        todo.append(c)
    todo.sort(key=lambda x: x["datum_iso"])

    logging.info(f"Kampaní od {today} bez podkladů: {len(todo)}")
    for c in todo[:args.limit]:
        logging.info(f"   {c['datum']} — {c['tema'][:60]}")

    summary = {"nalezeno": len(todo), "pripraveno": 0, "chyb": 0, "chyby": []}

    for c in todo[:args.limit]:
        label = f"{c['datum']} {c['tema'][:40]}"
        if args.dry_run:
            summary["pripraveno"] += 1
            continue
        try:
            groups = es.parse_product_codes(c.get("produkty", ""))
            products = es.lookup_products(groups, appmod.PRODUCTS_DB)

            brief = generate_emailing_brief(c, products, args.model)
            cz = generate_emailing_preview(brief, "cz", args.model)
            sk = generate_emailing_preview(brief, "sk", args.model)

            paths = es.export_all(c, brief, cz, sk)
            links = es.publish_to_drive(c, paths)
            es.write_links_to_plan(c["row_num"], links, ai_col)

            summary["pripraveno"] += 1
            logging.info(f"  OK {label} → {links.get('folder_url','')}")
        except Exception as e:
            summary["chyb"] += 1
            summary["chyby"].append(f"{label}: {str(e)[:160]}")
            logging.error(f"  CHYBA {label}: {str(e)[:220]}")
        time.sleep(1.0)

    dur = (datetime.datetime.now() - started).total_seconds()
    logging.info("-" * 70)
    logging.info(f"HOTOVO za {dur:.0f}s | nalezeno: {summary['nalezeno']} | "
                 f"připraveno: {summary['pripraveno']} | chyb: {summary['chyb']}")
    print(json.dumps({"ok": summary["chyb"] == 0, "dry_run": args.dry_run,
                      "duration_s": round(dur), **summary}, ensure_ascii=False, indent=1))
    sys.exit(0 if summary["chyb"] == 0 else 2)


if __name__ == "__main__":
    main()
