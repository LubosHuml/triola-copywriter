# -*- coding: utf-8 -*-
"""
Hlas rozesílek Trioly — vytažený z 24 skutečně odeslaných českých kampaní
(složka „Emailing / Rozesílky" na Google Disku, kampaně 07–09/2026).

Proč to tu je: dřív se model učil jen STRUKTURU zadání a o tónu měl jen abstraktní
pokyny („přátelský, konkrétní, lidský"). Výsledkem byly věcné, ale neosobní texty,
které mohl poslat jakýkoli e-shop. Tenhle soubor dodává skutečné vzory.

POZOR: vzory ukazují REGISTR A STAVBU, ne konkrétní slovní zásobu. Zákazy
z brandbooku (KOREKTURY_BLOCK v ai_service.py) mají VŽDY přednost — například
„hluboká bordó" se v jednom starém e-mailu vyskytuje, ale korektorka ho zakázala.
"""

# --- Předměty skutečně odeslaných kampaní -----------------------------------
PREDMETY = [
    "Bordó je nová černá. Osvěžte svůj šatník limitovanou edicí Vova 🍂",
    "Kousek, který si zamilujete 💕",
    "Tajemství dokonalého outfitu: Správný základ pod tričko",
    "Novinky SASSA: Láska na první pohled",
    "Vaše nejoblíbenější prádlo v nových barvách",
    "Limitovaná kolekce Dusty Rose je tady",
    "Novinky SUSA jsou tady",
    "Perfektně padnoucí kalhotky do 299 Kč",
    "Nejprodávanější plavky sezóny",
    "Čas na nové plavky",
    "Letní limitka inspirovaná exotikou",
    "Plavky pro všechny křivky nyní ve výprodeji",
    "Poslední šance ulovit plavky ve velkém výprodeji",
    "Slevy pro každou postavu",
    "Letní výprodej v Triole: Dopřejte si dokonalý střih za skvělé ceny",
    "Velký výprodej prádla: Kompletní set i pohodlné pyžamo",
]

# --- Celé úvodní texty jako vzor stavby a tónu -------------------------------
UVODNI_TEXTY = [
    # otázka ze společné zkušenosti
    """Znáte ten pocit, když si obléknete své oblíbené tričko, ale celkový dojem tak
trochu kazí prosvítající švy nebo nesprávná barva prádla? Dokonalý outfit totiž
nezačíná tím, co je vidět na první pohled. Začíná o vrstvu níž.
Naše stylistka pro vás sestavila rychlého průvodce světem našich triček. Podívejte se,
jak zkombinovat 4 trička různých barev s prádlem tak, abyste se celý den cítila
sebevědomě, pohodlně a naprosto božsky.""",

    """Milujete ten pocit, když je spodní prádlo tak pohodlné, že o něm po celý den ani
nevíte? Přesně taková je nová kolekce oblíbené značky Sassa. Ať už sáhnete po vyztužené
klasice s kosticí, nebo dáte přednost nevyztužené či bezkosticové podprsence, Sassa vás
nezklame. Doplňte je o skvěle padnoucí kalhotky a vytvořte si svůj nový oblíbený set.""",

    # obecná pravda o produktu
    """Některé kousky si oblíbíte na první obléknutí. Braletka je jedním z nich. Je lehká,
příjemná na nošení a díky jemným detailům i přirozeně ženská. Ať už si ji obléknete pod
košili, tričko nebo jen tak pro pohodový den doma, rychle se stane jedním z vašich
nejoblíbenějších kousků. Objevte kolekci značek Esotiq, Sloggi a Dorina a vyberte si
braletku, která bude sedět právě vám.""",

    # pozvání / dopřejte si
    """Dopřejte si pocit výjimečnosti každý den. Představujeme ikonickou sadu Triola 896
v limitované edici v novém odstínu Dusty Rose. Jemná pudrově růžová podtrhuje ženskost,
eleganci i přirozenou krásu.
Oblíbené střihy podprsenek krásně tvarují dekolt, poskytují spolehlivou oporu a zajišťují
celodenní pohodlí. Doplňte je kalhotkami do setu a vytvořte komplet, ve kterém se budete
cítit sebevědomě od rána do večera.""",

    # sezónní rámec
    """Předpověď na nejbližší týdny je jasná: slunce, voda a dny plné pohody. Pokud ještě
hledáte plavky, ve kterých se budete cítit skvěle, právě teď je ten správný čas.
Ve výprodeji najdete oblíbené střihy značek Triola, Esotiq i Dorina, které se přizpůsobí
vašim křivkám a dodají pocit sebevědomí pro všechny letní zážitky.""",

    # naléhavost u výprodeje
    """Poslední šance ulovit si dokonalé plavky za ty absolutně nejvýhodnější ceny sezóny!
Ať už nedáte dopustit na dvoudílné bikiny, nebo preferujete elegantní jednodílné plavky,
které krásně vytvarují siluetu, teď je ten správný čas si je pořídit.
Prohlédněte si poslední zlevněné kousky a skočte do zbytku léta v novém!""",

    # zajímavost / číslo jako hook
    """Víte, kolik plavek má průměrná žena v šatníku? Podle průzkumů jsou to minimálně troje.
A dává to dokonalý smysl! Plavek zkrátka není nikdy dost, protože každá letní aktivita
a každá žena si žádá své. Ať už nedáte dopustit na dvoudílnou klasiku, hledáte dokonale
padnoucí bikiny, nebo toužíte po jednodílných plavkách, které vykouzlí nádhernou siluetu,
mezi našimi nejprodávanějšími modely najdete ten svůj.""",

    # příběh značky
    """Věříte, že spodní prádlo by mělo být vaší druhou kůží? Měla byste o něm vědět jen vy
a místo kostic cítit jen celodenní pohodlí. Novinky legendární německé značky SUSA právě
dorazily do Trioly! SUSA se už přes 160 let specializuje na bezkosticové prádlo. Díky
promyšleným střihům a pevným materiálům spolehlivě unese a vytvaruje i plnější poprsí.""",
]

