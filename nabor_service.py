# -*- coding: utf-8 -*-
"""
Nábor — znalostní báze pro generování pracovních inzerátů Trioly.

Obsahuje tři věci, které generátor potřebuje a které se nedají odvodit z brandbooku:
  1. Zaměstnavatelské argumenty Trioly (proč u nás pracovat).
  2. Best practices pro inzerci prodejních pozic (rešerše 09/2026, zdroje níže).
  3. Pravidla genderově neutrálního psaní — v ČR je jednorodý inzerát pokutovatelný.

Zdroje k bodu 2 a 3:
  - Alma Career (provozovatel Prace.cz a Jobs.cz): jak psát pozici z hlediska genderu
    https://magazin.almacareer.com/cz/prodavac-prodavac-ka-prodavac-ka-nebo-prodavajici-
    jak-spravne-napsat-pozici-a-inzerat-z-hlediska-genderu
  - Hospodářské noviny: pokuta 75 000 Kč za inzerát „prodavačku … ve věku 25–35 let"
  - Fakturoid, Podnikatel.cz: průvodce pracovním inzerátem
  - EU směrnice o transparentnosti odměňování — implementace do 7. 6. 2026,
    většina povinností v ČR až od 1. 1. 2027; povinnost uvádět mzdu přímo v inzerátu
    MPSV z novely vyškrtlo. Uvádění mzdy tedy NENÍ povinné, ale zvyšuje prokliky.
"""

# --------------------------------------------------------------- pozice

# Zatím řešíme jen prodejny. Až bude potřeba jiná pozice, přidá se sem.
POZICE_VYCHOZI = "Prodejní asistent/ka"

# Prodejny dohledané na webu a v inzerátu — slouží jen jako našeptávač ve formuláři,
# pole je volně editovatelné. Před použitím ověřte, seznam se může měnit.
PRODEJNY_NAPOVEDA = [
    "Olomouc — OC Šantovka",
    "Praha — OC Černý Most",
    "Praha 5 — Řevnická (podniková prodejna)",
    "Brno — Jánská",
    "Ostrava — OC Avion",
    "Ostrava — OC Nová Karolina",
    "Plzeň",
    "Liberec",
    "Pardubice",
    "České Budějovice",
    "Jindřichův Hradec",
    "Frýdek-Místek",
]

# --------------------------------------------------------------- zaměstnavatelská značka

ZAMESTNAVATEL = """
KDO JE TRIOLA JAKO ZAMĚSTNAVATEL (fakta, ze kterých se smí psát):
- Česká značka s vlastní výrobou, přes 100 let na trhu. Ne řetězec, ne franšíza.
- Vyrábí spodní prádlo a plavky, k tomu distribuuje další značky. Vlastní síť prodejen
  a rostoucí e-shop.
- Na prodejnách se dělá bra-fitting: zákaznici se změří a vybere správná velikost.
  Košíčky až do velikosti L — tedy rozsah, který běžné obchody nemají.
  Tohle je jádro práce: ne „hlídat zboží", ale pomoct ženě najít prádlo, které sedí.
- Zaměstnanci procházejí pravidelným školením na střihy a materiály. Prodejní asistentka
  po zaškolení pozná, který střih komu sedí — je to odbornost, ne brigáda u pokladny.
- Styling Days: akce na prodejnách, kde se zákaznicím osobně měří velikost.

BENEFITY (uváděj jen ty, které jsou v podkladech k dané prodejně):
Provize z prodeje · bonusy a prémie · stravenky nebo příspěvek na stravování ·
zaměstnanecké slevy na zboží · 5 týdnů dovolené · školení a vzdělávací kurzy ·
příspěvek na pracovní oblečení
"""

# --------------------------------------------------------------- best practices

