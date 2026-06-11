import os
import openpyxl
import re
import logging
import csv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

COLOR_CODE_TO_NAME = {
    "01": "bílá - puntíček",
    "02": "stříbrná",
    "03": "bílá",
    "04": "černá",
    "05": "modrá",
    "06": "nugát",
    "07": "čokoládová",
    "08": "zelená",
    "09": "šedá",
    "10": "vínová",
    "11": "hnědá",
    "12": "slonová kost",
    "13": "jeans",
    "14": "rosé",
    "15": "zlatozelená",
    "16": "smetanovo - modrá",
    "17": "fialová",
    "18": "khaki",
    "19": "černo - zelená",
    "20": "jahodová",
    "21": "červená",
    "22": "modro - růžová",
    "23": "průhledná",
    "24": "make-up",
    "25": "světle modrá",
    "26": "ash",
    "27": "tyrkysová",
    "28": "světle zelená",
    "29": "fuchsiová",
    "30": "perlová",
    "31": "shadow",
    "32": "cherry",
    "33": "malinová",
    "34": "modro - šedá",
    "35": "navy",
    "36": "modro-červená",
    "37": "medová",
    "38": "šedo - fialová",
    "39": "petrolejová",
    "40": "lilková",
    "41": "lunar rock",
    "42": "smetanová kvítek",
    "43": "cihlová",
    "44": "lososová",
    "45": "černo-červená",
    "46": "šedo - modrá",
    "47": "dusty rose",
    "48": "perleťově modrá",
    "49": "olivová",
    "50": "zlatá",
    "51": "karmínová",
    "52": "šedo - růžová",
    "53": "tmavě šedá",
    "54": "koňaková",
    "55": "měděná",
    "67": "deco rose",
    "68": "cappuccino",
    "69": "bílo - zelená",
    "70": "žlutá",
    "71": "mint",
    "72": "smaragdová",
    "77": "šedo - hnědá",
    "78": "ametystová",
    "79": "nachová",
    "80": "oranžová",
    "81": "růžová",
    "82": "tm. růžová",
    "83": "smetana",
    "84": "champagne",
    "85": "eurová",
    "86": "tělová",
    "87": "dračí ovoce",
    "88": "bordó",
    "89": "lambrusco",
    "90": "černo - bílá",
    "91": "limeta",
    "92": "pudr",
    "93": "světle šedá",
    "95": "béžová",
    "97": "černá - tisk",
    "98": "kardinál",
    "99": "vícebarevná"
}

def resolve_color(model_code, color_code, products_db):
    """
    Attempts to match a color code (like 88 or 04) to a standard Czech color name.
    Prioritizes the static code mapping, then matches against feed variants,
    falling back to feed colors if the code is unknown.
    """
    if not color_code:
        return "neuvedena"
        
    color_code_str = str(color_code).strip().zfill(2) # Normalise e.g. "4" -> "04", "88" -> "88"
    expected_color = COLOR_CODE_TO_NAME.get(color_code_str)
    
    # 1. Check if model is in products db
    if model_code in products_db:
        feed_colors = products_db[model_code].get("all_colors", [])
        if expected_color:
            # Check if there is an exact or substring match in feed colors
            for fc in feed_colors:
                if expected_color in fc.lower() or fc.lower() in expected_color:
                    return fc
            # If not in feed but we have a name, return the mapped name (new variant)
            return expected_color
        else:
            # If we don't have expected color, fall back to single feed color if it exists
            if len(feed_colors) == 1:
                return feed_colors[0]
                
    # 2. Fallback to static mapping or raw code
    return expected_color if expected_color else f"kód {color_code}"

