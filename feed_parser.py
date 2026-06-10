import urllib.request
import xml.etree.ElementTree as ET
import re
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

FEED_URL = "https://www.triola.cz/feed/4/72b922270b116de2b42cd75019b78366af898d0a"
FEED_FILE = "triola_feed.xml"
CACHE_FILE = "products_cache.json"

def download_feed():
    """Downloads the XML feed and saves it to a file."""
    logging.info(f"Stahování XML feedu z {FEED_URL}...")
    try:
        req = urllib.request.Request(
            FEED_URL, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) TriolaCopywriter/1.0'}
        )
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            with open(FEED_FILE, "wb") as f:
                f.write(xml_data)
            logging.info(f"Feed úspěšně stažen a uložen ({len(xml_data)} bajtů).")
            return True
    except Exception as e:
        logging.error(f"Chyba při stahování feedu: {e}")
        return False

def clean_title(title, code, color):
    """Cleans product title to get a generic name without code or color."""
    t = title
    # Remove code if present
    if code:
        t = t.replace(code, "")
    # Remove color suffix
    if color:
        t = re.sub(rf'\b{re.escape(color)}\b', '', t, flags=re.IGNORECASE)
    # Remove dashes, spaces, and clean up
    t = t.replace(" - ", " ").replace("  ", " ").strip()
    # Normalize ending
    t = re.sub(r'\s+$', '', t)
    return t

