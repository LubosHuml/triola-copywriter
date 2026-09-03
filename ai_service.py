import os
import logging
import re
import time
from dotenv import load_dotenv
# openai a google-genai se importuji az pri prvnim pouziti (lazy) - grpc stack
# Gemini SDK sam o sobe zabira ~150 MB RAM, coz na 512MB Renderu zpusobovalo OOM.

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Default active model IDs based on verification
MODEL_MAPPING = {
    # Anthropic
    "claude-sonnet-5": "claude-sonnet-5",
    "claude-opus-5": "claude-opus-5",
    "claude-sonnet-4-6": "claude-sonnet-4-6",
    "claude-opus-4-8": "claude-opus-4-8",
    "claude-sonnet-4-5": "claude-sonnet-4-5-20250929",
    
    # OpenAI
    "gpt-4o": "gpt-4o",
    "gpt-4o-mini": "gpt-4o-mini",
    
    # Gemini
    "gemini-2.5-pro": "gemini-2.5-pro",
    "gemini-2.5-flash": "gemini-2.5-flash",
    "gemini-3.5-flash": "gemini-3.5-flash"
}

# The system prompt representing the brand rules for Triola.cz
TRIOLA_SYSTEM_PROMPT = """Jsi špičková česká copywriterka a specialistka na spodní prádlo (podprsenková stylistka) české značky Triola.cz.
Tvým úkolem je vytvářet texty v bezchybné, elegantní, plynulé a čtivé češtině, které dokonale sedí tónem a stylem naší značky.

VIZE, MISE A CLAIMY ZNAČKY:
- Vize: Pomáháme ženám cítit se příjemně a sebevědomě. Triola je symbolem sebepřijetí, ženské síly a spojení generací skrze dědictví kvality, tradice a inovace.
- Hlavní claimy (vhodné přirozeně zapojit): "Laskavá. Česká. Padnoucí.", "Tradice v každém stehu", "Každá velikost má svou krásu" (nabízíme velikosti od A do M a obvody 70 až 125).
- Bra-fitting: Víme, že až 80 % žen nosí špatnou velikost prádla. Zdůrazňujeme náš odborný poradenský servis a správné usazení podprsenky pro celodenní komfort.

CÍLOVÁ SKUPINA A PERSONY:
Naším hlavním publikem jsou aktivní ženy ve věku 30–40 let (zejména maminky, kterým se po porodu změnila postava a potřebují spolehlivé prádlo).
Cílíme na tři hlavní marketingové persony:
1. Moderní matka (hledá celodenní pohodlí, funkčnost a styl pro aktivní život).
2. Kreativní duše (zajímá ji etická výroba, lokálnost české značky, tradice a cost-per-wear).
3. Tradicionalistka nové generace (oceňuje časem prověřenou eleganci, špičkovou kvalitu a individuální péči).

ZÁKLADNÍ MARKETINGOVÁ PRAVIDLA A TÓN ZNAČKY:
1. Profesionalita a empatie: Píšeme s hlubokým pochopením pro potřeby žen. Známe potíže spojené s výběrem prádla (bolesti zad, zařezávající se ramínka, špatná podpora, zvedající se zadní obvod, asymetrie poprsí). Nabízíme řešení a úlevu.
2. Body Positivity (Sebevědomí): Všechny tvary a velikosti jsou krásné. Nepoužíváme slova jako "nedokonalosti", "problémy", "zamaskovat", "skrýt". Místo toho píšeme o "podtržení předností", "podpoře přirozených křivek", "zajištění jistoty" a "maximálním komfortu".
   ZÁKAZ VÝRAZU "UKRÝVAT SE": Prádlo se pod oblečením NIKDY neukrývá, neschovává ani nemizí — takové formulace naznačují, že je potřeba ho skrývat. Správně píšeme, že prádlo je "neviditelné pod oblečením", "nerýsuje se pod přiléhavým tričkem", "zůstává nenápadné" nebo "hladce splyne s postavou". Zakázané formulace: "ukrývá se pod oblečením", "schová se pod tričkem", "nikdo o něm nebude vědět".
3. Styl a plynulost: Píšeme pro čtenáře, ne pro roboty. Vyhýbej se klišé jako "must-have", "nechte se hýčkat", "jedinečný kousek" či "fascinující". Raději buď konkrétní (např. místo "skvělý materiál" napiš "pružný žakárový úplet s podílem elastanu").
4. Zákaz robotického AI jazyka: Vyhni se slovům jako "klíčový", "transformovat", "vstupte do světa", "navržen tak, aby", "představujeme vám". Piš přirozeně, jako bys mluvila s kamarádkou, ale s odbornou autoritou.
5. Správná terminologie: Používej termíny jako "flexi kostice", "T-šev", "Spacer košíček", "Perfect-Fit střih", "zadní díl s pevným podložením".
   ODBORNÉ KOREKCE (od produktové specialistky — ZÁVAZNÉ):
   - Flexi kostice se NEHÝBOU s tělem — správně: "přizpůsobí se pohybu těla", "nezapichují se do podpaží".
   - NIKDY nepiš, že podprsenka "opticky zmenší prsa o velikost" — žádný střih Triola prsa nezmenšuje. Piš o zpevnění, zformování a fixaci v ideální výšce.
   - Ramínka NIKDY nepopisuj jako "vypodložená", "polstrovaná" či "vyztužená", pokud to VÝSLOVNĚ není v prodejních argumentech.
   - Slovo "posazení" nepoužívej ("perfektní posazení" je špatně) — správně je "padnutí".
   - Kalhotky "padnou tak, jak mají" — nikdy "tam, kam mají".
   - Výšivka/krajka ve výstřihu: správně "pružná výšivka skryje drobnou asymetrii prsou a nezařezává se" — NIKDY "obejme celé ňadro" ani "vyrovná asymetrii".
   - Kalhotky střihu 31 jsou "klasické kalhotky" — NIKDY "klasické do pasu" (vyšší pas mají pouze kalhotky střihu 32).
KOREKTURY OD KOREKTORKY (list „korektura Triola a CZ") — ZÁVAZNÉ, platí pro CZ i SK:

A) ZAKÁZANÉ VYCPÁVKOVÉ FRÁZE — nepoužívej je v žádné podobě ani obměně:
   - jakákoli věta o „sladěné sadě" ("sladěná sada dodá jistotu", "…i ve dnech, kdy ji nikdo jiný nevidí",
     "…i pod jednoduché oblečení", "…působí upraveně a vydrží déle svěží"). Toto klišé je zakázané úplně.
   - "…zůstanou tam, kde mají být" / "…tam, kam mají" / "drží na svém místě"
   - "ať máte za sebou jakkoli dlouhý den"
   - "a nekroutí se ani při sezení"
   - "odhaluje jen spodní část hýždí"
   - "Tradiční střih, který drží slovo"
   - "Kalhotky, na které během dne ani nepomyslíte"
   - "Klasické kalhotky s klidným, přirozeným padnutím"
   - "s ženským vykrojením"
   - "neotlačují" (u prádla se toto slovo nepoužívá)
   - "rozešité švy" (nikdy, ani když to zmiňuje znalostní báze střihu — piš "měkké švy")

B) POVINNÉ NÁHRADY — vlevo špatně, vpravo správně:
   - "opora, kterou poznáte při prvním zkoušení"  ->  "opora, kterou oceníte při celodenním nošení"
   - "pevný zadní obvod se nezvedá"  ->  "pevný zadní obvod podprsenky se při nošení neposouvá, ale zůstává na místě"
   - "hygienický klínek pro celodenní čistotu"  ->  "bavlněný klínek pro celodenní komfort při nošení"
   - "Klasický střih pohodlně obepne boky i zadní díl"  ->  "klasický střih kalhotek zajistí pohodlí při nošení"
   - "Vybírejte velikost přesně podle svých měr…"  ->  "najděte si správnou velikost dle velikostní tabulky"
   - "s ženským vykrojením"  ->  "s vykrojeným zadním dílem, který se neproznačuje pod oblečením"
   - "shodná řada / ze shodné řady"  ->  "stejná řada / ze stejné řady"
   - "zůstanou dlouho ve formě"  ->  "neztratí svoji funkčnost"

C) BARVY: přívlastek "hluboká/hluboké/hlubokému" u barvy je zakázaný ("hluboké vínové", "hlubokému bordó").
   Tmavý odstín popisuj slovem "tmavě…" (tmavě vínová, tmavě modrá). Slovenská verze musí použít
   stejný odstín jako česká, jen slovensky (tmavě vínová -> tmavovínová / tmavo vínová).

D) NEVYMÝŠLEJ KONSTRUKČNÍ PRVKY. Pokud nejsou VÝSLOVNĚ v prodejních argumentech, nesmíš zmínit:
   légy, rozešité švy, měkce podložená / vypodložená ramínka, hygienický klínek, kostice, výztuhu.
   Raději o prvku nepiš vůbec, než abys ho odhadl.

E) PIŠ VĚCNĚ. Každá věta musí nést konkrétní informaci o produktu (materiál, střih, funkce, použití).
   Básnivé, prázdné a kostrbaté obraty vynech — korektorka je označuje jako „nedává smysl".
6. ZÁKAZ ZMÍNĚNÍ NÁZVŮ KOLEKCÍ: V textu NIKDY neuváděj ani nezmiňuj žádné názvy kolekcí (např. Selena, Tina, Olivia, atd.). Tuto informaci do textu nepromítej, a to ani tehdy, pokud je název kolekce uveden v původním popisku nebo v prodejních argumentech. Značku prezentujeme jako celek bez pojmenování jednotlivých kolekcí v produktových popiscích.

INFORMACE O STŘIZÍCH TRIOLA (ZNALOSTNÍ BÁZE):
- Perfect-Fit: Hladká, tence vyztužená podprsenka s kosticemi. Nezvětšuje objem, ale fixuje prsa v ideální výšce. Vhodná pro střední a velké velikosti pod přiléhavé oblečení.
- T-Fit: Třídílný košíček s T-švem. Dokonale prsa zakulatí, pozvedne a zafixuje na středu. Klasika pro velkou oporu.
- Top-Fit / Sensual-Fit: Hladká vyztužená podprsenka s nižším středem. Skvělá do hlubokých výstřihů.
- Fixed-Fit: Zpevňující střih pro těžká prsa, pevně drží na středu, široká ramínka pro úlevu zad a ramen.
- Soft-Fit (Bez kostic): Maximální svoboda pohybu a pohodlí bez kostic. Třídílný košíček s bočním dílkem přesto prsa spolehlivě zafixuje.
- Plavky Triola: Plavková podprsenka z rychleschnoucího materiálu, s pevným podložením, které drží i ve vodě.

Píšeme česky, čtivě, plynule, spisovně."""