BEST_PRACTICES = """
JAK PSÁT PRACOVNÍ INZERÁT (rešerše 09/2026):

1. INZERÁT JE PRODEJNÍ TEXT. Produktem je práce, kandidátka je zákaznice.
   Neptej se jen „koho chceme", ale „proč by to u nás chtěla dělat".

2. TITULEK NESE INFORMACI. Ne „Asistentka prodeje", ale pozice + místo + mzda:
   „Prodejní asistent/ka — Triola, OC Šantovka Olomouc, 28–37 000 Kč".
   Uchazečka hned ví, na čem je, a nemusí rozklikávat.

3. MZDU UVÁDĚJ. Povinné to zatím není (ČR povinnost uvádět mzdu v inzerátu z novely
   vyškrtla, většina pravidel platí až od 1. 1. 2027), ale inzeráty bez mzdy nebo
   s „odměna dohodou" mají výrazně nižší prokliky.

4. POPIŠ SKUTEČNÝ DEN. Konkrétní práce místo abstrakcí: co dělá ráno, s kým mluví,
   jak vypadá bra-fitting, kolik lidí projde prodejnou. Tohle uchazečku nechá
   porovnat se sebou.

5. KRAŤ SEZNAM POŽADAVKŮ. Ženy se hlásí, když splňují většinu požadavků; muži už
   při 60 %. Dlouhý seznam odradí vhodné kandidátky. Nech jen to, co je skutečně
   nezbytné, zbytek se dořeší na pohovoru.
   Zkušenost s prádlem NENÍ podmínka — Triola školí. Piš to nahlas.

6. NEPIŠ POŽADAVKY NA POVAHU MÍSTO NA PRÁCI. „Veselou náladu", „příjemné vystupování"
   a „kladný vztah ke komunikaci" nic neměří a působí jako fráze. Přepiš je na
   chování: „bavilo vás mluvit s lidmi a poradit jim i tehdy, když si nejsou jistí".

7. KONKRÉTNÍ CTA A SLIB ODPOVĚDI. Napiš, co se stane po odeslání a do kdy se ozvete.
   A pak to dodržte — každému kandidátovi se ozvěte, i když nevyšel.

8. DÉLKA. Inzerát na portál 250–400 slov. Delší text lidé nedočtou.
"""

# --------------------------------------------------------------- gender

GENDER_PRAVIDLA = """
GENDEROVĚ NEUTRÁLNÍ PSANÍ — ZÁVAZNÉ, JDE O PRÁVNÍ RIZIKO:

V ČR nesmí inzerát vylučovat jedno pohlaví. Antidiskriminační zákon to zakazuje,
inspektorát práce za to pokutuje (zveřejněný případ: 75 000 Kč za inzerát hledající
„prodavačku … ve věku 25 až 35 let"; pokutované byly i „usměvavé servírky").
Pokuta může jít až do 1 milionu Kč. Platí to pro NÁZEV POZICE I CELÝ TEXT.

A) NÁZEV POZICE — používej obourodý nebo neutrální tvar:
   SPRÁVNĚ: „Prodejní asistent/ka", „Prodavač/ka", „Posila do prodejny"
   ŠPATNĚ:  „Prodejní asistentka", „Asistentka prodeje", „Prodavačka"

B) CELÝ TEXT V OBOU RODECH nebo neutrálně. Nikdy nepiš jen ženský rod.
   ŠPATNĚ: „hledáme usměvavou a komunikativní asistentku prodeje"
   SPRÁVNĚ: „hledáme kolegu nebo kolegyni na prodejnu"
   Místo „budete prodávat" (bez rodu) raději než „budeš prodávala".
   Oslovení „vy" v přítomném čase se rodu vyhne úplně — používej ho.

C) ZAKÁZANÉ POŽADAVKY, které se čtou jako kód na pohlaví nebo věk:
   - vzhled: „reprezentativní vystupování", „upravený zevnějšek", „hezká"
   - povaha kódovaná žensky: „milé vystupování", „usměvavá", „empatická", „pečlivá"
   - povaha kódovaná mužsky: „dravý", „akční", „odhodlaný"
   - věk: „mladý kolektiv", „do 35 let", „student/ka", „čerstvý absolvent"
   - rodina a zdraví: „bez závazků", „plně flexibilní", „fyzicky zdatný"
   Vlastnosti nahrazuj popisem činnosti: ne „empatická", ale „vyslechnete, co
   zákaznice potřebuje, a podle toho vyberete velikost".

D) VÝJIMKA existuje jen tam, kde druhé pohlaví práci vykonávat nemůže
   (herečka, modelka pro řadu podprsenek). Prodejní asistent/ka mezi ně NEPATŘÍ.

E) Na konci textu uveď, že nabídka platí pro muže i ženy.
"""

