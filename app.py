from flask import Flask, render_template, request, jsonify
import logging
import os
import re
from dotenv import load_dotenv
import feed_parser
import sheet_parser
import batch_service
from ai_service import generate_copywriting, get_simulated_copywriting, generate_seo_snippet, MODEL_MAPPING, generate_batch_row_data

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

def merge_databases():
    global PRODUCTS_DB, MARKETING_DB
    logging.info("Slučování feed databáze s marketingovými podklady z Excelu...")
    # 1. Merge Excel marketing data into existing feed products
    for code, p in PRODUCTS_DB.items():
        m_data = sheet_parser.get_marketing_data_for_model(code, MARKETING_DB)
        if m_data:
            p["collection"] = m_data.get("collection", "")
            p["sales_arguments"] = m_data.get("sales_arguments", "")
            p["target_group"] = m_data.get("target_group", "")
            p["meta_title"] = m_data.get("meta_title", "")
            p["meta_description"] = m_data.get("meta_description", "")
            p["extra_descriptions"] = m_data.get("extra_descriptions", "")
            
    # 2. Add Excel-only products as stubs so they are searchable
    added_count = 0
    for code, m_entry in MARKETING_DB.items():
        if code not in PRODUCTS_DB:
            cut_name = m_entry["cuts"][0] if m_entry["cuts"] else "Neznámý střih"
            cut_data = feed_parser.detect_cut_properties(code, f"Podprsenka Triola {code}", "")
            m_data = sheet_parser.get_marketing_data_for_model(code, MARKETING_DB)
            
            PRODUCTS_DB[code] = {
                "model_code": code,
                "generic_title": f"Podprsenka Triola {code} (z Excelu)",
                "brand": "Triola",
                "type": "Dámské spodní prádlo",
                "cut_name": cut_name if cut_name != "Neznámý střih" else cut_data["cut_name"],
                "characteristics": cut_data["characteristics"],
                "benefits": cut_data["benefits"],
                "all_colors": ["viz tabulka"],
                "combined_description": "",
                "collection": m_data.get("collection", ""),
                "sales_arguments": m_data.get("sales_arguments", ""),
                "target_group": m_data.get("target_group", ""),
                "meta_title": m_data.get("meta_title", ""),
                "meta_description": m_data.get("meta_description", ""),
                "extra_descriptions": m_data.get("extra_descriptions", "")
            }
            added_count += 1
            
    logging.info(f"Sloučení dokončeno. Přidáno {added_count} nových modelů z Excelu. Celkem: {len(PRODUCTS_DB)} modelů.")

# Initialize product database
logging.info("Inicializace produktové databáze z feedu...")
PRODUCTS_DB = feed_parser.build_and_cache_products()
logging.info(f"Databáze úspěšně načtena. Počet modelů: {len(PRODUCTS_DB)}")

# Initialize marketing database from Excel
logging.info("Inicializace marketingové databáze z Excelu...")
MARKETING_DB = sheet_parser.build_marketing_db()
logging.info(f"Marketingová databáze úspěšně načtena. Počet modelů: {len(MARKETING_DB)}")

# Run merge
merge_databases()