def load_docx_cuts():
    cache_path = "docx_cuts_cache.json"
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def detect_cut_properties(code, title, description):
    """Detects Triola cut properties based on model code or descriptions and merges docx knowledge base."""
    code_str = str(code) if code else ""
    title_lower = title.lower()
    desc_lower = description.lower()
    
    # Defaults
    cut_name = "Neznámý střih"
    characteristics = "Standardní produkt spodního prádla."
    benefits = []
    
    # 1. Base classification based on codes or title
    # 28xxx - Perfect-Fit
    if code_str.startswith("28") or "perfect fit" in title_lower or "perfect-fit" in title_lower:
        cut_name = "Perfect-Fit"
        characteristics = "Hladká, tence vyztužená podprsenka s kosticemi navržená pro maximální oporu a formování postavy."
        benefits = [
            "Tence vyztužené bezešvé košíčky, které prsa nezvětšují, ale fixují v ideální výšce",
            "Materiál z jemného mikrovlákna se nerýsuje ani pod přiléhavým oblečením",
            "Flexi kostice se přizpůsobí pohybu těla a nikde netlačí",
            "Rozšířená ramínka ulevují ramenům a krční páteři",
            "Ideální pro střední a velká prsa (velikosti B až M)"
        ]
    # 22xxx - T-Fit
    elif code_str.startswith("22") or "t-fit" in title_lower or "t-šev" in desc_lower or "t-šev" in title_lower or "t-šev" in title_lower:
        cut_name = "T-Fit"
        characteristics = "Tradiční vyztužený střih s třídílnými košíčky sešitými do tvaru písmene T."
        benefits = [
            "Třídílný šitý košíček prsa perfektně zakulatí a upevní na středu",
            "Poskytuje skvělou oporu a vytvaruje nádherný dekolt i u povadlejšího poprsí",
            "Vyztužená konstrukce s pevnými kosticemi pro spolehlivost po celý den",
            "Vhodná pro malé, střední i velmi velké velikosti"
        ]
    # 29xxx - Top-Fit / Sensual-Fit
    elif code_str.startswith("29") or "top fit" in title_lower or "top-fit" in title_lower or "sensual-fit" in title_lower or "sensual fit" in title_lower:
        if "sensual-fit" in title_lower or "sensual fit" in title_lower:
            cut_name = "Sensual-Fit"
        else:
            cut_name = "Top-Fit"
        characteristics = "Hladká, tence vyztužená podprsenka s nižším středem a otevřenějším dekoltem."
        benefits = [
            "Nízký střed je ideální pro hluboké výstřihy do tvaru V",
            "Bezešvé košíčky vytvářejí hladkou siluetu, která je neviditelná pod oblečením",
            "Boční kostice a pevný obvod spolehlivě zafixují i větší poprsí",
            "Často doplněna o elegantní krajkové detaily na obvodu"
        ]
    # 27xxx - Krajková / Polo-vyztužená / Sexy-Fit
    elif code_str.startswith("27") or "polo-vyztužen" in desc_lower or "polo vyztuž" in desc_lower or "sexy-fit" in title_lower or "částečně vyztuž" in desc_lower:
        cut_name = "Krajková / Polo-vyztužená"
        characteristics = "Elegantní model kombinující funkční oporu vyztužené spodní části košíčku s jemností elastické krajky v horní části."
        benefits = [
            "Krajka v horní části košíčku se dokonale přizpůsobí prsu a opticky koriguje případnou drobnou asymetrii",
            "Spodní vyztužená část s kosticemi spolehlivě nese váhu prsou a nadzvedává je",
            "Kombinace luxusního ženského vzhledu a každodenního komfortu",
            "Široká škála velikostí"
        ]
    # 26xxx / 21xxx / 26xxx - Fixed-Fit / Comfy-Fit / S bočními dílky
    elif code_str.startswith("26") or code_str.startswith("21") or "fixed fit" in title_lower or "fixed-fit" in title_lower or "comfy-fit" in title_lower or "boční díl" in desc_lower or "bočními dílky" in desc_lower:
        if code_str.startswith("21") or "comfy" in title_lower:
            cut_name = "Comfy-Fit"
        else:
            cut_name = "Fixed-Fit"
        characteristics = "Střih s fixačními bočními dílky navržený speciálně pro plné, těžké poprsí s důrazem na maximální fixaci a odlehčení zad."
        benefits = [
            "Boční dílky košíčků prsa přitáhnou ke středu a zabrání jejich rozlévání do stran",
            "Pevný obvod a speciální konstrukce drží prsa pevně na středu a ve správné výšce",
            "Měkce podložená, široká ramínka rovnoměrně rozkládají váhu a ulehčují krční páteři",
            "Zadní obvod s pevným podložením, které se nevytahuje"
        ]
    # 14xxx - Soft-Fit (Bez kostic) / Casual-Fit
    elif code_str.startswith("14") or "bez kostic" in title_lower or "bez kostic" in desc_lower or "bezkosticová" in desc_lower or "casual-fit" in title_lower:
        if "casual" in title_lower or "casual-fit" in title_lower:
            cut_name = "Casual-Fit"
        else:
            cut_name = "Soft-Fit (Bez kostic)"
        characteristics = "Nevyztužená nebo tence vyztužená podprsenka zcela bez kostic pro absolutní svobodu pohybu."
        benefits = [
            "Žádné kostice – podprsenka nikde netlačí, netáhne a je extrémně pohodlná",
            "Třídílný střih košíčků s bočním dílkem přesto prsa spolehlivě zafixuje a vytvaruje",
            "Měkce vypodložená ramínka a elastický, přesto pevný obvod",
            "Skvělá volba pro domácí nošení, volný čas nebo pro ženy s citlivou pokožkou"
        ]
    elif "plavk" in title_lower or "plavky" in desc_lower or "plavková" in title_lower:
        cut_name = "Plavky Triola"
        characteristics = "Funkční plavková podprsenka z rychleschnoucího a odolného materiálu."
        benefits = [
            "Konstrukce vycházející z osvědčených střihů podprsenek Triola (např. Top-Fit nebo T-Fit)",
            "Pevně podložený zadní díl, který se ve vodě nevytáhne a udrží prsa ve správné výšce",
            "Variabilní ramínka s možností zapnutí do kříže nebo zavázání za krkem",
            "Odolnost vůči chloru a slunečnímu záření"
        ]
    elif "kalhotky" in title_lower or "panties" in title_lower or "brazilky" in title_lower or "tanga" in title_lower or "panty" in title_lower or code_str.startswith("31") or code_str.startswith("32") or code_str.startswith("34") or code_str.startswith("35") or code_str.startswith("37"):
        if "brazilky" in title_lower or "brazilky" in desc_lower or code_str.startswith("34") or code_str.startswith("37"):
            cut_name = "Brazilky"
        elif "tanga" in title_lower or "string" in title_lower or "tanga" in desc_lower:
            cut_name = "Tanga"
        elif "panty" in title_lower or "boxerky" in title_lower or code_str.startswith("35"):
            cut_name = "Panty"
        elif "stahovací" in title_lower or "formující" in title_lower or "stahovaci" in desc_lower or code_str.startswith("32"):
            cut_name = "Stahovací kalhotky"
        else:
            cut_name = "Klasické kalhotky"
        characteristics = "Pohodlné dámské kalhotky z příjemných a elastických materiálů."
        benefits = [
            "Perfektní střih, který dobře sedí, nezařezává se a drží na svém místě",
            "Bavlněný hygienický klínek pro maximální pohodlí a čistotu",
            "Zadní díl u brazilky zpracovaný bezešvě, aby se nerýsoval pod oblečením"
        ]

    # 2. DOCX Cut specifications mapping
    docx_data = load_docx_cuts()
    docx_desc = ""
    if docx_data:
        # Match keys in docx database
        docx_key = None
        if "balkon" in title_lower or "balkon" in desc_lower or "balkonov" in desc_lower:
            docx_key = "vyztuzena_podprsenka_balkonoveho_strihu"
        elif "zmenšov" in title_lower or "zmenšov" in desc_lower or "zmensovac" in title_lower or "zmensovac" in desc_lower:
            docx_key = "nevyztuzena_zmensovaci_podprsenka"
        elif "samodrž" in title_lower or "samodrž" in desc_lower or "samodrz" in title_lower or "samodrz" in desc_lower:
            docx_key = "samodrzici_podprsenka"
        elif "polo-vyztuž" in desc_lower or "polo vyztuž" in desc_lower or "částečně vyztuž" in desc_lower or "castecne vyztuz" in desc_lower or code_str.startswith("27"):
            docx_key = "castecne_vyztuzena_podprsenka_s_sitymi_kosiky"
        elif "řasen" in desc_lower or "řasen" in title_lower or "rasen" in desc_lower or "rasen" in title_lower:
            docx_key = "nevyztuzene_podprsenky_s_rasenymi_kosiky"
        elif "bez kostic" in title_lower or "bez kostic" in desc_lower or "bezkostic" in desc_lower or "bezkostic" in title_lower or code_str.startswith("14"):
            docx_key = "nevyztuzene_podprsenky_bez_kostic"
        elif "boční" in desc_lower or "boční" in title_lower or "bočn" in desc_lower or "comfy-fit" in title_lower or "comfy fit" in title_lower or code_str.startswith("21") or code_str.startswith("26"):
            docx_key = "nevyztuzene_podprsenky_s_bocnimi_dilky_a_s_kosticemi"
        elif code_str.startswith("22") or "t-fit" in title_lower or "t-šev" in desc_lower or "t-sev" in desc_lower:
            docx_key = "vyztuzena_podprsenka_s_sitymi_kosiky"
        elif code_str.startswith("28") or "perfect-fit" in title_lower or "perfect fit" in title_lower:
            docx_key = "vyztuzena_podprsenka_s_bezesvymi_kosiky"
            
        # Match kalhotky if not matched as podprsenka
        if not docx_key:
            if "tanga" in title_lower or "string" in title_lower or "tanga" in desc_lower:
                docx_key = "tanga"
            elif "brazilky" in title_lower or "brazilky" in desc_lower:
                docx_key = "brazilky"
            elif "panty" in title_lower or "boxerky" in title_lower or "panty" in desc_lower:
                docx_key = "panty"
            elif "stahovací" in title_lower or "formující" in title_lower or "stahovaci" in desc_lower or "formujici" in desc_lower or code_str.startswith("32"):
                docx_key = "stahovaci_a_formovaci_kalhotky"
            elif "klasické kalhotky" in title_lower or "klasicke kalhotky" in title_lower or ("kalhotky" in title_lower and code_str.startswith("31")):
                docx_key = "klasicke_kalhotky"

        # Load from parsed docx data
        if docx_key:
            # Check both podprsenky and kalhotky categories
            p_cuts = docx_data.get("podprsenky", {})
            k_cuts = docx_data.get("kalhotky", {})
            if docx_key in p_cuts:
                docx_desc = p_cuts[docx_key]["description"]
            elif docx_key in k_cuts:
                docx_desc = k_cuts[docx_key]["description"]
                
    return {
        "cut_name": cut_name,
        "characteristics": characteristics,
        "benefits": benefits,
        "docx_description": docx_desc
    }