# --------------------------------------------------------------- co nepoužívat

STAVAJICI_INZERAT_CHYBY = """
CO BYLO ŠPATNĚ NA PŘEDCHOZÍM INZERÁTU TRIOLY (neopakuj to):
- „Aktuálně hledáme usměvavou a komunikativní asistentku prodeje" — jednorodé
  a požadavek na povahu; přesně formulace, za jaké padaly pokuty.
- „kladný vztah ke komunikaci se zákazníkem" — úřední, nic neříká.
- „veselou náladu a příjemné vystupování" — nejde ověřit ani změřit.
- „pozitivní vztah ke spodnímu prádlu a módním trendům" — vyprázdněná fráze.
- „flexibilitu" — bez upřesnění zní jako skrytý požadavek na neomezenou dostupnost.
- „odpovídající ohodnocení" — mzda byla jen v hlavičce portálu, ne v textu.
- O bra-fittingu, školení ani o tom, co je na práci zajímavého, nebylo ani slovo.
  Přitom je to nejsilnější argument, který Triola má.
"""

# --------------------------------------------------------------- kontrola rizik

RIZIKOVE_VYRAZY = [
    # jednorodé tvary
    "asistentku", "asistentka", "prodavačku", "prodavačka", "kolegyni hledáme",
    "slečnu", "paní na prodejnu",
    # požadavky na vzhled a povahu
    "reprezentativní", "upravený zevnějšek", "upravená", "usměvavou", "usměvavá",
    "milé vystupování", "příjemné vystupování", "empatická", "pečlivá", "veselou",
    "dravý", "akční typ", "odhodlaný",
    # věk
    "mladý kolektiv", "mladý tým", "do 35 let", "do 30 let", "čerstvý absolvent",
    "student", "mladá",
    # rodina, zdraví, původ
    "bez závazků", "fyzicky zdatný", "zdravotně způsobilý", "rodilý Čech",
    # vágní
    "odměna dohodou", "odpovídající ohodnocení", "mzda dle dohody",
]


def zkontroluj_rizika(text):
    """
    Projde hotový inzerát a vrátí seznam nalezených rizikových formulací.
    Slouží jako pojistka za generátorem — kdyby prompt selhal, chyba se ukáže v UI.
    """
    if not text:
        return []
    nizky = str(text).lower()
    nalezeno = []
    for vyraz in RIZIKOVE_VYRAZY:
        if vyraz.lower() in nizky and vyraz not in nalezeno:
            nalezeno.append(vyraz)
    return nalezeno


def podklady_block(inzerat_podklady):
    """Volitelné podklady od šéfa — vloží se do promptu, když jsou vyplněné."""
    text = str(inzerat_podklady or "").strip()
    if not text:
        return ('PODKLADY OD VEDENÍ: žádné nejsou. Vycházej z faktů o zaměstnavateli '
                'výše a nic si nedomýšlej — mzdu, termín nástupu ani benefity, které '
                'nemáš v zadání, neuváděj a nahraď je poznámkou "(doplní vedení)".')
    return f"PODKLADY OD VEDENÍ (mají přednost před vším ostatním):\n{text}"