SEO_SYSTEM_PROMPT = """Jsi senior SEO copywriter specializovaný na psychologii pozornosti. Přepisuješ meta title, meta description a H1 podle principů prediktivního zpracování mozku: pozornost vzniká jen tam, kde dojde k mírnému narušení očekávání, a klik vzniká jen tam, kde je nejdřív potvrzena relevance.

PRINCIPY (v tomto pořadí priorit):

P1 – Potvrzení predikce (relevance) — POVINNÉ, vždy první.
Uživatel skenuje SERP s hotovou predikcí. Primární klíčové slovo nebo jeho přirozená varianta MUSÍ být v první polovině title. Bez potvrzení relevance mozek zbytek nezpracuje. Nikdy neobětuj relevanci kreativitě.

P2 – Jeden pattern break (prediction error).
Po potvrzení relevance přidej PRÁVĚ JEDEN prvek, který se vymyká vzoru SERPu: konkrétní senzorický detail, neokrouhlé číslo, nečekaný benefit, časový rámec. Pokud máš konkurenční titles, identifikuj společný vzor konkurence a vědomě ho v jednom prvku poruš. Jeden break, ne tři — víc odchylek = šum a nedůvěra.

P3 – Otevřená smyčka v description.
Description nesmí říct všechno. Otevři konkrétní informační mezeru, kterou uzavře až klik. Vzorec: [konkrétní fakt nebo problém] + [příslib konkrétní odpovědi na stránce] + [CTA]. Zakázáno: shrnout obsah stránky tak, že klik už není potřeba.

P4 – Specifičnost místo adjektiv.
Zakázaná slova bez doplnění faktem: kvalitní, nejlepší, široký výběr, skvělý, luxusní, výhodný. Každé tvrzení nahraď konkrétem: materiál, číslo (preferuj neokrouhlá: 47, ne 50), čas, smyslový vjem. Mozek prázdná adjektiva nesimuluje — konkrétní detail ano.

P5 – Predikční kontinuita title → H1 → stránka.
H1 musí potvrdit a rozvinout slib z title. Ne doslovná kopie title, ne jiné téma. Test: kdyby uživatel viděl jen title a pak jen H1, musí mít pocit "ano, jsem na správném místě a dozvím se víc".

P6 – Intent určuje tón breaku:
- Transakční: break = konkrétní výhoda nákupu (dostupnost, rychlost, záruka, unikátní parametr)
- Informační: break = otevřená smyčka / překvapivý fakt / číslo
- Srovnávací: break = jasné kritérium rozhodnutí
- Navigační: minimální break, maximální jasnost + brand

TVRDÉ LIMITY:
- Title: max 60 znaků včetně mezer (cíl 50–58); brand suffix " | {brand}" přidej jen pokud se vejde, u homepage vždy
- Description: 120–155 znaků
- H1: max 70 znaků, bez brand suffixu
- Jazyk: čeština, přirozená, bez keyword stuffingu (KW max 1× v title, max 1× v description)
- Žádné CAPS, žádné vykřičníky v title, max 1 vykřičník v description
- Žádné nepodložené sliby (doprava zdarma jen pokud je v usp)

VÝSTUPNÍ FORMÁT:
Vždy vrať pouze čistou JSON strukturu (bez markdown uvozovek jako ```json) s těmito klíči:
{
  "url": "adresa stránky",
  "title": "navržený title",
  "title_znaku": délka title v čísle,
  "description": "navržený description",
  "desc_znaku": délka description v čísle,
  "h1": "navržený h1",
  "pattern_break": "co je ten jeden break a proč funguje",
  "smycka": "jakou mezeru otevírá description",
  "rizika": "případné upozornění"
}
Nepřidávej žádný další komentář mimo tuto strukturu."""

FORMAT_PROMPTS = {
    "popisek": """Vytvoř produktový popisek (popis produktu) pro e-shop Triola.cz.
Požadovaná struktura textu:
1. Chytlavý úvod (1-2 věty) - zaměř se na pocity, pohodlí a design.
2. Krátký odstavec popisující hlavní vlastnosti modelu a to, jak se v něm bude žena cítit.
3. Seznam klíčových výhod a technických benefitů (v odrážkách):
   - Uveď střih, kostice, ramínka a materiál.
   - Popiš, jakou oporu prsům poskytuje a pro koho je vhodný.
4. Doporučení stylistky: tip na nošení, s čím kombinovat (např. se stejnými kalhotkami) nebo na co si dát pozor při výběru.
Celý text musí působit jako od profesionální stylistky.""",

    "kratky_popis_html": """Vytvoř krátký produktový popisek v jednoduchém HTML kódu. 
Text by měl obsahovat 1 až 2 čtivé, prodejní odstavce (používej pouze tagy <p> a <strong> pro zvýraznění). 
Nepoužívej žádné odrážky (ul, li), nadpisy (h2, h3), ani žádný obalový kód (html, body, head). 
Piš přirozeně, vřele a profesionálně.""",

    "dlouhy_popis_html": """Vytvoř dlouhý produktový popisek v jednoduchém HTML kódu. 
Struktura musí obsahovat:
1. Úvodní poutavý odstavec (tagy <p> a <strong> pro důležité vlastnosti).
2. Podnadpis <h2> s názvem střihu a popisem jeho chování na těle.
3. Odrážkový seznam klíčových výhod a konstrukčních specifikací (tagy <ul>, <li>). Uveď typ kostic, provedení ramínek, obvodu a materiálu.
4. Podnadpis <h3> s doporučením stylistky (bra-fitting tipy a rady pro výběr správné velikosti).
5. Závěrečný odstavec shrnující celkový pocit z nošení.
Používej pouze tagy <p>, <strong>, <ul>, <li>, <h2>, <h3>. 
Nepoužívej žádné obalové tagy jako <html>, <body>, <head>, ani inline styly. Výstup musí být čistý HTML fragment.""",

    "lp": """Vytvoř text pro prodejní přistávací stránku (Landing Page) zaměřenou na tento konkrétní produkt nebo modelovou řadu.
Struktura by měla obsahovat:
1. Hlavní titulek (H1) - silný, emocionální a chytlavý benefit (např. o úlevě pro záda nebo o sebevědomí).
2. Podtitulek (H2) - rozvinutí hlavní myšlenky.
3. Úvodní text (Hook) - popiš situaci/problém, se kterým se ženy potýkají, a uveď produkt jako řešení.
4. Sekce „Proč si vybrat právě tento model?“ - 3-4 klíčové body (s mezititulky H3) popisující střih, materiál, ramínka a oporu.
5. Sekce s recenzí/stylistickým posudkem - proč tento produkt milují tisíce Češek.
6. Výzva k akci (CTA) - přesvědčivá výzva k vyzkoušení.""",

    "kategorie": """Vytvoř text pro kategorii e-shopu (např. "Podprsenky Perfect-Fit" nebo "Spodní prádlo pro plné křivky").
Struktura:
1. Titulek kategorie (H1).
2. Krátký úvodní text (2-3 věty) uvádějící zákaznici do naší nabídky a filozofie této kategorie.
3. Přehledný průvodce „Jak vybrat a v čem tkví tajemství této kategorie“ s rozdělením na klíčové vlastnosti (H2, H3).
4. Praktické tipy na nošení a péči o prádlo z této kategorie.
Text by měl organicky (přirozeně) obsahovat zadaná klíčová slova.""",

    "clanek": """Vytvoř poutavý a edukativní článek na blog Triola.cz inspirovaný tímto produktem nebo jeho střihem.
Struktura:
1. Chytlavý titulek článku (H1) - např. formou otázky nebo slibu rady (např. "5 mýtů o velkém poprsí..." nebo "Jak na zařezávající se ramínka...").
2. Poutavý úvodník (Perex) - vtáhni čtenářku do děje.
3. Tělo článku rozdělené do 3-4 tematických sekcí s podnadpisy (H2) - popiš anatomii prádla, stylistické tipy a jak tento konkrétní model pomáhá.
4. Závěr s praktickým shrnutím a přátelským povzbuzením.
Styl psaní: přátelský, odborný, čtivý, inspirativní. Délka textu by měla odpovídat požadovanému rozsahu.""",

    "socialni_site": """Vytvoř sadu 3 různých příspěvků na sociální sítě (Facebook / Instagram) propagujících tento produkt.
1. Příspěvek 1: Emoční a produktový (zaměřený na pocit pohodlí, úlevy a sebevědomí).
2. Příspěvek 2: Odborný (tip stylistky, vysvětlení střihu, konstrukčních detailů).
3. Příspěvek 3: Rychlý/prodejní (s výzvou k nákupu, zaměřený na barvy a limitovanou edici).
Každý příspěvek musí obsahovat:
- Chytlavý první řádek (hook).
- Vhodné emojis (decentně, žádný spam).
- Výzvu k akci (CTA).
- 4-5 relevantních hashtagů (např. #triolacz #spodnipradlo #bodypositivity #ceskaznacka)."""
}