# --- CTA tlačítka ze skutečných kampaní --------------------------------------
CTA = [
    "Chci braletku", "Chci podprsenku SUSA", "Chci plavky v akční nabídce",
    "Chci vidět novinky Sassa", "Chci vidět novinky V.O.V.A.",
    "Objevit kolekci", "Objevit novinky", "Objevit celou nabídku",
    "Objevit akční nabídku", "Objevit více",
    "Vybrat braletku", "Vybrat si kalhotky", "Vybrat svůj střih",
    "Prozkoumat novinky", "Prohlédnout", "Pojďme na to!",
]


def hlas_block():
    """Sestaví blok s hlasem Trioly pro systémový prompt emailingu."""
    predmety = "\n".join(f'   - „{p}"' for p in PREDMETY)
    uvody = "\n\n".join(
        f"   PŘÍKLAD {i}:\n   " + t.strip().replace("\n", "\n   ")
        for i, t in enumerate(UVODNI_TEXTY, 1))
    ctas = ", ".join(f'„{c}"' for c in CTA)
    return f"""
HLAS ROZESÍLEK TRIOLY — NAUČENO ZE 24 SKUTEČNĚ ODESLANÝCH KAMPANÍ

Tohle je závazný vzor REGISTRU A STAVBY. Neopisuj z něj celé věty, ale piš ve stejném
tónu. Zákazy z korektur výše mají vždy přednost před formulacemi ve vzorech.

A) ÚVODNÍ TEXT MÁ VŽDY HÁČEK. Nikdy nezačínej oznámením typu „Právě jsme naskladnily
   nové kousky". Použij jeden z těchto pěti otevíráků, které Triola opravdu používá:
   1. Otázka ze společné zkušenosti — „Znáte ten pocit, když…?", „Milujete ten pocit,
      když…?", „Věříte, že…?"
   2. Pozvání — „Dopřejte si…"
   3. Obecná pravda o produktu — „Některé kousky si oblíbíte na první obléknutí."
   4. Sezónní nebo situační rámec — „Předpověď na nejbližší týdny je jasná: …",
      „Podzim se nezadržitelně blíží…"
   5. Číslo nebo zajímavost — „Víte, kolik plavek má průměrná žena v šatníku?"
   U výprodejů navíc naléhavost: „Poslední šance…", „Letní slevy jsou tu!"

B) STAVBA ÚVODU: háček → co představujeme a proč to stojí za pozornost → pozvání
   k výběru → (u akcí) jemná naléhavost. Dva až čtyři krátké odstavce.

C) PODPISOVÁ VAZBA ZNAČKY, používej ji často:
   „Ať už [varianta A], nebo [varianta B], … najdete ten svůj / ta pravá / vás nezklame."

D) SLOVNÍK TRIOLY: dopřejte si, pocit výjimečnosti, ženskost, elegance, přirozená krása,
   cítit se sebevědomě, druhá kůže, sázka na jistotu, nedáte dopustit, ten svůj, ta pravá,
   vykouzlí siluetu, podtrhne. Vykáme, oslovujeme ženu přímo („vaše", „vám", „budete se
   cítit"). Píšeme o tom, jak se zákaznice bude cítit, ne jen co produkt umí.

E) SKUTEČNÉ PŘEDMĚTY TRIOLY — předmět je příslib nebo metafora, ne oznámení fakta:
{predmety}

F) SKUTEČNÁ CTA TLAČÍTKA: {ctas}
   Formát „Chci …" je nejsilnější, protože mluví za zákaznici.

G) VZOROVÉ ÚVODNÍ TEXTY:
{uvody}
"""