def parse_batch_excel(file_path, products_db):
    """
    Parses the uploaded Excel file. Skips empty rows.
    Automatically resolves the color names and checks if the model is in the DB.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Soubor {file_path} neexistuje.")
        
    logging.info(f"Načítání Excelu: {file_path}")
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb.active
    
    # Identify columns
    fazona_idx = -1
    arguments_idx = -1
    
    headers = [str(cell.value).strip().lower() if cell.value is not None else "" for cell in ws[1]]
    for idx, h in enumerate(headers):
        if "fazón" in h or "číslo" in h or "kod" in h or h == "code":
            fazona_idx = idx
        elif "argument" in h or "prodejní" in h or "prodejni" in h:
            arguments_idx = idx
            
    # Fallback to column index if headers are not matched exactly
    if fazona_idx == -1:
        fazona_idx = 0
    if arguments_idx == -1:
        arguments_idx = 1
        
    rows = []
    # Loop from row 2 (first row is header)
    for r in range(2, ws.max_row + 1):
        raw_code = ws.cell(row=r, column=fazona_idx + 1).value
        args = ws.cell(row=r, column=arguments_idx + 1).value
        
        if raw_code is None and args is None:
            continue # Skip blank rows
            
        code_str = str(raw_code).strip() if raw_code is not None else ""
        if not code_str:
            continue
            
        # Parse model and color code (e.g. 22859/88)
        parts = code_str.split('/')
        model_code = parts[0].strip()
        color_code = parts[1].strip() if len(parts) > 1 else ""
        
        color_name = resolve_color(model_code, color_code, products_db)
        
        # Check if we have the model in products cache
        in_db = model_code in products_db
        
        rows.append({
            "row_num": r,
            "raw_code": code_str,
            "model_code": model_code,
            "color_code": color_code,
            "color_name": color_name,
            "arguments": str(args).strip() if args is not None else "",
            "in_db": in_db
        })
        
    logging.info(f"Získáno {len(rows)} datových řádků k zpracování.")
    return rows

def write_descriptions_to_excel(file_path, row_num, short_html, long_html):
    """
    Writes the generated descriptions into new columns in the Excel file.
    Creates column headers if they don't exist yet.
    """
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active
    
    # Get current headers
    headers = [str(cell.value).strip() if cell.value is not None else "" for cell in ws[1]]
    
    short_col_idx = -1
    long_col_idx = -1
    
    for idx, h in enumerate(headers):
        if h == "Krátký popis (HTML)":
            short_col_idx = idx + 1
        elif h == "Dlouhý popis (HTML)":
            long_col_idx = idx + 1
            
    # If columns do not exist, create them
    if short_col_idx == -1:
        short_col_idx = len(headers) + 1
        ws.cell(row=1, column=short_col_idx, value="Krátký popis (HTML)")
        headers.append("Krátký popis (HTML)")
        
    if long_col_idx == -1:
        long_col_idx = len(headers) + 1
        ws.cell(row=1, column=long_col_idx, value="Dlouhý popis (HTML)")
        
    # Write values
    ws.cell(row=row_num, column=short_col_idx, value=short_html)
    ws.cell(row=row_num, column=long_col_idx, value=long_html)
    
    wb.save(file_path)
    logging.info(f"Zapsány HTML popisky na řádek {row_num} v {file_path}")

def normalize_header(h):
    if not h:
        return ""
    trans = str.maketrans("áéěíóúůýžščřďťň", "aeeouuyzscrdtnn")
    h = str(h).lower().strip().translate(trans)
    h = re.sub(r'[\s_\-]+', '', h)
    return h

def detect_csv_encoding_and_delimiter(file_path):
    encodings = ['utf-8-sig', 'windows-1250', 'utf-8', 'latin1']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                first_line = f.readline()
                if not first_line:
                    continue
                semicolons = first_line.count(';')
                commas = first_line.count(',')
                tabs = first_line.count('\t')
                
                delimiter = ';'
                if commas > semicolons and commas > tabs:
                    delimiter = ','
                elif tabs > semicolons and tabs > commas:
                    delimiter = '\t'
                return enc, delimiter
        except UnicodeDecodeError:
            continue
    return 'utf-8', ';'

def parse_seo_batch(file_path):
    """
    Parses CSV or Excel file for SEO Snippet generation.
    Returns a list of dicts with normalized keys.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Soubor {file_path} neexistuje.")

    ext = os.path.splitext(file_path.lower())[1]
    rows = []
    headers = []

    if ext == '.csv':
        enc, delimiter = detect_csv_encoding_and_delimiter(file_path)
        with open(file_path, 'r', encoding=enc) as f:
            reader = csv.reader(f, delimiter=delimiter)
            try:
                headers = next(reader)
            except StopIteration:
                return []
            
            headers = [h.strip() for h in headers]
            
            for idx, row in enumerate(reader, start=2):
                if not row or all(cell.strip() == "" for cell in row):
                    continue
                rows.append((idx, row))
    elif ext in ['.xlsx', '.xls']:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb.active
        
        header_row = [ws.cell(row=1, column=c).value for c in range(1, ws.max_column + 1)]
        headers = [str(h).strip() if h is not None else "" for h in header_row]
        
        for idx in range(2, ws.max_row + 1):
            row_vals = [ws.cell(row=idx, column=c).value for c in range(1, ws.max_column + 1)]
            row_str_vals = [str(cell).strip() if cell is not None else "" for cell in row_vals]
            if all(cell == "" for cell in row_str_vals):
                continue
            rows.append((idx, row_str_vals))
    else:
        raise ValueError(f"Nepodporovaný formát souboru: {ext}")

    mapping = {}
    normalized_headers = [normalize_header(h) for h in headers]
    
    keyword_patterns = ['primarnikw', 'primarniklicoveslovo', 'klicoveslovo', 'klicovyvyraz', 'klicovydotaz', 'dotaz', 'kw']
    intent_patterns = ['intent', 'zamer', 'typzameru']
    type_patterns = ['typstranky', 'kategorie', 'pagetype', 'typ']
    title_patterns = ['soucasnytitle', 'aktualnititle', 'staritle', 'title']
    desc_patterns = ['soucasnadesc', 'soucasnydescription', 'aktualnidesc', 'description', 'desc', 'popisek']
    h1_patterns = ['soucasnyh1', 'aktualnih1', 'h1']
    usp_patterns = ['usp', 'vyhody', 'prednosti', 'argumenty']
    brand_patterns = ['brand', 'znacka', 'firma']
    serp_patterns = ['konkurenceserp', 'serpkonkurence', 'konkurence', 'titleskonkurence']
    url_patterns = ['url', 'adresa', 'link', 'stranka']

    def find_idx(patterns):
        for pattern in patterns:
            for i, nh in enumerate(normalized_headers):
                if nh == pattern:
                    return i
        for pattern in patterns:
            for i, nh in enumerate(normalized_headers):
                if pattern in nh or nh in pattern:
                    return i
        return -1

    mapping['url'] = find_idx(url_patterns)
    mapping['primarni_kw'] = find_idx(keyword_patterns)
    mapping['intent'] = find_idx(intent_patterns)
    mapping['typ_stranky'] = find_idx(type_patterns)
    mapping['soucasny_title'] = find_idx(title_patterns)
    mapping['soucasna_desc'] = find_idx(desc_patterns)
    mapping['soucasny_h1'] = find_idx(h1_patterns)
    mapping['usp'] = find_idx(usp_patterns)
    mapping['brand'] = find_idx(brand_patterns)
    mapping['konkurence_serp'] = find_idx(serp_patterns)

    standard_keys = ['url', 'primarni_kw', 'intent', 'typ_stranky', 'soucasny_title', 'soucasna_desc', 'soucasny_h1', 'usp', 'brand', 'konkurence_serp']
    for idx, key in enumerate(standard_keys):
        if mapping[key] == -1 and idx < len(headers):
            mapping[key] = idx

    parsed_data = []
    for idx, row in rows:
        def get_val(key, default=""):
            col_idx = mapping[key]
            if col_idx != -1 and col_idx < len(row):
                return str(row[col_idx]).strip()
            return default

        parsed_data.append({
            "row_num": idx,
            "url": get_val('url'),
            "primarni_kw": get_val('primarni_kw'),
            "intent": get_val('intent'),
            "typ_stranky": get_val('typ_stranky'),
            "soucasny_title": get_val('soucasny_title'),
            "soucasna_desc": get_val('soucasna_desc'),
            "soucasny_h1": get_val('soucasny_h1'),
            "usp": get_val('usp'),
            "brand": get_val('brand', 'Triola'),
            "konkurence_serp": get_val('konkurence_serp')
        })
    
    return parsed_data

