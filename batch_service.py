import os
import openpyxl
import re
import logging

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