def get_color_from_title(title):
    """Extracts color from title (usually after the dash or as a word)."""
    # Look for "- color" at the end of the title
    dash_match = re.search(r'-\s*([a-zA-Zá-žÁ-Ž\s\-]+)$', title)
    if dash_match:
        color = dash_match.group(1).strip()
        # Clean color names that might include sizes or clutter
        color = color.split(',')[0].strip()
        return color.lower()
    
    # Common Czech colors in underwear
    colors = [
        'černá', 'černé', 'bílá', 'bílé', 'tělová', 'tělové', 'béžová', 'béžové', 
        'cappuccino', 'smetanová', 'smetana', 'růžová', 'růžové', 'rosé', 'modrá', 
        'modré', 'červená', 'červené', 'fialová', 'lilek', 'lilková', 'meruňková',
        'šedo-fialová', 'šedá'
    ]
    for c in colors:
        if c in title.lower():
            return c
    return "neuvedena"

def parse_xml_feed():
    """Parses the XML feed file and returns raw product list."""
    if not os.path.exists(FEED_FILE):
        success = download_feed()
        if not success:
            return []
            
    logging.info("Parsování XML feedu...")
    try:
        # Register namespaces to find tags correctly
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'g': 'http://base.google.com/ns/1.0'
        }
        
        tree = ET.parse(FEED_FILE)
        root = tree.getroot()
        entries = root.findall('atom:entry', ns)
        
        products = []
        for entry in entries:
            title_node = entry.find('atom:title', ns)
            link_node = entry.find('atom:link', ns)
            desc_node = entry.find('g:description', ns)
            id_node = entry.find('g:id', ns)
            price_node = entry.find('g:price', ns)
            sale_price_node = entry.find('g:sale_price', ns)
            image_node = entry.find('g:image_link', ns)
            brand_node = entry.find('g:brand', ns)
            type_node = entry.find('g:product_type', ns)
            
            title = title_node.text if title_node is not None and title_node.text is not None else ""
            link = link_node.attrib.get('href', '') if link_node is not None else ""
            if not link and link_node is not None:
                link = link_node.text or ""
            description = desc_node.text if desc_node is not None and desc_node.text is not None else ""
            item_id = id_node.text if id_node is not None and id_node.text is not None else ""
            price = price_node.text if price_node is not None and price_node.text is not None else ""
            sale_price = sale_price_node.text if sale_price_node is not None and sale_price_node.text is not None else ""
            image = image_node.text if image_node is not None and image_node.text is not None else ""
            brand = brand_node.text if brand_node is not None and brand_node.text is not None else "Triola"
            prod_type = type_node.text if type_node is not None and type_node.text is not None else "Dámské spodní prádlo"
            
            # Find 5 digit number in title
            model_match = re.search(r'\b\d{5}\b', title)
            model_code = model_match.group(0) if model_match else None
            
            color = get_color_from_title(title)
            
            products.append({
                "id": item_id,
                "title": title,
                "link": link,
                "description": description,
                "price": price,
                "sale_price": sale_price,
                "image": image,
                "brand": brand,
                "type": prod_type,
                "model_code": model_code,
                "color": color
            })
            
        logging.info(f"Nalezeno {len(products)} produktů ve feedu.")
        return products
    except Exception as e:
        logging.error(f"Chyba při parsování XML feedu: {e}")
        return []