def write_seo_to_file(file_path, row_num, seo_data):
    """
    Writes the generated SEO snippet data into new columns in the CSV/Excel file.
    Creates column headers if they don't exist yet.
    """
    ext = os.path.splitext(file_path.lower())[1]
    
    headers_to_add = [
        "Navržený Title",
        "Délka Title",
        "Navržený Description",
        "Délka Description",
        "Navržený H1",
        "Pattern Break",
        "Otevřená smyčka",
        "Rizika"
    ]
    
    vals_to_add = [
        seo_data.get("title", ""),
        seo_data.get("title_znaku", len(seo_data.get("title", ""))),
        seo_data.get("description", ""),
        seo_data.get("desc_znaku", len(seo_data.get("description", ""))),
        seo_data.get("h1", ""),
        seo_data.get("pattern_break", ""),
        seo_data.get("smycka", ""),
        seo_data.get("rizika", "")
    ]
    
    if ext == '.csv':
        enc, delimiter = detect_csv_encoding_and_delimiter(file_path)
        all_rows = []
        with open(file_path, 'r', encoding=enc) as f:
            reader = csv.reader(f, delimiter=delimiter)
            all_rows = list(reader)
            
        if not all_rows:
            return
            
        headers = all_rows[0]
        col_idxs = {}
        for h in headers_to_add:
            if h in headers:
                col_idxs[h] = headers.index(h)
            else:
                headers.append(h)
                col_idxs[h] = len(headers) - 1
                
        for r_idx in range(len(all_rows)):
            while len(all_rows[r_idx]) < len(headers):
                all_rows[r_idx].append("")
                
        target_idx = row_num - 1
        if 0 < target_idx < len(all_rows):
            for h, val in zip(headers_to_add, vals_to_add):
                col_i = col_idxs[h]
                all_rows[target_idx][col_i] = str(val)
                
        with open(file_path, 'w', encoding=enc, newline='') as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerows(all_rows)
            
    elif ext in ['.xlsx', '.xls']:
        wb = openpyxl.load_workbook(file_path)
        ws = wb.active
        
        header_row = [ws.cell(row=1, column=c).value for c in range(1, ws.max_column + 1)]
        headers = [str(h).strip() if h is not None else "" for h in header_row]
        
        col_idxs = {}
        for h in headers_to_add:
            if h in headers:
                col_idxs[h] = headers.index(h) + 1
            else:
                new_col = len(headers) + 1
                ws.cell(row=1, column=new_col, value=h)
                headers.append(h)
                col_idxs[h] = new_col
                
        for h, val in zip(headers_to_add, vals_to_add):
            col_i = col_idxs[h]
            ws.cell(row=row_num, column=col_i, value=val)
            
        wb.save(file_path)
        
    logging.info(f"Zapsána SEO data na řádek {row_num} v {file_path}")