# Mapa marketingovych barev na SEO vykonne ekvivalenty.
# V NAZVU a META TITLE se pouziva SEO barva (lide ji hledaji),
# marketingovy nazev smi zaznit v popisu.
SEO_COLOR_MAP = {
    "dračí ovoce": "sytě růžová",
    "petrolejová": "tmavě zelená",
    "petrol": "tmavě zelená",
    "pudr": "pudrově růžová",
    "pudrová": "pudrově růžová",
    "écru": "krémová",
    "ecru": "krémová",
    "ivory": "smetanová",
    "champagne": "béžová",
    "šampaň": "béžová",
    "nude": "tělová",
    "skin": "tělová",
    "marsala": "vínová",
    "bordó": "tmavě vínová",
    "bordeaux": "tmavě vínová",
    "čokoládová": "hnědá",
    "burgundy": "vínová",
    "antracit": "tmavě šedá",
    "antracitová": "tmavě šedá",
    "grafit": "tmavě šedá",
    "grafitová": "tmavě šedá",
    "khaki": "olivově zelená",
    "oliva": "olivově zelená",
    "lila": "světle fialová",
    "levandulová": "světle fialová",
    "fuchsia": "sytě růžová",
    "fuchsiová": "sytě růžová",
    "malinová": "sytě růžová",
    "lososová": "světle růžová",
    "korálová": "růžová",
    "mentolová": "světle zelená",
    "cappuccino": "béžová",
    "mocca": "hnědá",
    "moka": "hnědá",
    "karamelová": "béžová",
    "noční modrá": "tmavě modrá",
    "inkoustová": "tmavě modrá",
    "půlnoční modrá": "tmavě modrá",
    "denim": "modrá",
    "jeans": "modrá",
    "nachová": "fialová",
    "lilková": "tmavě fialová",
    "rosé": "růžová",
    "navy": "tmavě modrá",
    "cherry": "třešňově červená",
    "shadow": "tmavě šedá",
    "ash": "šedá",
    "mint": "mátově zelená",
    "lambrusco": "vínová",
    "dusty rose": "starorůžová",
    "deco rose": "růžová",
    "make-up": "tělová",
    "lunar rock": "světle šedá",
    "nugát": "oříškově hnědá",
    "slonová kost": "smetanová",
    "eurová": "tělová",
    "kardinál": "tmavě červená",
    "jahodová": "jahodově červená",
    "smaragdová": "smaragdově zelená",
    "koňaková": "karamelově hnědá",
    "limeta": "limetkově zelená",
    "tm. růžová": "tmavě růžová",
}


def color_prompt_block(colors):
    """
    Sestavi instrukci k barve pro prompt.
    - prazdna/zadna barva -> texty bez barvy (nikdy 'standardni')
    - marketingova barva -> doplni SEO ekvivalent pro nazev a meta title
    """
    colors = [c for c in (colors or []) if str(c).strip()
              and str(c).strip().lower() not in ("standardní", "standardni", "none")]
    if not colors:
        return ("BARVA: není uvedena. Název produktu, popisy i metadata piš BEZ zmínky "
                "o barvě. NIKDY nepiš 'standardní barva' ani barvu nevymýšlej.")
    parts = []
    for c in colors:
        seo = SEO_COLOR_MAP.get(str(c).strip().lower())
        if seo and seo != str(c).strip().lower():
            parts.append(f"{c} (do NÁZVU PRODUKTU a META TITLE použij SEO variantu: "
                         f"'{seo}'; marketingový název '{c}' můžeš zmínit v popisu)")
        else:
            parts.append(str(c))
    return ("DOSTUPNÉ BARVY: " + "; ".join(parts) +
            "\nPRAVIDLO: V názvu a meta title vždy hledaná (SEO) podoba barvy. "
            "V celém textu piš VÝHRADNĚ o této barvě - žádné jiné barvy z podkladů.")


def key_points_block(product_info):
    """
    Body z klicoveho slova "Nejdůležitější:" v prodejnich argumentech.
    Kdyz jsou vyplnene, MUSI zaznit v odrazkach hlavniho popisu.
    """
    pts = product_info.get("key_points") or []
    if not pts:
        return ""
    body = "\n".join(f"   - {p}" for p in pts)
    return (f"""
POVINNÉ ODRÁŽKY (kolegyně je označila slovem „Nejdůležitější:") — KRITICKÉ PRAVIDLO:
V hlavním popisu (eshop_desc1) MUSÍ být seznam <ul> a v něm samostatná <li> odrážka
pro KAŽDÝ z těchto bodů. Formuluj je čtivě a prodejně, ale význam zachovej přesně
a nic z nich nevynechávej:
{body}
   Pořadí odrážek zachovej. Další odrážku navíc přidávej jen tehdy, když je opřená
   o prodejní argumenty. Ve slovenské verzi musí být stejné odrážky, jen slovensky.
""")


def tech_specs_block(product_info):
    """Technicke parametry (sirka raminek, zapinani) - fakta, ktera se nesmi menit."""
    tech = product_info.get("tech_specs") or []
    if not tech:
        return ""
    body = "\n".join(f"   - {t}" for t in tech)
    return (f"""
TECHNICKÉ PARAMETRY OD VÝROBY — uveď je v popisu, aby zákaznice hned věděla, co čekat:
{body}
   Tato čísla jsou závazná: NEMĚŇ je, nezaokrouhluj a nedomýšlej k nim nic dalšího.
   Zapracuj je přirozeně do textu nebo jako samostatnou odrážku (klidně i v POPIS 2).
   Ve slovenské verzi uveď stejné hodnoty.
""")


def category_prompt_block(product_info):
    """Instrukce podle kategorie produktu: plavky / plazove obleceni / pradlo."""
    cat = str(product_info.get("category", "") or "").lower()
    if cat == "plavky":
        return """
KATEGORIE PRODUKTU: PLAVKY (nikoli spodní prádlo!) — KRITICKÉ PRAVIDLO
- Jde o PLAVKY na pláž, k bazénu a na dovolenou. Text musí být jednoznačně o plavkách.
- V názvu i v textech používej VŽDY plavkové názvosloví: "plavková podprsenka", "plavkové kalhotky",
  "plavkové kalhotky do pasu", "plavkové brazilky", "bokové plavkové kalhotky", "jednodílné plavky", "tankiny".
  NIKDY nepiš jen "podprsenka" nebo "kalhotky" bez slova plavkové.
- ZAKÁZANÉ formulace (patří ke spodnímu prádlu, ne k plavkám): "pod oblečením", "pod tričkem",
  "nerýsuje se pod oblečením", "neviditelné pod oblečením", "do práce", "na celý den v kanceláři",
  "pod přiléhavé šaty", "bra-fitting poradna".
- Piš o tom, na čem u plavek záleží: držení a opora i ve vodě a při pohybu, rychleschnoucí materiál,
  odolnost vůči chloru, slané vodě a slunci, pohodlí při plavání i opalování, jistota na pláži,
  tvarování postavy v plavkách, možnost kombinovat vrchní a spodní díl.
- Kontext použití: dovolená, pláž, bazén, aquapark, léto — nikdy kancelář nebo každodenní nošení pod oblečením.
"""
    if cat == "plazove":
        return """
KATEGORIE PRODUKTU: PLÁŽOVÉ OBLEČENÍ (kaftan, pareo, plážové šaty, tunika) — KRITICKÉ PRAVIDLO
- NEJDE o spodní prádlo ANI o plavky. NIKDY nepoužívej terminologii podprsenek ani kalhotek
  (košíčky, kostice, ramínka, obvod, nohavičky, zadní díl, bra-fitting).
- Piš o střihu, materiálu a splývavosti, délce, průsvitnosti, snadném oblékání přes plavky,
  o stínu a ochraně před sluncem, o nošení na pláži, k bazénu, na procházku k moři i na drink.
- Zdůrazni, že jde o doplněk přes plavky — ne o produkt, který se nosí pod oblečením.
"""
    return ""


def execute_with_retry(api_func, *args, max_retries=5, initial_delay=2.0, backoff_factor=2.0, **kwargs):
    """
    Spustí zadanou API funkci s automatickým opakováním v případě přetížení nebo překročení limitů.
    Používá exponenciální backoff.
    """
    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            return api_func(*args, **kwargs)
        except Exception as e:
            err_msg = str(e).lower()
            err_type = type(e).__name__
            
            # Detekce dočasných chyb (přetížení, překročení limitu požadavků, dočasné vnitřní chyby)
            is_transient = (
                any(x in err_msg for x in ["overloaded", "rate limit", "rate_limit", "429", "529", "503", "500", "502", "exhausted", "quota", "tempo", "busy", "limit exceeded", "timeout", "deadline"])
                or any(x in err_type for x in ["RateLimitError", "APIConnectionError", "InternalServerError", "APITimeoutError", "OverloadedError", "ResourceExhausted"])
            )
            
            if is_transient and attempt < max_retries:
                logging.warning(
                    f"Dočasné selhání API ({err_type}: {e}). "
                    f"Pokus {attempt}/{max_retries}. Čekám {delay}s před dalším pokusem..."
                )
                time.sleep(delay)
                delay *= backoff_factor
            else:
                logging.error(f"API volání definitivně selhalo po {attempt} pokusech: {e}")
                raise e

def generate_with_openai(api_key, model, system_prompt, user_prompt):
    """Call OpenAI API using modern SDK client."""
    import openai
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=2500
    )
    return response.choices[0].message.content

# Modely, ktere parametr temperature nepodporuji. Novejsi verze knihovny anthropic
# ho uz nemaji ani v signature - misto HTTP chyby vyhodi TypeError
# ("Messages.create() got an unexpected keyword argument 'temperature'").
NO_TEMPERATURE_PREFIXES = (
    "claude-opus-5", "claude-sonnet-5", "claude-fable-5", "claude-haiku-5",
    "claude-opus-4-6", "claude-opus-4-7", "claude-opus-4-8",
)
_no_temperature_cache = set()   # naucene za behu


def _supports_temperature(model):
    m = str(model or "")
    if m in _no_temperature_cache:
        return False
    return not any(m.startswith(pfx) for pfx in NO_TEMPERATURE_PREFIXES)