def group_products(products):
    """Groups products by model code or generic name to merge variants."""
    grouped = {}
    
    for p in products:
        # Determine the grouping key
        if p["model_code"]:
            key = p["model_code"]
        else:
            # Fallback key: clean product title or ID
            key = f"ID_{p['id']}"
            
        color_val = p["color"]
        
        if key not in grouped:
            # Initialize grouped product
            cut_data = detect_cut_properties(p["model_code"], p["title"], p["description"])
            cleaned_t = clean_title(p["title"], p["model_code"], p["color"])
            
            grouped[key] = {
                "model_code": p["model_code"] or key,
                "generic_title": cleaned_t,
                "brand": p["brand"],
                "type": p["type"],
                "cut_name": cut_data["cut_name"],
                "characteristics": cut_data["characteristics"],
                "benefits": cut_data["benefits"],
                "docx_description": cut_data.get("docx_description", ""),
                "base_price": p["price"],
                "sale_price": p["sale_price"],
                "variants": [],
                "all_colors": [],
                "all_images": [],
                "all_links": [],
                "combined_description": p["description"]
            }
            
        g = grouped[key]
        
        # Append variant details
        g["variants"].append({
            "id": p["id"],
            "title": p["title"],
            "color": color_val,
            "image": p["image"],
            "link": p["link"],
            "price": p["price"],
            "sale_price": p["sale_price"]
        })
        
        # Collect unique lists
        if color_val and color_val not in g["all_colors"] and color_val != "neuvedena":
            g["all_colors"].append(color_val)
            
        if p["image"] and p["image"] not in g["all_images"]:
            g["all_images"].append(p["image"])
            
        if p["link"] and p["link"] not in g["all_links"]:
            g["all_links"].append(p["link"])
            
        # If the current description is longer or contains more keywords, use it
        if len(p["description"]) > len(g["combined_description"]):
            g["combined_description"] = p["description"]
            
    # Clean up empty colors or fallback titles
    for k, g in grouped.items():
        if not g["all_colors"]:
            g["all_colors"] = ["standardní"]
            
    logging.info(f"Produkty seskupeny do {len(grouped)} unikátních modelů.")
    return grouped

