# Audit copywritingu — Triola / Snus-Shop / FutureCycling

Datum: 7. 7. 2026 · Rozsah: prompty, copywriting logika, UI textů generátoru, kontaminace mezi projekty
**AKTUALIZACE (2. kolo):** Všechny opravy provedeny a ověřeny (syntaxe Python i JS u všech tří projektů). FutureCycling_Copy znovu postaven a otestován.

---

## 1. TRIOLA (produkce, běží na Renderu) — celkově VELMI DOBRÝ STAV

### Co funguje dobře
Systémový prompt (`TRIOLA_SYSTEM_PROMPT`) je plně v souladu s dokumentem „Komunikační strategie": sedí vize i mise, všechny tři persony (Moderní matka, Kreativní duše, Tradicionalistka nové generace), claimy („Laskavá. Česká. Padnoucí.", „Tradice v každém stehu", „Každá velikost má svou krásu") i body-positivity pravidla (zákaz slov „nedokonalosti", „zamaskovat" apod.). Znalostní báze střihů (Perfect-Fit, T-Fit, Top-Fit, Fixed-Fit, Soft-Fit) je věcně správná, SEO prompt (prediktivní kalibrace, pattern break, otevřená smyčka) je nadstandardně kvalitní. Zákaz názvů kolekcí je ošetřen dvojitě (system + user prompt), stejně tak vynucení zadané barvy.

### Nalezeno a OPRAVENO
1. **Překlep v batch promptu**: „KLÍČOVÉ VÝHOWY" → „KLÍČOVÉ VÝHODY" (`ai_service.py`). Šlo přímo do promptu pro všechny hromadně generované produkty.
2. **Literál `\n` místo skutečného řádkování**: seznam benefitů a marketingový blok v batch promptu se do AI posílaly jako jeden slitý řetězec s viditelnými „\n". Opraveno na skutečné nové řádky (čistší prompt = spolehlivější výstup).
3. **Simulovaný text porušoval vlastní brand pravidla**: fallback příspěvek na sociální sítě obsahoval zakázanou frázi „Představujeme vám" — přeformulováno.
4. **eshop_desc2 u kalhotek**: prompt vždy radil „kombinovat s kalhotkami", i když je produkt sám kalhotky. Nyní podmíněně (podprsenka → kalhotky, kalhotky → podprsenka).

### Dodatečně opraveno (2. kolo)
- **`cycle_feed.xml` přesunut** z Triola_Copy do FutureCycling_Copy (nebude se nasazovat na Render).
- **Meta title instrukce v batch**: přidána prioritizace obsahu (typ + kód + barva; střih jen pokud se vejde do 60 znaků).
- Syntaxe všech souborů ověřena (`py_compile` + `node --check`).

### Zbývající drobnost (kosmetická, k rozhodnutí)
- **`parse_robust_json`**: záchranný regex umí jen stringové hodnoty; číselné klíče (`title_znaku`) při záchraně vrací prázdné.

---

## 2. SNUS-SHOP.CZ (Snus_Copy) — KONTAMINACE ODSTRANĚNA

Jádro promptů bylo už dobře předělané (legislativa SZPI/ČOI, zákaz zdravotních a terapeutických tvrzení, povinné varování 18+, Zero-GPT pravidla — kvalitní práce). Ale propisovaly se věci z Trioly:

### Nalezeno a OPRAVENO
1. **KRITICKÁ CHYBA KÓDU**: špatné odsazení `competitor_block` v `generate_copywriting` — pokud produkt neměl marketingová data ani konkurenční texty, generování spadlo na `NameError`. To je pravděpodobná příčina „rozpadlého" chování.
2. **Batch simulace generovala čistou Triolu**: „Podprsenka/Kalhotky Triola", péče o prádlo, „| Triola.cz" v meta title. → Přepsáno na nikotinové sáčky vč. povinného legislativního varování.
3. **Tónové instrukce z Trioly** („bra-fitting rady", „oslavující ženskost") ve dvou funkcích → nahrazeno: Odborný průvodce / Prémiový / Moderní. UI selecty sladěny.
4. **Stuby produktů v `app.py`**: `"type": "Dámské spodní prádlo"`, „Dámské kalhotky", `f"Podprsenka Triola {kód}"` → „Nikotinové sáčky".
5. **USP extraktor** s příklady „košíčky do velikosti J, 47 střihů" → snus příklady (příchutě, mg/sáček, odeslání do 24 h).
6. **Brand Book záložka v UI**: pravidla i ukázkové fráze byly celé o podprsenkách → přepsáno na snus ToV (parametry mg/formát, diskrétnost, zákazy SZPI/ČOI, dospělé popisy příchutí).
7. **Modal ručního produktu**: „Střih podprsenky" + Perfect-Fit/T-Fit… → „Formát sáčků" (Slim, Mini, Super Slim, Regular, Dry Slim); „Dostupné barvy" → „Příchutě".
8. **app.js**: fallback charakteristiky střihů podprsenek → formáty sáčků; SEO simulace „47 střihů Triola do košíčku J" → snus varianta; loading hlášky („brafitting pravidla Trioly") → snus.
9. Drobné: komentáře „brand rules for Triola.cz", docstringy, literály `\n` — vše opraveno.

### Zbývá před nasazením
- Projít 1–2 reálné vygenerované texty (single i batch) a zkontrolovat legislativní varování na konci `eshop_desc2`.
- ~~Vytvořit `render.yaml`~~ → **HOTOVO** (2. kolo), služba `snusshop-copywriter`.
- ~~Kontrola syntaxe~~ → **HOTOVO**, vše kompiluje.

---

## 3. FUTURECYCLING — ZNOVU POSTAVEN (2. kolo)

`C:\Users\Acer\Desktop\FutureCycling_Copy` byl kompletně znovu vytvořen z vyčištěné šablony, s vlastním tone of voice (ne jen find-and-replace):

**Co obsahuje:**
- **Vlastní ToV pro prémiový cyklo obchod** (Bike&Coffee koncept): odbornost + konkrétní parametry (hmotnost, materiál, kompatibilita), jazyk zkušeného cyklisty, zákaz vymýšlení technických údajů, Zero-GPT pravidla, opatrnost u helem/brzd (žádné sliby absolutní ochrany).
- **Nový feed parser** pro Google Merchant RSS feed futurecycling.cz — otestováno na reálném feedu: 3048 položek → 1966 modelů, seskupování variant přes `item_group_id`.
- **Automatická detekce 19 kategorií sortimentu** (středová složení, zapletená kola, pohon, oblečení, výživa, kola…) s vlastními benefity pro copywriting.
- **Všech 7 formátů textů** (popisek, krátký/dlouhý HTML, LP, kategorie, článek, sociální sítě) + SEO snippety + hromadné generování 6 polí.
- UI kompletně přebrandované vč. Brand Book záložky s cyklo pravidly a ukázkami frází.
- `render.yaml` (služba `futurecycling-copywriter`), `.env`, `.gitignore` — připraveno na Render.

**Ověřeno:** aplikace nabootuje, načte 1966 produktů, vyhledávání funguje (CeramicSpeed, Enve…), batch simulace generuje všech 6 polí, web server renderuje UI. Nulová kontaminace z Trioly i Snusu.

**Před nasazením:** vygenerovat 1–2 reálné texty přes API a zkontrolovat kvalitu; případně doladit barvy UI (převzaty z Triola šablony).

---

## Shrnutí

| Projekt | Stav | Akce |
|---|---|---|
| Triola | Výborný, v souladu se strategií | 6 oprav provedeno a ověřeno |
| Snus-Shop | Vyčištěn, kompiluje, render.yaml připraven | 10 oprav, připraven k testu textů |
| FutureCycling | Znovu postaven s vlastním cyklo ToV, otestován | Připraven k testu textů |