def generate_with_anthropic(api_key, model, system_prompt, user_prompt):
    """Call Anthropic API using message structure.
    Novejsi modely parametr temperature nepodporuji - u nich se rovnou neposila.
    Kdyby ho odmitl i jiny model, volani se zopakuje bez nej a model se zapamatuje."""
    import anthropic  # lazy - setri ~40 MB RAM pri startu
    client = anthropic.Anthropic(api_key=api_key)
    kwargs = dict(
        model=model,
        max_tokens=16000,  # 12 poli (CZ+SK) + thinking u Sonnet 5/Opus
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    if not _supports_temperature(model):
        message = client.messages.create(**kwargs)
    else:
        try:
            message = client.messages.create(temperature=0.7, **kwargs)
        except (TypeError, Exception) as e:
            msg = str(e).lower()
            if "temperature" in msg:
                logging.info(f"Model '{model}' nepodporuje temperature - "
                             f"opakuji bez parametru a příště ho už neposílám.")
                _no_temperature_cache.add(str(model))
                message = client.messages.create(**kwargs)
            else:
                raise
    # Novejsi modely mohou vracet ThinkingBlock pred textem - vezmi vsechny textove bloky
    text_parts = [b.text for b in message.content if getattr(b, "type", "") == "text" and hasattr(b, "text")]
    if not text_parts:
        raise RuntimeError(f"Model '{model}' nevratil zadny textovy blok (bloky: {[getattr(b, 'type', '?') for b in message.content]})")
    return "\n".join(text_parts)

def generate_with_gemini(api_key, model, system_prompt, user_prompt):
    """Call Google Gemini API using new google-genai client."""
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
            max_output_tokens=2500
        )
    )
    return response.text

FALLBACK_CLAUDE_MODEL = "claude-sonnet-4-6"

def generate_with_anthropic_fallback(api_key, model, system_prompt, user_prompt):
    """Zavolá Anthropic API; pokud zadaný model není na klíči dostupný (404 not_found),
    automaticky přepne na záložní model, aby hromadné generování nespadlo."""
    try:
        return generate_with_anthropic(api_key, model, system_prompt, user_prompt)
    except Exception as e:
        msg = str(e).lower()
        model_missing = ("not_found" in msg or "not found" in msg or "404" in msg)
        if model_missing and model != FALLBACK_CLAUDE_MODEL:
            logging.warning(f"Model '{model}' není na API klíči dostupný ({e}). Přepínám na záložní '{FALLBACK_CLAUDE_MODEL}'.")
            return generate_with_anthropic(api_key, FALLBACK_CLAUDE_MODEL, system_prompt, user_prompt)
        raise


def generate_copywriting(product_info, format_type, model_key, tone_key, length_key, keywords="", custom_instructions=""):
    """
    Generates copywriting based on product data, format, selected model and configurations.
    """
    # 1. Select the API key and client method based on model_key
    model_name = MODEL_MAPPING.get(model_key, model_key)
    
    # 2. Extract API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    # Build prompt context
    prod_title = product_info.get("generic_title", "Podprsenka Triola")
    prod_code = product_info.get("model_code", "")
    prod_colors = ", ".join([c for c in product_info.get("all_colors", []) if str(c).strip()]) or "není uvedena"
    prod_cut = product_info.get("cut_name", "Neznámý střih")
    prod_char = product_info.get("characteristics", "")
    prod_benefits = "\n - " + "\n - ".join(product_info.get("benefits", [])) if product_info.get("benefits") else ""
    prod_price = product_info.get("base_price", "")
    prod_desc = product_info.get("combined_description", "")
    prod_docx = product_info.get("docx_description", "")
    prod_recommendation = product_info.get("recommendation", "")
    
    # Excel marketing data fields
    collection = product_info.get("collection", "")
    sales_arguments = product_info.get("sales_arguments", "")
    target_group = product_info.get("target_group", "")
    meta_title = product_info.get("meta_title", "")
    meta_description = product_info.get("meta_description", "")
    extra_descriptions = product_info.get("extra_descriptions", "")
    
    # Clean HTML or spaces from description
    prod_desc_clean = re.sub(r'<[^>]*>', '', prod_desc)
    prod_desc_clean = re.sub(r'\s+', ' ', prod_desc_clean).strip()
    # Limit original description context size
    prod_desc_clean = prod_desc_clean[:1000]
    
    # Format tone instructions
    tone_instructions = ""
    if tone_key == "empaticky":
        tone_instructions = "Tón: Hluboce empatický, chápavý, povzbuzující a profesionálně stylistický (bra-fitting rady)."
    elif tone_key == "elegantni":
        tone_instructions = "Tón: Elegantní, smyslný, oslavující ženskost a luxusní pocit z nošení."
    elif tone_key == "moderni":
        tone_instructions = "Tón: Moderní, dynamický, svěží a aktivní lifestyle."
        
    length_instructions = ""
    if length_key == "kratky":
        length_instructions = "Délka: Stručný a úderný text (cca 100-200 slov)."
    elif length_key == "stredni":
        length_instructions = "Délka: Standardní, vyvážený rozsah (cca 250-400 slov)."
    elif length_key == "dlouhy":
        length_instructions = "Délka: Detailní, rozsáhlý a vyčerpávající text (cca 500-800 slov)."

    keyword_instructions = f"Do textu přirozeně (organicky a se správným skloňováním) zakomponuj tato klíčová slova: {keywords}" if keywords else ""
    custom_instructions_block = f"Speciální požadavky na text: {custom_instructions}" if custom_instructions else ""

    # Assemble user prompt
    marketing_block = ""
    if collection or sales_arguments or target_group or extra_descriptions:
        marketing_block = "\nDŮLEŽITÉ PODKLADY Z MARKETINGOVÉ TABULKY ZNAČKY:\nPři tvorbě textu povinně vycházej a dominantně stav na těchto oficiálních marketingových prodejních argumentech:\n"
        if target_group: 
            marketing_block += f"- Cílová skupina / Vhodné pro: {target_group}\n"
        if sales_arguments: 
            marketing_block += f"- Oficiální prodejní argumenty: {sales_arguments}\n"
        if extra_descriptions: 
            marketing_block += f"- Doplňující podklady/popisy: {extra_descriptions}\n"
        if meta_title: 
            marketing_block += f"- Doporučený titulek (Meta Title): {meta_title}\n"
        if meta_description: 
            marketing_block += f"- Doporučený popisek (Meta Description): {meta_description}\n"
        marketing_block += "-----------------\n"

    user_prompt = f"""
Níže jsou uvedeny specifikace produktu, pro který máš napsat text:
-----------------
NÁZEV PRODUKTU: {prod_title}
KÓD MODELU: {prod_code}
STŘIH / TYP PRODUKTU: {prod_cut}
CHARAKTERISTIKA: {prod_char}
OFICIÁLNÍ KONSTRUKČNÍ SPECIFIKACE STŘIHU (z Wordu): {prod_docx if prod_docx else 'Není specifikováno'}
KLÍČOVÉ VÝHODY: {prod_benefits}
DOPORUČENÉ PRODEJNÍ ARGUMENTY A TIPY STYLISTKY: {prod_recommendation if prod_recommendation else 'Nejsou specifikovány'}
{color_prompt_block(product_info.get("all_colors"))}{category_prompt_block(product_info)}{key_points_block(product_info)}{tech_specs_block(product_info)}
DŮLEŽITÉ UPOZORNĚNÍ K NÁZVŮM KOLEKCÍ: V textu NIKDY neuváděj ani nezmiňuj žádné názvy kolekcí (např. Selena, Tina, Olivia, atd.). Pokud se název jakékoliv kolekce objeví v původním popisu nebo v marketingových podkladech, ignoruj ho a nezmiňuj.
PŮVODNÍ POPIS PRODUKTU: {prod_desc_clean}
-----------------
{marketing_block}
POKYNY K FORMÁTU TEXTU:
{FORMAT_PROMPTS.get(format_type, FORMAT_PROMPTS['popisek'])}

DALŠÍ SPECIFICKÉ PARAMETRY:
{tone_instructions}
{length_instructions}
{keyword_instructions}
{custom_instructions_block}

Napiš pouze samotný výsledný text v češtině, nepoužívej žádný úvodní ani závěrečný komentář typu "Zde je váš text:"."""

    logging.info(f"Generování textu typu '{format_type}' přes model '{model_name}'...")
    
    try:
        if model_key.startswith("claude"):
            if not anthropic_key:
                raise ValueError("Chybí ANTHROPIC_API_KEY v souboru .env.")
            text = execute_with_retry(generate_with_anthropic_fallback, anthropic_key, model_name, TRIOLA_SYSTEM_PROMPT, user_prompt)
            
        elif model_key.startswith("gpt"):
            if not openai_key:
                raise ValueError("Chybí OPENAI_API_KEY v souboru .env.")
            text = execute_with_retry(generate_with_openai, openai_key, model_name, TRIOLA_SYSTEM_PROMPT, user_prompt)
            
        elif model_key.startswith("gemini"):
            if not google_key:
                raise ValueError("Chybí GOOGLE_API_KEY v souboru .env.")
            text = execute_with_retry(generate_with_gemini, google_key, model_name, TRIOLA_SYSTEM_PROMPT, user_prompt)
            
        else:
            raise ValueError(f"Nepodporovaný typ modelu: {model_key}")
            
        # Clean up HTML markdown blocks if returned
        if "html" in format_type:
            text = re.sub(r'^```(?:html|xml)?\s*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\s*```$', '', text)
            text = text.strip()
        return text
        
    except Exception as e:
        logging.error(f"Chyba při generování AI textu: {e}")
        raise e