def build_and_cache_products(force_update=False):
    """Downloads, parses, groups and caches products. Returns grouped products."""
    if not force_update and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                logging.info(f"Načteno {len(data)} modelů z cache souboru.")
                return data
        except Exception as e:
            logging.error(f"Chyba při čtení cache: {e}. Proběhne regenerace.")
            
    # Download and parse
    download_feed()
    raw_products = parse_xml_feed()
    if not raw_products:
        # If feed download failed, try loading old cache if exists
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
        
    grouped = group_products(raw_products)
    
    # Save to cache
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(grouped, f, ensure_ascii=False, indent=2)
        logging.info("Znalostní báze byla uložena do cache souboru.")
    except Exception as e:
        logging.error(f"Chyba při ukládání cache: {e}")
        
    return grouped

def search_products(query, products_db):
    """Searches products in grouped database by query."""
    if not query:
        return []
        
    q = query.lower().strip()
    results = []
    
    for key, p in products_db.items():
        # Match model code, title, cut, brand or colors
        code_match = q in str(p["model_code"]).lower()
        title_match = q in p["generic_title"].lower()
        cut_match = q in p["cut_name"].lower()
        brand_match = q in p["brand"].lower()
        color_match = any(q in c.lower() for c in p["all_colors"])
        
        # Calculate search relevance score
        score = 0
        if q == str(p["model_code"]).lower():
            score = 100 # Exact code match
        elif code_match:
            score = 80 # Partial code match
        elif title_match:
            score = 50
            # Higher score if query starts the title
            if p["generic_title"].lower().startswith(q):
                score += 15
        elif cut_match:
            score = 40
        elif brand_match:
            score = 20
        elif color_match:
            score = 30
            
        if score > 0:
            results.append({
                "product": p,
                "score": score
            })
            
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return [r["product"] for r in results[:10]] # Limit to top 10

if __name__ == "__main__":
    # Test script run
    print("Testování parseru...")
    db = build_and_cache_products(force_update=True)
    print(f"Hotovo. Databáze obsahuje {len(db)} modelů.")
    
    # Test search
    test_q = "28746"
    res = search_products(test_q, db)
    print(f"\nVýsledky vyhledávání pro '{test_q}':")
    for r in res:
        print(f"- {r['generic_title']} ({r['model_code']}) | Střih: {r['cut_name']} | Barvy: {', '.join(r['all_colors'])}")