@app.route('/')
def index():
    """Renders the main application page."""
    return render_template('index.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    """Endpoint for searching products in the database."""
    query = request.args.get('q', '')
    show_all = request.args.get('all', 'false') == 'true'
    
    if show_all:
        return jsonify(list(PRODUCTS_DB.values()))
        
    if not query:
        # Return popular recommendation models
        popular_codes = ["28746", "22000", "29665", "28003", "14020"]
        popular = [PRODUCTS_DB[code] for code in popular_codes if code in PRODUCTS_DB]
        # Fallback to first 5 products if popular not found
        if not popular:
            popular = list(PRODUCTS_DB.values())[:5]
        return jsonify(popular)
        
    results = feed_parser.search_products(query, PRODUCTS_DB)
    return jsonify(results)

@app.route('/api/generate', methods=['POST'])
def generate():
    """Endpoint for generating copywriting text."""
    data = request.json or {}
    product_code = data.get('product_code', '')
    format_type = data.get('format_type', 'popisek')
    model_key = data.get('model_key', 'claude-sonnet-5')
    tone_key = data.get('tone_key', 'empaticky')
    length_key = data.get('length_key', 'stredni')
    keywords = data.get('keywords', '')
    custom_instructions = data.get('custom_instructions', '')
    use_simulation = data.get('use_simulation', False)
    
    # 1. Resolve product context
    if product_code in PRODUCTS_DB:
        product_info = dict(PRODUCTS_DB[product_code]) # Copy to avoid modifying global cache
    else:
        # Code not in feed - build a mock product properties block based on prefix
        cut_data = feed_parser.detect_cut_properties(product_code, f"Podprsenka Triola {product_code}", "")
        product_info = {
            "model_code": product_code,
            "generic_title": f"Podprsenka Triola {product_code}",
            "brand": "Triola",
            "type": "Dámské spodní prádlo",
            "cut_name": cut_data["cut_name"],
            "characteristics": cut_data["characteristics"],
            "benefits": cut_data["benefits"],
            "recommendation": cut_data.get("recommendation", ""),
            "all_colors": ["černá", "bílá", "tělová"],
            "combined_description": ""
        }
        
    # Merge marketing data from Excel if available
    m_data = sheet_parser.get_marketing_data_for_model(product_code, MARKETING_DB)
    if m_data:
        product_info["collection"] = m_data.get("collection", "")
        product_info["sales_arguments"] = m_data.get("sales_arguments", "")
        product_info["target_group"] = m_data.get("target_group", "")
        product_info["meta_title"] = m_data.get("meta_title", "")
        product_info["meta_description"] = m_data.get("meta_description", "")
        product_info["extra_descriptions"] = m_data.get("extra_descriptions", "")
        
    # 2. Perform text generation
    try:
        if use_simulation:
            text = get_simulated_copywriting(product_info, format_type, tone_key)
        else:
            text = generate_copywriting(
                product_info=product_info,
                format_type=format_type,
                model_key=model_key,
                tone_key=tone_key,
                length_key=length_key,
                keywords=keywords,
                custom_instructions=custom_instructions
            )
        return jsonify({
            "success": True, 
            "text": text,
            "product": product_info
        })
    except Exception as e:
        logging.error(f"Chyba při generování textu: {e}")
        return jsonify({
            "success": False, 
            "error": str(e)
        }), 500

@app.route('/api/feed/update', methods=['POST'])
def update_feed():
    """Forces download and reload of the XML feed and Excel marketing sheets."""
    global PRODUCTS_DB, MARKETING_DB
    try:
        logging.info("Vynucená aktualizace XML feedu a Excelu z rozhraní...")
        PRODUCTS_DB = feed_parser.build_and_cache_products(force_update=True)
        MARKETING_DB = sheet_parser.build_marketing_db(force_update=True)
        merge_databases()
        return jsonify({
            "success": True, 
            "product_count": len(PRODUCTS_DB),
            "marketing_count": len(MARKETING_DB)
        })
    except Exception as e:
        logging.error(f"Chyba při aktualizaci feedů: {e}")
        return jsonify({
            "success": False, 
            "error": str(e)
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Checks the status of the keys and product counts."""
    openai_ok = bool(os.getenv("OPENAI_API_KEY"))
    anthropic_ok = bool(os.getenv("ANTHROPIC_API_KEY"))
    google_ok = bool(os.getenv("GOOGLE_API_KEY"))
    
    return jsonify({
        "openai_key": openai_ok,
        "anthropic_key": anthropic_ok,
        "google_key": google_ok,
        "product_count": len(PRODUCTS_DB),
        "marketing_count": len(MARKETING_DB),
        "excel_present": os.path.exists("triola_marketing_data.xlsx"),
        "models": list(MODEL_MAPPING.keys())
    })

# Create uploads directory if not exists
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/api/batch/upload', methods=['POST'])
def batch_upload():
    """Handles Excel file upload and returns rows to process."""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "Žádný soubor nebyl nahrán."}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "Prázdný název souboru."}), 400
        
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({"success": False, "error": "Nepodporovaný typ souboru. Nahrajte pouze soubory Excel (.xlsx, .xls)."}), 400
        
    from werkzeug.utils import secure_filename
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    try:
        rows = batch_service.parse_batch_excel(file_path, PRODUCTS_DB)
        return jsonify({
            "success": True,
            "filename": filename,
            "total_rows": len(rows),
            "rows": rows
        })
    except Exception as e:
        logging.error(f"Chyba při parsování nahrávaného Excelu: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/batch/process-row', methods=['POST'])
def batch_process_row():
    """Processes a single row from the Excel file."""
    data = request.json or {}
    filename = data.get('filename', '')
    row_num = data.get('row_num')
    model_code = data.get('model_code', '')
    color_name = data.get('color_name', '')
    arguments = data.get('arguments', '')
    product_name = data.get('product_name', '').strip()
    design_name = data.get('design_name', '').strip()
    row_brand = data.get('brand', '').strip()
    material = data.get('material', '').strip()
    size = data.get('size', '').strip()
    model_key = data.get('model_key', 'claude-sonnet-5')
    tone_key = data.get('tone_key', 'empaticky')
    use_simulation = data.get('use_simulation', False)
    
    if not filename or row_num is None or not model_code:
        return jsonify({"success": False, "error": "Chybí povinné parametry."}), 400
        
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({"success": False, "error": "Soubor neexistuje."}), 400
        
    # 1. Resolve product context
    # Check if model is in products db
    if model_code in PRODUCTS_DB:
        product_info = dict(PRODUCTS_DB[model_code])
        # Override color with the specific variant from Excel row
        product_info["all_colors"] = [color_name] if color_name else product_info.get("all_colors", [])
        if arguments:
            product_info["sales_arguments"] = arguments
        if row_brand:
            product_info["brand"] = row_brand
        if design_name:
            product_info["design_name"] = design_name
    else:
        # Build stub for missing product.
        # Pokud Excel obsahuje nazev produktu (napr. "Osuška", "Župan"), pouzij ho -
        # ne kazdy produkt je podprsenka a strihova detekce prádla by AI zmatla.
        lingerie_words = ("podprsenk", "kalhotk", "prádlo", "pradlo", "body", "korzet", "podvazk", "kosilka", "košilka", "plavky", "braletka", "bralet")
        is_lingerie = (not product_name) or any(w in product_name.lower() for w in lingerie_words)
        resolved_brand = row_brand if row_brand else "Triola"
        is_triola_brand = "triola" in resolved_brand.lower()

        if not is_triola_brand:
            # CIZI ZNACKA (napr. sassa): zadne "Triola" v nazvu, ZADNY kod v nazvu,
            # zadne Triola strihy - nazev = typ + znacka + design/kolekce.
            title_parts = [product_name.strip().capitalize() if product_name else "Produkt", resolved_brand]
            if design_name:
                title_parts.append(design_name.strip().title())
            details = [d for d in [f"Materiál: {material}" if material else "", f"Velikost: {size}" if size else ""] if d]
            product_info = {
                "model_code": model_code,
                "generic_title": " ".join(title_parts),
                "brand": resolved_brand,
                "design_name": design_name,
                "type": (product_name.strip().capitalize() if product_name else "Produkt"),
                "cut_name": (product_name.strip().capitalize() if product_name else "Produkt"),
                "characteristics": ". ".join(details) if details else f"Produkt značky {resolved_brand}.",
                "benefits": details,
                "docx_description": "",
                "recommendation": f"Produkt značky {resolved_brand} (NE Triola). Nepoužívej názvy střihů Triola ani claimy Trioly. Vycházej z prodejních argumentů, materiálu a velikosti.",
                "all_colors": [color_name] if color_name else ["standardní"],
                "combined_description": "",
                "sales_arguments": arguments
            }
        elif product_name and not is_lingerie:
            # Obecny produkt (osuska, zupan, doplnek...) - zadna podprsenkova terminologie
            details = [d for d in [f"Materiál: {material}" if material else "", f"Velikost: {size}" if size else ""] if d]
            product_info = {
                "model_code": model_code,
                "generic_title": f"{product_name.strip().capitalize()} Triola {model_code}",
                "brand": "Triola",
                "type": product_name.strip().capitalize(),
                "cut_name": product_name.strip().capitalize(),
                "characteristics": ". ".join(details) if details else f"{product_name.strip().capitalize()} značky Triola.",
                "benefits": [d for d in details] or [],
                "docx_description": "",
                "recommendation": "Piš věcně o tomto typu produktu. NEPOUŽÍVEJ terminologii spodního prádla (košíčky, kostice, ramínka, obvod). Vycházej z materiálu, velikosti a prodejních argumentů.",
                "all_colors": [color_name] if color_name else ["standardní"],
                "combined_description": "",
                "sales_arguments": arguments
            }
        else:
            cut_data = feed_parser.detect_cut_properties(model_code, f"Podprsenka Triola {model_code}", "")
            base_name = product_name.strip().capitalize() if product_name else ("Podprsenka" if not model_code.startswith('3') else "Kalhotky")
            product_info = {
                "model_code": model_code,
                "generic_title": f"{base_name} Triola {model_code}",
                "brand": "Triola",
                "type": "Dámské spodní prádlo" if not model_code.startswith('3') else "Dámské kalhotky",
                "cut_name": cut_data["cut_name"],
                "characteristics": cut_data["characteristics"],
                "benefits": cut_data["benefits"],
                "docx_description": cut_data.get("docx_description", ""),
                "recommendation": cut_data.get("recommendation", ""),
                "all_colors": [color_name] if color_name else ["standardní"],
                "combined_description": "",
                "sales_arguments": arguments
            }
        if material and "Materiál" not in str(product_info.get("characteristics", "")):
            product_info["characteristics"] = (str(product_info.get("characteristics", "")) + f" Materiál: {material}.").strip()
        
    # 2. Perform copywriting generation for all 6 columns in one single call
    try:
        results = generate_batch_row_data(
            product_info=product_info,
            model_key=model_key,
            tone_key=tone_key,
            use_simulation=use_simulation
        )
        
        # 3. Write back to excel
        batch_service.write_row_results_to_excel(file_path, row_num, results)
        
        return jsonify({
            "success": True,
            "row_num": row_num,
            "eshop_name": results.get("eshop_name", ""),
            "short_desc": results.get("short_desc", ""),
            "long_desc": results.get("eshop_desc1", ""),
            "eshop_desc2": results.get("eshop_desc2", ""),
            "meta_title": results.get("meta_title", ""),
            "meta_desc": results.get("meta_desc", "")
        })
    except Exception as e:
        logging.error(f"Chyba při zpracování řádku {row_num}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/batch/download/<filename>', methods=['GET'])
def batch_download(filename):
    """Serves the processed Excel file."""
    from flask import send_from_directory
    from werkzeug.utils import secure_filename
    clean_name = secure_filename(filename)
    return send_from_directory(app.config['UPLOAD_FOLDER'], clean_name, as_attachment=True)

@app.route('/api/seo/generate-single', methods=['POST'])
def seo_generate_single():
    """Generates an SEO snippet for a single page manually."""
    data = request.json or {}
    model_key = data.get('model_key', 'claude-sonnet-5')
    try:
        result = generate_seo_snippet(data, model_key)
        return jsonify({
            "success": True,
            "result": result
        })
    except Exception as e:
        logging.error(f"Chyba při generování single SEO: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def clean_html_to_text(html):
    # Remove script and style elements
    html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.IGNORECASE | re.DOTALL)
    # Remove HTML tags
    text = re.sub(r'<[^>]*>', ' ', html)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_usp_with_ai(text, openai_key, anthropic_key, google_key):
    system_prompt = """Jsi seniorní copywriter a SEO specialista. Z textu e-shopové stránky vytáhni 1 až 3 konkrétní věcné výhody (USP) produktu nebo kategorie.
Pravidla pro výhody:
- Pouze fakta, čísla, parametry, výhody (např. 'české šití', 'košíčky do velikosti J', '47 střihů skladem', 'bezešvé košíčky').
- ŽÁDNÉ prázdné fráze (jako 'nejlepší kvalita', 'skvělý výběr', 'luxusní prádlo').
- Výstup musí být ve formátu: výhody oddělené čárkami a mezerou (např: české šití, košíčky do velikosti J, 47 střihů skladem).
- Vrať POUZE tento čárkami oddělený seznam, bez jakýchkoliv keců okolo (žádné 'Zde jsou výhody:', '1.', '•', atd.)."""

    user_prompt = f"Zde je text stránky:\n\n{text}\n\nVytáhni USP:"

    try:
        from ai_service import execute_with_retry, generate_with_openai, generate_with_anthropic_fallback, generate_with_gemini
        
        if anthropic_key:
            return execute_with_retry(generate_with_anthropic_fallback, anthropic_key, "claude-sonnet-5", system_prompt, user_prompt).strip()
        elif openai_key:
            return execute_with_retry(generate_with_openai, openai_key, "gpt-4o-mini", system_prompt, user_prompt).strip()
        elif google_key:
            return execute_with_retry(generate_with_gemini, google_key, "gemini-2.5-flash", system_prompt, user_prompt).strip()
    except Exception as e:
        logging.error(f"Chyba při AI extrakci USP: {e}")
    return ""

@app.route('/api/seo/scrape', methods=['POST'])
def seo_scrape_page():
    """Fetches a page by URL and extracts title, meta description, H1, and AI-extracted USP."""
    data = request.json or {}
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({"success": False, "error": "Chybí URL adresa."}), 400
        
    # Prepend domain if relative path
    full_url = url
    if not url.startswith(('http://', 'https://')):
        # Ensure it starts with /
        if not url.startswith('/'):
            url = '/' + url
        full_url = f"https://www.triola.cz{url}"
        
    try:
        import requests
        from html.parser import HTMLParser
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(full_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # HTMLParser needs string html
        html_content = response.text
        
        class TriolaSEOHTMLParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.title = ""
                self.description = ""
                self.h1 = ""
                self.in_title = False
                self.in_h1 = False
                self.h1_found = False

            def handle_starttag(self, tag, attrs):
                if tag == 'title':
                    self.in_title = True
                elif tag == 'h1' and not self.h1_found:
                    self.in_h1 = True
                elif tag == 'meta':
                    attr_dict = dict(attrs)
                    name_val = attr_dict.get('name', '').lower()
                    if name_val == 'description':
                        self.description = attr_dict.get('content', '')

            def handle_endtag(self, tag):
                if tag == 'title':
                    self.in_title = False
                elif tag == 'h1':
                    self.in_h1 = False
                    self.h1_found = True

            def handle_data(self, data):
                if self.in_title:
                    self.title += data
                elif self.in_h1:
                    self.h1 += data
                    
        parser = TriolaSEOHTMLParser()
        parser.feed(html_content)
        
        # Clean extracted text
        title = parser.title.strip()
        description = parser.description.strip()
        h1 = parser.h1.strip()
        
        # Extract USP using first available API key
        usp = ""
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        google_key = os.getenv("GOOGLE_API_KEY")
        
        if openai_key or anthropic_key or google_key:
            clean_text = clean_html_to_text(html_content)[:6000]
            usp = extract_usp_with_ai(clean_text, openai_key, anthropic_key, google_key)
            
        return jsonify({
            "success": True,
            "title": title,
            "description": description,
            "h1": h1,
            "usp": usp
        })
        
    except Exception as e:
        logging.error(f"Chyba při crawlování URL {full_url}: {e}")
        return jsonify({
            "success": False,
            "error": f"Nepodařilo se stáhnout stránku: {str(e)}"
        }), 500


@app.route('/api/seo/upload', methods=['POST'])
def seo_upload():
    """Handles CSV/Excel upload and returns rows to process for SEO."""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "Žádný soubor nebyl nahrán."}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "Prázdný název souboru."}), 400
        
    if not file.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
        return jsonify({"success": False, "error": "Nepodporovaný typ souboru. Nahrajte pouze CSV nebo Excel (.xlsx, .xls)."}), 400
        
    from werkzeug.utils import secure_filename
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    try:
        rows = batch_service.parse_seo_batch(file_path)
        return jsonify({
            "success": True,
            "filename": filename,
            "total_rows": len(rows),
            "rows": rows
        })
    except Exception as e:
        logging.error(f"Chyba při parsování nahrávaného souboru pro SEO: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/seo/process-row', methods=['POST'])
def seo_process_row():
    """Processes a single row for SEO batch generation and writes to file."""
    data = request.json or {}
    filename = data.get('filename', '')
    row_num = data.get('row_num')
    model_key = data.get('model_key', 'claude-sonnet-5')
    
    if not filename or row_num is None:
        return jsonify({"success": False, "error": "Chybí povinné parametry (filename nebo row_num)."}), 400
        
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({"success": False, "error": "Soubor neexistuje."}), 400
        
    try:
        result = generate_seo_snippet(data, model_key)
        
        # Write to file
        batch_service.write_seo_to_file(file_path, row_num, result)
        
        return jsonify({
            "success": True,
            "row_num": row_num,
            "result": result
        })
    except Exception as e:
        logging.error(f"Chyba při zpracování SEO řádku {row_num}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/seo/download/<filename>', methods=['GET'])
def seo_download(filename):
    """Serves the processed SEO file."""
    from flask import send_from_directory
    from werkzeug.utils import secure_filename
    clean_name = secure_filename(filename)
    return send_from_directory(app.config['UPLOAD_FOLDER'], clean_name, as_attachment=True)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    logging.info(f"Spouštění serveru Triola Copywriting AI na portu {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