# Local simulated generator fallback (useful for sandbox, testing, or API limit fallbacks)
def get_simulated_copywriting(product_info, format_type, tone_key):
    """Generates high quality template-based Czech text for local testing."""
    prod_title = product_info.get("generic_title", "Podprsenka Triola")
    prod_code = product_info.get("model_code", "28746")
    prod_colors = ", ".join(product_info.get("all_colors", ["černá"]))
    prod_cut = product_info.get("cut_name", "Perfect-Fit")
    
    intro = f"Hledáte spodní prádlo, které vám poskytne dokonalou oporu a zároveň se budete po celý den cítit neuvěřitelně pohodlně? **{prod_title}** v elegantním střihu **{prod_cut}** je navržena přesně tak, aby splnila vaše nejvyšší nároky."
    
    body = f"Tato podprsenka je skvělým spojením tradičního českého řemesla a moderních technologií. Střih **{prod_cut}** se vyznačuje precizně vypracovanými košíčky, které dokonale obejmou poprsí a zafixují ho v ideální výšce. V kombinaci s flexibilními kosticemi a širokými ramínky, která spolehlivě odlehčí zádům a krční páteři, nabízí model s kódem **{prod_code}** celodenní úlevu a jistotu, ať už vás čeká náročný pracovní den, nebo společenská událost."
    
    benefits = f"""### Klíčové vlastnosti modelu {prod_code}:
* **Osvědčený střih {prod_cut}**: Navržený pro perfektní fixaci a optimální tvarování dekoltu.
* **Měkká a stabilní podpora**: Pevný obvod drží prádlo spolehlivě na místě (až 80 % váhy nese obvod, ne ramínka!).
* **Prvotřídní materiály**: Jemný úplet je prodyšný a mimořádně příjemný k pokožce.
* **Užitečné detaily**: Ramínka se nezařezávají a jejich šířka se stupňuje s rostoucí velikostí košíčku.
* **Barevná variabilita**: Model je dostupný v barvách: {prod_colors}."""

    stylist = """#### 💡 Doporučení podprsenkové stylistky Triola:
Pro zaručení 100% funkčnosti podprsenky je nejdůležitější zvolit správnou velikost obvodu. Ten musí být dostatečně pevný a neměl by se na zádech posouvat směrem nahoru. Pokud váháte, zvolte raději o číslo menší obvod a o číslo větší košíček (tzv. sesterskou velikost)."""

    if format_type == "kratky_popis_html":
        return f"<p>Zažijte výjimečné pohodlí a podporu s podprsenkou <strong>{prod_title}</strong> v elegantní barvě <strong>{prod_colors}</strong>. Hladké vypracování a prvotřídní materiály zajistí, že se podprsenka nerýsuje pod oblečením a stane se vaší druhou kůží po celý den.</p>"
        
    if format_type == "dlouhy_popis_html":
        return f"<p>Hledáte spodní prádlo, které vám poskytne dokonalou oporu a zároveň se budete po celý den cítit neuvěřitelně pohodlně? <strong>{prod_title}</strong> v elegantní barvě <strong>{prod_colors}</strong> je navržena přesně tak, aby splnila vaše nejvyšší nároky a přinesla celodenní úlevu.</p><h2>Prvotřídní střih {prod_cut}</h2><ul><li><strong>Tence vyztužené košíčky</strong> prsa nezvětšují, ale fixují v ideální výšce.</li><li><strong>Flexi kostice</strong> se přizpůsobí pohybu těla a nikde netlačí.</li><li><strong>Široká a pohodlná ramínka</strong> spolehlivě odlehčují krční páteři a zádům.</li><li>Jemný a ultra hladký úplet, který je mimořádně příjemný k pokožce.</li></ul><h3>💡 Doporučení stylistky Triola</h3><p>Pro zaručení 100% funkčnosti podprsenky doporučujeme zvolit dostatečně pevný zadní obvod, který by se neměl na zádech posouvat nahoru. Tento model v barvě {prod_colors} je ideální pro každodenní nošení pod přiléhavé oblečení.</p>"

    if format_type == "socialni_site":
        return f"""### 📱 Příspěvek 1 (Pohodlí a emoce)
Hledáte podprsenku, která spolehlivě unese i větší poprsí a uleví vašim zádům? 🤍
Model **{prod_title}** se střihem **{prod_cut}** je tu přesně pro vás! Hladká ramínka a jemný materiál se postarají o vaše celodenní pohodlí, zatímco precizní střih vytvoří krásný dekolt. 
Užijte si den bez nepříjemného tlačení! 🌸
👉 Odkaz v bio.
#triolacz #pohodli #sebevedomi #ceskaznacka

---
### 📱 Příspěvek 2 (Odborný a střihový)
Věděly jste, že až 80 % váhy poprsí by měl nést obvod podprsenky, a ne ramínka? 💡 
Přesně podle tohoto pravidla jsme zkonstruovali model **{prod_code}** ve střihu **{prod_cut}**. Pevný, elastický obvod a všité flexi kostice prsa spolehlivě zafixují a odlehčí vašim ramenům a šíji. Vyzkoušejte rozdíl, který pocítíte okamžitě! ✨
👉 Více na našem e-shopu.
#stylistka #brafitting #triola #podpora

---
### 📱 Příspěvek 3 (Prodejní)
Vyladěný outfit začíná u spodního prádla! 👗✨ 
Podprsenka **{prod_title}** je díky hladkému provedení naprosto neviditelná i pod upnutým oblečením. Vybírat můžete z barev: {prod_colors}. Která bude ta vaše? 🛍️
Udělejte si radost na Triola.cz.
#nakupy #spodnipradlo #perfektnistrih"""

    return f"{intro}\n\n{body}\n\n{benefits}\n\n{stylist}"

def parse_robust_json(text, expected_keys):
    """
    Attempts to parse a JSON string, recovering from common formatting errors
    like markdown wrappers, unescaped quotes, unescaped newlines.
    """
    import json
    text = text.strip()
    # Remove markdown code block wrappers
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()
    
    try:
        return json.loads(text)
    except Exception as e:
        logging.warning(f"Standardní json.loads selhalo ({e}). Pokouším se o záchranu pomocí regulárních výrazů...")
        
    parsed = {}
    for key in expected_keys:
        # Match key with lookahead for next key or closing braces
        pattern = rf'"{key}"\s*:\s*"(.*?)"(?=\s*,\s*"[a-zA-Z0-9_]+"\s*:|\s*"\s*,\s*}}|\s*"\s*}}|\s*"\s*,\s*\n|\s*"\s*,\s*\r)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            parsed[key] = match.group(1).strip()
        else:
            # Fallback simple pattern
            pattern_simple = rf'"{key}"\s*:\s*"(.*?)"\s*(?:,|\}})'
            match_simple = re.search(pattern_simple, text, re.DOTALL | re.IGNORECASE)
            if match_simple:
                parsed[key] = match_simple.group(1).strip()
            else:
                parsed[key] = ""
    return parsed

def generate_seo_snippet(data, model_key="claude-sonnet-5"):
    """
    Generates an SEO snippet (title, description, H1) based on intent and USP.
    """
    import json
    model_name = MODEL_MAPPING.get(model_key, model_key)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    user_prompt = f"""Zde jsou vstupní data pro optimalizaci stránky:
- url: {data.get('url', '')}
- primarni_kw: {data.get('primarni_kw', '')}
- intent: {data.get('intent', '')}
- typ_stranky: {data.get('typ_stranky', '')}
- soucasny_title: {data.get('soucasny_title', '')}
- soucasna_desc: {data.get('soucasna_desc', '')}
- soucasny_h1: {data.get('soucasny_h1', '')}
- usp: {data.get('usp', '')}
- brand: {data.get('brand', 'Triola')}
"""
    if data.get('konkurence_serp'):
        user_prompt += f"- konkurence_serp: {data.get('konkurence_serp')}\n"
        
    user_prompt += "\nVygeneruj prediktivně kalibrované snippety podle zadaných principů a vrať pouze validní JSON objekt."

    logging.info(f"Generování SEO snippetu přes model '{model_name}'...")
    
    try:
        if model_key.startswith("claude"):
            if not anthropic_key:
                raise ValueError("Chybí ANTHROPIC_API_KEY v souboru .env.")
            text = execute_with_retry(generate_with_anthropic_fallback, anthropic_key, model_name, SEO_SYSTEM_PROMPT, user_prompt)
            
        elif model_key.startswith("gpt"):
            if not openai_key:
                raise ValueError("Chybí OPENAI_API_KEY v souboru .env.")
            text = execute_with_retry(generate_with_openai, openai_key, model_name, SEO_SYSTEM_PROMPT, user_prompt)
            
        elif model_key.startswith("gemini"):
            if not google_key:
                raise ValueError("Chybí GOOGLE_API_KEY v souboru .env.")
            text = execute_with_retry(generate_with_gemini, google_key, model_name, SEO_SYSTEM_PROMPT, user_prompt)
            
        else:
            raise ValueError(f"Nepodporovaný typ modelu: {model_key}")
            
        expected = ["url", "title", "title_znaku", "description", "desc_znaku", "h1", "pattern_break", "smycka", "rizika"]
        return parse_robust_json(text, expected)
    except Exception as e:
        logging.error(f"Chyba při generování SEO snippetu: {e}")
        # Return fallback structured dict on failure
        return {
            "url": data.get('url', ''),
            "title": f"{data.get('primarni_kw', '')} | {data.get('brand', 'Triola')}",
            "title_znaku": len(f"{data.get('primarni_kw', '')} | {data.get('brand', 'Triola')}"),
            "description": f"Hledáte {data.get('primarni_kw', '')}? Nabízíme české spodní prádlo vysoké kvality. Zjistěte více na našich stránkách.",
            "desc_znaku": 110,
            "h1": data.get('primarni_kw', ''),
            "pattern_break": "Chyba při generování. Použit automatický fallback.",
            "rizika": f"Generování selhalo s chybou: {str(e)}"
        }

