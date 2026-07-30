# Manuál: Jak připravit podklady, aby se texty generovaly samy

Každý den **v 6:00 ráno** projde robot hlavní tabulku **Triola_CZ_Prodejní_argumenty**,
najde produkty s vyplněnými podklady a chybějícími texty a texty **sám doplní**.
Vy připravujete jen podklady — texty (CZ i SK) doplní robot.

---

## 1. Jak založit nový list

**Název listu = Značka + sezóna s rokem.** Robot zpracovává jen listy aktuální sezóny —
pozná je podle roku v názvu (letos `26`, příští rok `27`).

| Správně | Špatně | Proč |
|---|---|---|
| `Dorina SS26` | `Dorina jaro` | chybí rok — robot list přeskočí |
| `SASSA basic+AW26` | `Nová kolekce` | chybí značka i rok |
| `Triola PZ 26` | `PZ 26` | chybí značka — texty by vyšly bez značky |

- Značka v názvu listu určuje značku ve všech textech (`SASSA…` → texty pro Sassa).
- Listy s `basic`, `Basic` nebo `stálá kolekce` v názvu robot bere **stále**, i bez roku.
- Staré sezóny (25, 24…) robot ignoruje — nic v nich nepřepíše.
- Nejjednodušší je **zkopírovat existující list** (pravý klik na záložku → Duplikovat),
  smazat řádky a přejmenovat.

## 2. Povinné sloupce (bez nich robot řádek přeskočí)

| Sloupec | Co vyplnit | Příklad |
|---|---|---|
| **Nomenklatura** | kód produktu | `SAS1A004` |
| **PRODUKT** | typ produktu, malými písmeny | `podprsenka`, `kalhotky`, `osuška` |
| **PRODEJNÍ ARGUMENTY** | vlastnosti a benefity oddělené středníkem — **minimálně 15 znaků**, ideálně 3–6 konkrétních bodů | `vyztužená podprsenka s kosticí; vyšší střed; krajkový obvod; nastavitelná ramínka; + kalhotky do setu` |

**Prodejní argumenty jsou jediný zdroj, ze kterého robot píše.** Co tam není, v textu
nebude — a robot si nesmí nic vymýšlet. Čím konkrétnější argumenty, tím lepší text.
Pište materiály, střihy a funkce, ne obecnosti („krásná", „kvalitní" robot nevyužije).

## 3. Doporučené sloupce (zlepšují výsledek)

| Sloupec | K čemu slouží | Příklad |
|---|---|---|
| **Název** | název kolekce/designu — objeví se v názvu produktu, ale robot z něj NIKDY neodvozuje vlastnosti | `HAPPY CHOICE` |
| **Barva** | propíše se do názvu i textů | `smetanová` |
| **Velikost** | rozsah velikostí | `B75-B85  C75-C85` |
| **Značka** | jen pokud se liší od názvu listu (např. list „Ostatní značky") | `Triumph` |

## 4. Co robot doplní (12 sloupců)

České: **E-SHOP NÁZEV** (formát Heureka: Značka + přívlastek + typ + barva) ·
**E-SHOP KRÁTKÝ NÁZEV** (jedna prodejní věta, max 120 znaků) ·
**TRIOLA ESHOP POPIS** (hlavní popis, 90–140 slov, HTML) ·
**TRIOLA ESHOP POPIS 2** (doplňkový krátký popis) ·
**ESHOP META TITLE** (do 60 znaků) · **ESHOP META DESCRIPTION** (do 155 znaků).

Slovenské: stejné sloupce s příponou **SK**. Pokud sloupce v listu nejsou,
robot si je sám přidá na konec.

## 5. Zlatá pravidla

1. **Robot nikdy nemaže ani nepřepisuje.** Doplňuje jen prázdné buňky. Vaše ruční
   úpravy textů jsou v bezpečí.
2. **Chcete text vygenerovat znovu?** Smažte obsah buňky (Delete) — druhý den ráno
   ji robot doplní. Nebo požádejte o ruční spuštění, je to hned.
3. **Řádek bez prodejních argumentů = žádný text.** Robot ho přeskočí a počká,
   až argumenty doplníte.
4. U cizích značek (Sassa, Dorina…) robot **nikdy nepoužije** claimy Trioly
   (bra-fitting, česká výroba…) ani kód produktu v názvu.
5. Název kolekce (`HAPPY CHOICE`) se objeví v názvu produktu, ale robot z něj
   nevymýšlí vlastnosti — „Happy" neznamená, že text bude o štěstí.

## 6. Kdy se co stane

| Situace | Výsledek |
|---|---|
| V pátek přidáte 3 řádky s argumenty | v sobotu v 6:00 mají texty |
| Přidáte řádek bez argumentů | robot čeká, dokud argumenty nedoplníte |
| Smažete text v jedné buňce | druhý den ráno je doplněná znovu |
| Založíte list `Dorina SS27` | robot ho zpracovává (rok 27 = příští sezóna) |
| Založíte list `Dorina léto` | robot ho NEVIDÍ — chybí rok v názvu |

*Otázky a ruční spuštění mimo ranní čas: Luboš.*
