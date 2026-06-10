import os
import logging
import re
import time
from dotenv import load_dotenv
import openai
import anthropic
from google import genai
from google.genai import types

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Default active model IDs based on verification
MODEL_MAPPING = {
    # Anthropic
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
3. Styl a plynulost: Píšeme pro čtenáře, ne pro roboty. Vyhýbej se klišé jako "must-have", "nechte se hýčkat", "jedinečný kousek" či "fascinující". Raději buď konkrétní (např. místo "skvělý materiál" napiš "pružný žakárový úplet s podílem elastanu").
4. Zákaz robotického AI jazyka: Vyhni se slovům jako "klíčový", "transformovat", "vstupte do světa", "navržen tak, aby", "představujeme vám". Piš přirozeně, jako bys mluvila s kamarádkou, ale s odbornou autoritou.
5. Správná terminologie: Používej termíny jako "flexi kostice", "T-šev", "Spacer košíček", "Perfect-Fit střih", "zadní díl s pevným podložením".
6. ZÁKAZ FABULACE KOLEKCÍ: Nikdy si nevymýšlej žádné názvy kolekcí (např. Tina atd.). Zmiňuj pouze název kolekce, který je explicitně uveden v marketingových podkladech. Pokud tam není, o žádné kolekci nepiš!

INFORMACE O STŘIZÍCH TRIOLA (ZNALOSTNÍ BÁZE):
- Perfect-Fit: Hladká, tence vyztužená podprsenka s kosticemi. Nezvětšuje objem, ale fixuje prsa v ideální výšce. Vhodná pro střední a velké velikosti pod přiléhavé oblečení.
- T-Fit: Třídílný košíček s T-švem. Dokonale prsa zakulatí, pozvedne a zafixuje na středu. Klasika pro velkou oporu.
- Top-Fit / Sensual-Fit: Hladká vyztužená podprsenka s nižším středem. Skvělá do hlubokých výstřihů.
- Fixed-Fit: Zpevňující střih pro těžká prsa, pevně drží na středu, široká ramínka pro úlevu zad a ramen.
- Soft-Fit (Bez kostic): Maximální svoboda pohybu a pohodlí bez kostic. Třídílný košíček s bočním dílkem přesto prsa spolehlivě zafixuje.
- Plavky Triola: Plavková podprsenka z rychleschnoucího materiálu, s pevným podložením, které drží i ve vodě.

Píšeme česky, čtivě, plynule, spisovně."""

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

def generate_with_anthropic(api_key, model, system_prompt, user_prompt):
    """Call Anthropic API using message structure."""
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=2500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        temperature=0.7
    )
    return message.content[0].text

def generate_with_gemini(api_key, model, system_prompt, user_prompt):
    """Call Google Gemini API using new google-genai client."""
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
    prod_colors = ", ".join(product_info.get("all_colors", ["standardní"]))
    prod_cut = product_info.get("cut_name", "Neznámý střih")
    prod_char = product_info.get("characteristics", "")
    prod_benefits = "\\n - " + "\\n - ".join(product_info.get("benefits", [])) if product_info.get("benefits") else ""
    prod_price = product_info.get("base_price", "")
    prod_desc = product_info.get("combined_description", "")
    prod_docx = product_info.get("docx_description", "")
    
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
        if collection: 
            marketing_block += f"- Název kolekce: {collection}\n"
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
STŘIH PODPRSENKY: {prod_cut}
CHARAKTERISTIKA STŘIHU: {prod_char}
OFICIÁLNÍ KONSTRUKČNÍ SPECIFIKACE STŘIHU (z Wordu): {prod_docx if prod_docx else 'Není specifikováno'}
KLÍČOVÉ VÝHODE: {prod_benefits}
DOSTUPNÉ BARVY: {prod_colors}
DŮLEŽITÉ UPOZORNĚNÍ K BARVĚ: V celém textu piš VÝHRADNĚ o barvě uvedené v poli "DOSTUPNÉ BARVY" (tj. {prod_colors}). Ignoruj jakékoliv jiné barvy zmíněné v původním popisu produktu nebo v marketingových podkladech, pokud se liší od této zadané barvy. Například pokud je zadaná barva "{prod_colors}" (např. lilková, bordó), nesmí se v textu objevit slovo "černá" nebo "bílá" z původního popisu!
DŮLEŽITÉ UPOZORNĚNÍ K NÁZVŮM KOLEKCÍ: Nikdy si nevymýšlej ani nepředpokládej žádný název kolekce (např. Tina atd.), pokud není výslovně uveden pod klíčem "Název kolekce" v marketingových podkladech níže. Pokud je tam hodnota prázdná, v textu o žádné kolekci nepiš!
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
            text = execute_with_retry(generate_with_anthropic, anthropic_key, model_name, TRIOLA_SYSTEM_PROMPT, user_prompt)
            
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
Představujeme vám model **{prod_title}** se střihem **{prod_cut}**! Hladká ramínka a jemný materiál se postarají o vaše celodenní pohodlí, zatímco precizní střih vytvoří krásný dekolt. 
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