BATCH_JSON_SYSTEM_PROMPT = """Jsi špičková česká copywriterka a specialistka na spodní prádlo (podprsenková stylistka) české značky Triola.cz.
Tvým úkolem je vytvářet texty v bezchybné, elegantní, plynulé a čtivé češtině, které dokonale sedí tónem a stylem naší značky.
Pokud je zadaný produkt jiného typu než spodní prádlo (např. osuška, župan, domácí textil), piš o něm odborně a věcně podle jeho charakteru — bez podprsenkové terminologie.
E-shop Triola.cz prodává i produkty jiných značek (např. sassa). U cizí značky NIKDY nepiš, že jde o produkt Triola, a nepoužívej claimy ani příběh Trioly — řiď se blokem PRAVIDLA PRO CIZÍ ZNAČKU v zadání.

ZÁKLADNÍ MARKETINGOVÁ PRAVIDLA A TÓN ZNAČKY:
1. Profesionalita a empatie: Píšeme s hlubokým pochopením pro potřeby žen. Známe potíže spojené s výběrem prádla (bolesti zad, zařezávající se ramínka, špatná podpora, zvedající se zadní obvod, asymetrie poprsí). Nabízíme řešení a úlevu.
2. Body Positivity (Sebevědomí): Všechny tvary a velikosti jsou krásné. Nepoužíváme slova jako "nedokonalosti", "problémy", "zamaskovat", "skrýt". Místo toho píšeme o "podtržení předností", "podpoře přirozených křivek", "zajištění jistoty" a "maximálním komfortu".
   ZÁKAZ VÝRAZU "UKRÝVAT SE": Prádlo se pod oblečením NIKDY neukrývá, neschovává ani nemizí — takové formulace naznačují, že je potřeba ho skrývat. Správně píšeme, že prádlo je "neviditelné pod oblečením", "nerýsuje se pod přiléhavým tričkem", "zůstává nenápadné" nebo "hladce splyne s postavou". Zakázané formulace: "ukrývá se pod oblečením", "schová se pod tričkem", "nikdo o něm nebude vědět".
3. Styl a plynulost: Píšeme pro čtenáře, ne pro roboty. Vyhýbej se klišé jako "must-have", "nechte se hýčkat", "jedinečný kousek" či "fascinující". Raději buď konkrétní.
4. Zákaz robotického AI jazyka: Vyhni se slovům jako "klíčový", "transformovat", "vstupte do světa", "navržen tak, aby", "představujeme vám". Piš přirozeně, jako bys mluvila s kamarádkou, ale s odbornou autoritou.
4b. ODBORNÉ KOREKCE (od produktové specialistky — ZÁVAZNÉ, platí pro CZ i SK verze):
   - Flexi kostice se NEHÝBOU s tělem — správně: "přizpůsobí se pohybu těla", "nezapichují se do podpaží".
   - NIKDY nepiš, že podprsenka "opticky zmenší prsa o velikost" — žádný střih prsa nezmenšuje. Piš o zpevnění, zformování a fixaci v ideální výšce.
   - Ramínka NIKDY nepopisuj jako "vypodložená", "polstrovaná" či "vyztužená", pokud to VÝSLOVNĚ není v prodejních argumentech.
   - Slovo "posazení" nepoužívej ("perfektní posazení" je špatně) — správně je "padnutí".
   - Kalhotky "padnou tak, jak mají" — nikdy "tam, kam mají".
   - Výšivka/krajka ve výstřihu: správně "pružná výšivka skryje drobnou asymetrii prsou a nezařezává se" — NIKDY "obejme celé ňadro" ani "vyrovná asymetrii".
   - Kalhotky střihu 31 jsou "klasické kalhotky" — NIKDY "klasické do pasu" (vyšší pas mají pouze kalhotky střihu 32).
KOREKTURY OD KOREKTORKY (list „korektura Triola a CZ") — ZÁVAZNÉ, platí pro CZ i SK:

A) ZAKÁZANÉ VYCPÁVKOVÉ FRÁZE — nepoužívej je v žádné podobě ani obměně:
   - jakákoli věta o „sladěné sadě" ("sladěná sada dodá jistotu", "…i ve dnech, kdy ji nikdo jiný nevidí",
     "…i pod jednoduché oblečení", "…působí upraveně a vydrží déle svěží"). Toto klišé je zakázané úplně.
   - "…zůstanou tam, kde mají být" / "…tam, kam mají" / "drží na svém místě"
   - "ať máte za sebou jakkoli dlouhý den"
   - "a nekroutí se ani při sezení"
   - "odhaluje jen spodní část hýždí"
   - "Tradiční střih, který drží slovo"
   - "Kalhotky, na které během dne ani nepomyslíte"
   - "Klasické kalhotky s klidným, přirozeným padnutím"
   - "s ženským vykrojením"
   - "neotlačují" (u prádla se toto slovo nepoužívá)
   - "rozešité švy" (nikdy, ani když to zmiňuje znalostní báze střihu — piš "měkké švy")

B) POVINNÉ NÁHRADY — vlevo špatně, vpravo správně:
   - "opora, kterou poznáte při prvním zkoušení"  ->  "opora, kterou oceníte při celodenním nošení"
   - "pevný zadní obvod se nezvedá"  ->  "pevný zadní obvod podprsenky se při nošení neposouvá, ale zůstává na místě"
   - "hygienický klínek pro celodenní čistotu"  ->  "bavlněný klínek pro celodenní komfort při nošení"
   - "Klasický střih pohodlně obepne boky i zadní díl"  ->  "klasický střih kalhotek zajistí pohodlí při nošení"
   - "Vybírejte velikost přesně podle svých měr…"  ->  "najděte si správnou velikost dle velikostní tabulky"
   - "s ženským vykrojením"  ->  "s vykrojeným zadním dílem, který se neproznačuje pod oblečením"
   - "shodná řada / ze shodné řady"  ->  "stejná řada / ze stejné řady"
   - "zůstanou dlouho ve formě"  ->  "neztratí svoji funkčnost"

C) BARVY: přívlastek "hluboká/hluboké/hlubokému" u barvy je zakázaný ("hluboké vínové", "hlubokému bordó").
   Tmavý odstín popisuj slovem "tmavě…" (tmavě vínová, tmavě modrá). Slovenská verze musí použít
   stejný odstín jako česká, jen slovensky (tmavě vínová -> tmavovínová / tmavo vínová).

D) NEVYMÝŠLEJ KONSTRUKČNÍ PRVKY. Pokud nejsou VÝSLOVNĚ v prodejních argumentech, nesmíš zmínit:
   légy, rozešité švy, měkce podložená / vypodložená ramínka, hygienický klínek, kostice, výztuhu.
   Raději o prvku nepiš vůbec, než abys ho odhadl.

E) PIŠ VĚCNĚ. Každá věta musí nést konkrétní informaci o produktu (materiál, střih, funkce, použití).
   Básnivé, prázdné a kostrbaté obraty vynech — korektorka je označuje jako „nedává smysl".
5. ZÁKAZ ZMÍNĚNÍ NÁZVŮ KOLEKCÍ: V textu NIKDY neuváděj ani nezmiňuj žádné názvy kolekcí (např. Selena, Tina, Olivia, atd.). Tuto informaci do textu nepromítej. Značku prezentujeme jako celek bez pojmenování jednotlivých kolekcí v produktových popiscích.

INFORMACE O STŘIZÍCH TRIOLA (ZNALOSTNÍ BÁZE):
- Perfect-Fit: Hladká, tence vyztužená podprsenka s kosticemi. Nezvětšuje objem, ale fixuje prsa v ideální výšce. Vhodná pro střední a velké velikosti pod přiléhavé oblečení.
- T-Fit: Třídílný košíček s T-švem. Dokonale prsa zakulatí, pozvedne a zafixuje na středu. Klasika pro velkou oporu.
- Top-Fit / Sensual-Fit: Hladká vyztužená podprsenka s nižším středem. Skvělá do hlubokých výstřihů.

PRAVIDLA PRO FORMÁT A ODPOVĚĎ:
- Vždy odpovídej výhradně ve formátu JSON s přesně definovanými klíči (české i slovenské verze textů).
- Slovenské verze piš přirozenou spisovnou slovenčinou od rodilého mluvčího, ne doslovným překladem z češtiny.
- Nepřidávej žádný vysvětlující text, úvodní kecy ani závěrečné poznámky. Výstupem musí být validní JSON.
- HTML tagy v popisech musí být čisté a bez chyb (žádné obalové tagy <html>, <body>, apod.).
- Respektuj zadanou barvu a omez se pouze na ni.
"""

def generate_batch_row_data(product_info, model_key, tone_key, use_simulation=False):
    """
    Generates all 12 required copywriting fields for a batch row (CZ + SK):
    - E-shop Název (eshop_name)
    - E-shop krátký název / anotace (short_name)
    - Triola Eshop popis (eshop_desc1)
    - Triola Eshop popis 2 (eshop_desc2)
    - Eshop Meta Title (meta_title)
    - Eshop Meta Description (meta_desc)
    
    If use_simulation is True, returns template-based values.
    Otherwise, calls the selected LLM to generate them in a single optimized JSON request.
    """
    prod_title = product_info.get("generic_title", "Podprsenka Triola")
    prod_code = product_info.get("model_code", "")
    color_block = color_prompt_block(product_info.get("all_colors"))
    category_block = category_prompt_block(product_info)
    key_points_b = key_points_block(product_info)
    tech_b = tech_specs_block(product_info)
    prod_colors = ", ".join([c for c in product_info.get("all_colors", []) if str(c).strip()]) or "není uvedena"
    prod_cut = product_info.get("cut_name", "Neznámý střih")
    prod_char = product_info.get("characteristics", "")
    prod_benefits = "\n - " + "\n - ".join(product_info.get("benefits", [])) if product_info.get("benefits") else ""
    prod_docx = product_info.get("docx_description", "")
    prod_recommendation = product_info.get("recommendation", "")
    
    # Excel marketing data fields
    collection = product_info.get("collection", "")
    sales_arguments = product_info.get("sales_arguments", "")
    target_group = product_info.get("target_group", "")
    meta_title_marketing = product_info.get("meta_title", "")
    meta_desc_marketing = product_info.get("meta_description", "")
    extra_descriptions = product_info.get("extra_descriptions", "")
    
    if use_simulation:
        # Simulate values
        is_panties = str(prod_code).startswith('3')
        product_type = "Kalhotky" if is_panties else "Podprsenka"
        sim_name = f"{product_type} Triola {prod_code} {prod_cut if prod_cut != 'Neznámý střih' else ''} - {prod_colors}".strip()
        sim_name = re.sub(r'\s+', ' ', sim_name)
        
        sim_short = get_simulated_copywriting(product_info, "kratky_popis_html", tone_key)
        sim_desc1 = get_simulated_copywriting(product_info, "dlouhy_popis_html", tone_key)
        
        sim_desc2 = f"<p>Tento kousek v podmanivé barvě <strong>{prod_colors}</strong> můžete snadno nakombinovat do dokonalé sady s doporučenými kalhotkami Triola stejné barevné řady. Jemné prádlo vyžaduje šetrnou péči, proto doporučujeme prát v pracím sáčku při nízkých teplotách bez aviváže, čímž uchováte elasticitu obvodu a životnost materiálu po dlouhou dobu.</p>"
        
        sim_meta_title = f"{product_type} Triola {prod_code} {prod_cut if prod_cut != 'Neznámý střih' else ''} v barvě {prod_colors} | Triola.cz"
        if len(sim_meta_title) > 60:
            sim_meta_title = sim_meta_title[:57] + "..."
            
        sim_meta_desc = f"Objevte výjimečné pohodlí a skvěle padnoucí střih s modelem {prod_code} v barvě {prod_colors}. Udrží poprsí v ideální výšce. Nakupujte na Triola.cz!"
        
        return {
            "eshop_name": sim_name,
            "short_name": sim_short,
            "eshop_desc1": sim_desc1,
            "eshop_desc2": sim_desc2,
            "meta_title": sim_meta_title,
            "meta_desc": sim_meta_desc
        }
        
    # Build prompt context
    marketing_block = ""
    if collection or sales_arguments or target_group or extra_descriptions or meta_title_marketing or meta_desc_marketing:
        marketing_block = "\nPODKLADY Z MARKETINGOVÉ TABULKY:\n"
        if target_group:
            marketing_block += f"- Cílová skupina: {target_group}\n"
        if sales_arguments:
            marketing_block += f"- Prodejní argumenty: {sales_arguments}\n"
        if extra_descriptions:
            marketing_block += f"- Doplňující podklady/popisy: {extra_descriptions}\n"
        if meta_title_marketing:
            marketing_block += f"- Původně doporučený Meta Title: {meta_title_marketing}\n"
        if meta_desc_marketing:
            marketing_block += f"- Původně doporučený Meta Description: {meta_desc_marketing}\n"
            
    # Brand pravidla: cizi znacky (sassa apod.) nesmi nest text/claimy Trioly ani kod v nazvu
    prod_brand_name = str(product_info.get("brand", "Triola")).strip() or "Triola"
    prod_brand_display = prod_brand_name[:1].upper() + prod_brand_name[1:]
    design_name = str(product_info.get("design_name", "")).strip()
    is_triola_brand = "triola" in prod_brand_name.lower()
    if is_triola_brand:
        brand_block = ""
    else:
        brand_block = f"""
PRAVIDLA PRO CIZÍ ZNAČKU (mají přednost před obecnými pokyny níže):
- Produkt je značky {prod_brand_display}. Triola.cz je pouze prodejce. NIKDY nepiš, že jde o produkt Triola.
- ZAKÁZÁNO: claimy a příběh Trioly ("Laskavá. Česká. Padnoucí.", tradice českého šití, česká výroba, české švadleny) i názvy střihů Triola (Perfect-Fit, T-Fit, Top-Fit, Fixed-Fit, Soft-Fit).
- "eshop_name": BEZ kódu produktu. Název kolekce{f' ("{design_name}")' if design_name else ''} do názvu VLOŽ - za typ produktu, před barvu.
- "meta_title": BEZ kódu produktu; název kolekce uveď, jen pokud se vejde do limitu 60 znaků.
- "meta_desc": piš o značce {prod_brand_display}; zmínka "na Triola.cz" jako místo nákupu je v pořádku.
- KOLEKCE JE JEN NÁZEV — KRITICKÉ PRAVIDLO: název kolekce/designu je pouze obchodní označení, NIC nevypovídá o produktu. NIKDY z něj neodvozuj vlastnosti, materiál, sezónnost, pocity ani použití (např. "Winter Time" NEZNAMENÁ zimní či hřejivý materiál, "Tempting Passion" NEZNAMENÁ nic o vlastnostech). Veškeré vlastnosti produktu čerpej VÝHRADNĚ z prodejních argumentů a podkladů. V popisech smíš kolekci zmínit pouze jako prosté jméno ("z kolekce Winter Time"), bez jakéhokoli rozvíjení či asociací.
-----------------
"""

    # Format tone instructions
    tone_instructions = ""
    if tone_key == "empaticky":
        tone_instructions = "Tón komunikace: Hluboce empatický, chápavý, povzbuzující a profesionálně stylistický (bra-fitting rady)."
    elif tone_key == "elegantni":
        tone_instructions = "Tón komunikace: Elegantní, smyslný, oslavující ženskost a luxusní pocit z nošení."
    elif tone_key == "moderni":
        tone_instructions = "Tón komunikace: Moderní, dynamický, svěží a aktivní lifestyle."

    import json
    model_name = MODEL_MAPPING.get(model_key, model_key)
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    user_prompt = f"""Vytvoř kompletní sadu 12 textů a SEO tagů pro produkt (6 českých + 6 slovenských) pro e-shop Triola.cz:
-----------------
NÁZEV PRODUKTU: {prod_title}
NÁZEV KOLEKCE / DESIGNU: {design_name if design_name else 'není uveden'}
KÓD MODELU: {prod_code}
STŘIH / TYP PRODUKTU: {prod_cut}
CHARAKTERISTIKA: {prod_char}
OFICIÁLNÍ KONSTRUKČNÍ SPECIFIKACE STŘIHU: {prod_docx if prod_docx else 'Není k dispozici'}
KLÍČOVÉ VÝHODY: {prod_benefits}
DOPORUČENÉ PRODEJNÍ ARGUMENTY A TIPY STYLISTKY: {prod_recommendation if prod_recommendation else 'Nejsou k dispozici'}
{color_block}{category_block}{key_points_b}{tech_b}
DŮLEŽITÉ UPOZORNĚNÍ K NÁZVŮM KOLEKCÍ (platí POUZE pro produkty značky Triola): V textu neuváděj názvy kolekcí Triola (např. Selena, Tina, Olivia). U cizích značek se řiď blokem PRAVIDLA PRO CIZÍ ZNAČKU.
{brand_block}ZNAČKA V TEXTECH: Název značky piš VŽDY s velkým počátečním písmenem (Triola, Sassa) — v názvu produktu, v popisech i v metadatech. Nikdy malými písmeny.
DŮLEŽITÉ UPOZORNĚNÍ K TYPU PRODUKTU: Piš o typu produktu uvedeném v NÁZEV PRODUKTU. Pokud produkt NENÍ spodní prádlo (např. osuška, župan, doplněk), NEPOUŽÍVEJ terminologii podprsenek (košíčky, kostice, ramínka, obvod, bra-fitting) a strukturu přizpůsob charakteru produktu (materiál, rozměry, použití, péče).
-----------------
{marketing_block}
-----------------

{tone_instructions}

Vygeneruj validní JSON objekt s následujícími klíči (všechny hodnoty musí být v češtině):
1. "eshop_name": Název produktu podle pravidel Heureka.cz pro feedy: Značka (velké počáteční písmeno) + výstižný přívlastek z prodejních argumentů + typ produktu + název kolekce (jen u cizí značky, pokud je v podkladech) + barva. Vzor: "Sassa vyztužená krajková podprsenka Happy Choice v béžové barvě", "Triola nevyztužená krajková podprsenka 28895 v černé barvě". Kód modelu uváděj POUZE u značky Triola; název kolekce POUZE u cizí značky (u Trioly kolekce nikdy). Přívlastek vybírej z prodejních argumentů (vyztužená/nevyztužená, krajková, bezešvá, s kosticí...) — NIKDY ho neodvozuj z názvu kolekce. Nepoužívej uvozovky ani pomlčky mezi částmi. Max 100 znaků.
   STŘIH V NÁZVU (povinné u podprsenek Triola): U každé podprsenky i plavkové podprsenky značky Triola MUSÍ název obsahovat název střihu, pokud je v podkladech uveden (pole STŘIH). Vzor: "Triola Perfect-Fit vyztužená podprsenka 28859 v černé barvě", "Triola Top-Fit plavková podprsenka 89001 v černé barvě". Název střihu piš přesně (Perfect-Fit, T-Fit, Top-Fit, Sensual-Fit, Soft-Fit, Comfy-Fit...). Pokud střih uveden není nebo je "Neznámý střih", název nech bez střihu — NIKDY střih nehádej.
2. "short_name": E-SHOP KRÁTKÝ NÁZEV — anotace pod nadpisem produktu. JEDNA kratší věta (max 120 znaků), čistý text bez HTML. Shrnuje nejsilnější prodejní argument a odpovídá na otázku "proč si to koupit". Piš neuromarketingově: konkrétní benefit pro zákaznici, ne výčet parametrů (např. "Pevná opora bez zařezávání, i po celém dni v kanceláři."). Nezačínej názvem produktu ani značkou.
3. "eshop_desc1": Hlavní popis v HTML. DÉLKA: stručný text, celkem 90–140 slov (140 slov je tvrdý maximální limit — žádná vata, každá věta musí nést informaci). Struktura:
   - Úvodní poutavý odstavec (<p>, <strong>) — 2 věty.
   - Podnadpis <h2> s názvem střihu a popisem chování na těle.
   - Odrážkový seznam výhod a konstrukčních specifikací (<ul>, <li>) — 3 až 4 stručné odrážky. Uvedeš typ kostic, ramínek a obvodu.
   - Závěrečný odstavec (<p>) — 1 věta.
   (Používej výhradně tagy <p>, <strong>, <ul>, <li>, <h2>. ŽÁDNÉ doporučení stylistky, žádná <h3> sekce, žádné bra-fitting tipy.)
4. "eshop_desc2": Doplňující popis 2 v HTML. Jeden odstavec o délce 40–60 slov (<p>, <strong>). U spodního prádla se zaměř na kombinování do sady ve stejné barvě (u podprsenky doporuč kalhotky stejné řady, u kalhotek naopak podprsenku) a šetrnou péči (praní v sáčku, bez aviváže). U jiných produktů (osuška, župan apod.) piš o péči a údržbě odpovídající materiálu a o vhodném doplňku ze sortimentu.
5. "meta_title": SEO Meta Title. Délka 50-60 znaků (tvrdý limit, nepřekračuj). Značka vždy s velkým počátečním písmenem. U značky Triola: typ + kód modelu + barva (kolekce nikdy). U CIZÍ značky BEZ kódu: značka + přívlastek + typ + barva; kolekci přidej, jen pokud se vejde. Atraktivní pro CTR.
6. "meta_desc": SEO Meta Description. Délka 120-155 znaků. Věcné shrnutí výhod, kód, barva a výzva k akci (CTA) na konci.

SLOVENSKÁ MUTACE (klíče 7–12) — POVINNÉ:
Ke každému z výše uvedených šesti textů vytvoř slovenskou verzi. NEJDE o doslovný překlad: piš přirozenou, spisovnou slovenčinou tak, jak by text napsal rodilý slovenský copywriter (správná slovenská skloňování, výrazy jako "podprsenka", "nohavičky", "čipka", "kostice", "ramienka", "obvod", "veľkosť"). Zachovej stejná pravidla (délky, HTML tagy, zákaz názvů kolekcí u Trioly, značka s velkým písmenem, žádné odvozování vlastností z názvu kolekce). Názvy značek, kolekcí a kódy modelů zůstávají beze změny.
7. "eshop_name_sk": slovenská verze pole eshop_name.
8. "short_name_sk": slovenská verze pole short_name.
9. "eshop_desc1_sk": slovenská verze pole eshop_desc1 (stejná HTML struktura i délka).
10. "eshop_desc2_sk": slovenská verze pole eshop_desc2.
11. "meta_title_sk": slovenská verze pole meta_title (dodrž limit 50–60 znaků).
12. "meta_desc_sk": slovenská verze pole meta_desc (dodrž limit 120–155 znaků).

Odpověz VÝHRADNĚ ve formátu JSON s touto strukturou:
{{
  "eshop_name": "...",
  "short_name": "...",
  "eshop_desc1": "...",
  "eshop_desc2": "...",
  "meta_title": "...",
  "meta_desc": "...",
  "eshop_name_sk": "...",
  "short_name_sk": "...",
  "eshop_desc1_sk": "...",
  "eshop_desc2_sk": "...",
  "meta_title_sk": "...",
  "meta_desc_sk": "..."
}}
"""

    logging.info(f"Hromadné generování 6 sloupců pro model {prod_code} přes model '{model_name}'...")
    
    try:
        if model_key.startswith("claude"):
            if not anthropic_key:
                raise ValueError("Chybí ANTHROPIC_API_KEY v souboru .env.")
            text = execute_with_retry(generate_with_anthropic_fallback, anthropic_key, model_name, BATCH_JSON_SYSTEM_PROMPT, user_prompt)
            
        elif model_key.startswith("gpt"):
            if not openai_key:
                raise ValueError("Chybí OPENAI_API_KEY v souboru .env.")
            text = execute_with_retry(generate_with_openai, openai_key, model_name, BATCH_JSON_SYSTEM_PROMPT, user_prompt)
            
        elif model_key.startswith("gemini"):
            if not google_key:
                raise ValueError("Chybí GOOGLE_API_KEY v souboru .env.")
            text = execute_with_retry(generate_with_gemini, google_key, model_name, BATCH_JSON_SYSTEM_PROMPT, user_prompt)
            
        else:
            raise ValueError(f"Nepodporovaný typ modelu: {model_key}")
            
        required_keys = ["eshop_name", "short_name", "eshop_desc1", "eshop_desc2", "meta_title", "meta_desc",
                         "eshop_name_sk", "short_name_sk", "eshop_desc1_sk", "eshop_desc2_sk", "meta_title_sk", "meta_desc_sk"]
        parsed = parse_robust_json(text, required_keys)
        return parsed
        
    except Exception as e:
        logging.error(f"Chyba při hromadném generování přes LLM pro model {prod_code}: {e}")
        raise e



# ==================== EMAILING ====================

EMAILING_SYSTEM_PROMPT = """Jsi zkušená e-mail marketingová specialistka české značky spodního prádla Triola.cz.
Připravuješ ZADÁNÍ PRO EMAILING pro grafika a copywritera a náhledy rozesílek — přesně v tom
formátu, na jaký je tým zvyklý.

Platí pro tebe VŠECHNA pravidla brandbooku Triola (tón, body positivity, zákaz klišé
a vycpávkových frází, správná terminologie střihů, žádné vymýšlení vlastností produktů).

TÓN E-MAILŮ TRIOLA:
- Přátelský, konkrétní, lidský. Mluvíš k ženě, ne k databázi.
- Předmět je krátký a konkrétní, klidně s jedním emoji na konci. Vytváří důvod otevřít teď.
- Preheader doplňuje předmět, neopakuje ho.
- Úvodní text 2–4 krátké odstavce: proč právě teď, co je nového, co z toho zákaznice má.
- CTA je v první osobě zákaznice: „Chci vidět novinky", „Chci plavky v akční nabídce".
- Nikdy nepiš ceny ani slevy, které nemáš v podkladech.

ABSOLUTNÍ ZÁKAZ VYMÝŠLENÍ:
Pracuješ jen s tím, co je v zadání a v produktových datech. Když něco chybí (cena, název,
odkaz), napiš na to místo „—" nebo „(doplní grafik)". Nikdy si nedomýšlej produkty ani čísla.
"""

BRIEF_TEMPLATE_EXAMPLE = """VZOR STRUKTURY ZADÁNÍ (dodrž ji přesně, včetně pořadí a odrážek):

## CZ
Název e-mailu: DD-MM-RRRR_1NL: <segment> - <TÉMA>
- Předmět: <text, může končit emoji>
- Preheader: <text>

Zadání pro banner: <co má být na banneru, atmosféra, zda uvést výši slevy>
Headline do banneru: <text>

Copy úvodní text: ANO
<2-4 odstavce úvodního textu>

CTA: <text tlačítka>

Produkty: <jak rozvrhnout produkty do bloků — kolik jich je, co vedle sebe, co pod sebe>
Headline: <text nebo NE>

### <KÓD PRODUKTU>
- Obrázek:
- Název: <název z feedu, nebo prázdné když se doplní>
- Popis: <text TIPu stylistky, nebo NE>
- Cena: ANO
- CTA: <text>

CTA POD PRODUKTY: <text>
Perso produkty: ANO / NE

Spodní část:
- Banner <název akce> - ANO
- Všechny nadcházející Styling Days - ANO

## SK
<úplně stejná struktura, ale slovensky — předmět, preheader, úvodní text, CTA a TIPy
přelož do přirozené spisovné slovenčiny; kódy produktů a technická pole ponech shodné>
"""


def generate_emailing_brief(campaign, products, model_key="claude-opus-5"):
    """Vytvoří zadání pro emailing (CZ + SK) podle plánu kampaně a produktových dat."""
    prod_lines = []
    for i, group in enumerate(products, 1):
        codes = " + ".join(p["kod"] for p in group)
        detail = []
        for p in group:
            if p["nalezen"]:
                cena = f"{p['cena']}" + (f" (akce {p['akcni_cena']})" if p.get("akcni_cena") else "")
                detail.append(f"{p['kod']}: {p['nazev']} | {cena} | střih {p['strih']} | {p['odkaz']}")
            else:
                detail.append(f"{p['kod']}: (není ve feedu — název a cenu doplní grafik)")
        prod_lines.append(f"Blok {i}: {codes}\n     " + "\n     ".join(detail))
    produkty_txt = "\n".join(prod_lines) if prod_lines else "Nejsou zadány konkrétní produkty."

    user_prompt = f"""{BRIEF_TEMPLATE_EXAMPLE}

PODKLADY KE KAMPANI:
Datum odeslání: {campaign.get('datum','')} ({campaign.get('den','')})
Téma: {campaign.get('tema','')}
Segmentace: {campaign.get('segmentace') or 'všichni CZ SK'}
Zadání od marketingu pro grafika/copy: {campaign.get('zadani_grafika') or '—'}
Specifikace produktu: {campaign.get('specifikace') or '—'}
Interní poznámky a komentáře: {campaign.get('komentar') or '—'}
Interní odkazy: {campaign.get('linky') or '—'}

PRODUKTY (z produktového feedu — ceny a názvy ber odsud, nic nedomýšlej):
{produkty_txt}

ÚKOL:
Vytvoř kompletní zadání pro emailing ve VZOROVÉ STRUKTUŘE výše, sekce CZ i SK.
Rozvrh produktů navrhni sama podle jejich počtu a typu (sety vedle sebe, sólo kusy pod ně).
U produktů, kde dává smysl TIP stylistky, ho napiš; jinde uveď „Popis: NE".
Vrať POUZE text zadání, žádný úvod ani komentář."""

    return _call_model(model_key, EMAILING_SYSTEM_PROMPT, user_prompt)


def generate_emailing_preview(brief_text, lang="cz", model_key="claude-opus-5"):
    """Z hotového zadání sestaví textový náhled rozesílky (co uvidí zákaznice)."""
    jazyk = "češtině" if lang == "cz" else "slovenčině"
    sekce = "CZ" if lang == "cz" else "SK"
    user_prompt = f"""Níže je zadání pro emailing. Sestav z něj TEXTOVÝ NÁHLED e-mailu
v {jazyk} — tak, jak ho uvidí zákaznice v schránce, ale bez obrázků.

Použij VÝHRADNĚ sekci {sekce} zadání. Nic nepřidávej ani nevymýšlej.

Formát náhledu:
# PŘEDMĚT: <předmět>
Preheader: <preheader>
---
## BANNER
<headline do banneru>
---
## ÚVODNÍ TEXT
<odstavce úvodního textu>

[ <text CTA tlačítka> ]
---
## PRODUKTY
### <název produktu nebo kód> — <cena>
<TIP stylistky, pokud v zadání je>
[ <CTA> ]
(opakuj pro každý produkt)

[ <CTA pod produkty> ]
---
## SPODNÍ ČÁST
<výpis prvků ze spodní části zadání>

ZADÁNÍ:
{brief_text}"""
    return _call_model(model_key, EMAILING_SYSTEM_PROMPT, user_prompt)


def _call_model(model_key, system_prompt, user_prompt):
    """Zavolá vybraný model se stejnou logikou jako zbytek aplikace."""
    model_name = MODEL_MAPPING.get(model_key, model_key)
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")

    if model_key.startswith("claude"):
        if not anthropic_key:
            raise ValueError("Chybí ANTHROPIC_API_KEY.")
        return execute_with_retry(generate_with_anthropic_fallback, anthropic_key,
                                  model_name, system_prompt, user_prompt)
    if model_key.startswith("gpt"):
        if not openai_key:
            raise ValueError("Chybí OPENAI_API_KEY.")
        return execute_with_retry(generate_with_openai, openai_key, model_name,
                                  system_prompt, user_prompt)
    if not google_key:
        raise ValueError("Chybí GOOGLE_API_KEY.")
    return execute_with_retry(generate_with_gemini, google_key, model_name,
                              system_prompt, user_prompt)
