import zipfile
import xml.etree.ElementTree as ET
import os
import json
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DOCX_FILE = "Typy podprsenek a kalhotek.docx"
DOCX_CACHE_FILE = "docx_cuts_cache.json"

def clean_paragraph_text(text):
    """Removes special image placeholders and layout indicators from DOCX text."""
    if not text:
        return ""
    
    # Remove noise prefixes like left635, right635, righttop
    text_clean = re.sub(r'^(left\d+|right\d+|righttop|lefttop)', '', text)
    # Remove specific symbols and non-breakable spaces
    text_clean = text_clean.replace("", "").replace("\xa0", " ").strip()
    return text_clean

def parse_docx_cuts(force_update=False):
    """Parses Typy podprsenek a kalhotek.docx and caches the cuts info to a JSON file."""
    if not force_update and os.path.exists(DOCX_CACHE_FILE):
        try:
            with open(DOCX_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                logging.info(f"Načteno {len(data['podprsenky']) + len(data['kalhotky'])} střihů z DOCX cache.")
                return data
        except Exception as e:
            logging.error(f"Chyba při čtení cache střihů z DOCX: {e}")

    if not os.path.exists(DOCX_FILE):
        logging.warning(f"Dokument {DOCX_FILE} neexistuje. AI poběží s výchozími definicemi střihů.")
        return {"podprsenky": {}, "kalhotky": {}}

    logging.info("Parsování střihů z Word dokumentu (.docx)...")
    try:
        z = zipfile.ZipFile(DOCX_FILE)
        doc_xml = z.read('word/document.xml')
        root = ET.fromstring(doc_xml)
        
        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        paragraphs = root.findall('.//w:p', namespaces)
        
        # Read text from paragraphs
        raw_paras = []
        for p in paragraphs:
            text = "".join(node.text for node in p.iter() if node.text is not None)
            cleaned = clean_paragraph_text(text)
            if cleaned:
                raw_paras.append(cleaned)
                
        # Define sections based on headings
        # We will scan for known headings
        headings = [
            "VYZTUŽENÁ PODPRSENKA S ŠITÝMI KOŠÍKY",
            "VYZTUŽENÁ PODPRSENKA S BEZEŠVÝMI KOŠÍKY",
            "SAMODRŽÍCÍ PODPRSENKA",
            "VYZTUŽENÁ PODPRSENKA BALKONOVÉHO STŘIHU",
            "ČÁSTEČNĚ VYZTUŽENÁ PODPRSENKA S ŠITÝMI KOŠÍKY",
            "PUSH - UP VYZTUŽENÁ PODPRSENKA",
            "VYZTUŽENÁ I NEVYZTUŽENÁ PODPRSENKA BEZ SEDLA",
            "NEVYZTUŽENÉ PODPRSENKY S ŘASENÝMI KOŠÍKY",
            "NEVYZTUŽENÉ PODPRSENKY S BOČNÍMI DÍLKY A S KOSTICEMI",
            "NEVYZTUŽENÁ ZMENŠOVACÍ PODPRSENKA",
            "NEVYZTUŽENÉ PODPRSENKY BEZ KOSTIC",
            "TANGA",
            "BRAZILKY",
            "KLASICKÉ KALHOTKY",
            "PANTY",
            "STAHOVACÍ A FORMOVACÍ KALHOTKY"
        ]
        
        cuts_data = {
            "podprsenky": {},
            "kalhotky": {}
        }
        
        current_section = None
        current_category = "podprsenky" # Default category
        current_paragraphs = []
        
        # Categorize headings statically
        podprsenky_headings = headings[:11]
        kalhotky_headings = headings[11:]

        def remove_diacritics(text):
            accent_map = {
                'á': 'a', 'č': 'c', 'ď': 'd', 'é': 'e', 'ě': 'e', 'í': 'i', 'ň': 'n',
                'ó': 'o', 'ř': 'r', 'š': 's', 'ť': 't', 'ú': 'u', 'ů': 'u', 'ý': 'y', 'ž': 'z',
                'Á': 'a', 'Č': 'c', 'Ď': 'd', 'É': 'e', 'Ě': 'e', 'Í': 'i', 'Ň': 'n',
                'Ó': 'o', 'Ř': 'r', 'Š': 's', 'Ť': 't', 'Ú': 'u', 'Ů': 'u', 'Ý': 'y', 'Ž': 'z'
            }
            return "".join(accent_map.get(c, c) for c in text)

        def get_normalized_key(heading):
            # Convert to ascii-like lowercase snake_case
            h = remove_diacritics(heading).lower()
            h = h.replace("vyztuzena", "vyztuzena").replace("vyztuzene", "vyztuzene")
            h = h.replace("sitymi", "sitymi").replace("kosiky", "kosiky").replace("kosicky", "kosiky")
            
            # Clean non-alphanumeric and make snake_case
            h = re.sub(r'[^a-z0-9\s-]', '', h).strip()
            h = re.sub(r'\s+', '_', h)
            return h

        # Loop through paragraphs and cluster under headings
        for p_text in raw_paras:
            # Check if this paragraph is one of our headings
            matched_heading = None
            p_clean = clean_paragraph_text(p_text)
            # Strip smart quotes and brackets
            p_clean = re.sub(r'[^a-zA-Zá-žÁ-ŽČŠŽÍěščřžýáíéóúůďťňĎŤŇ\s]', '', p_clean)
            p_clean = re.sub(r'\s+', ' ', p_clean).strip()
            
            if len(p_clean) < 80:
                p_clean_no_acc = remove_diacritics(p_clean).lower()
                p_norm = re.sub(r'\s+', '', p_clean_no_acc).replace('kosicky', 'kosiky').replace('kosky', 'kosiky').replace('castecni', 'castecne').replace('stresni', 'castecne')
                
                for h in headings:
                    h_clean_no_acc = remove_diacritics(h).lower()
                    h_norm = re.sub(r'\s+', '', h_clean_no_acc).replace('kosicky', 'kosiky')
                    # Check for close match
                    if h_norm == p_norm or h_norm in p_norm or p_norm in h_norm:
                        matched_heading = h
                        break
            
            if matched_heading:
                # Save previous section if exists
                if current_section:
                    key = get_normalized_key(current_section)
                    target_cat = "podprsenky" if current_section in podprsenky_headings else "kalhotky"
                    cuts_data[target_cat][key] = {
                        "title": current_section,
                        "description": " ".join(current_paragraphs)
                    }
                # Start new section
                current_section = matched_heading
                current_paragraphs = []
            else:
                # If we are in a section, collect text
                if current_section:
                    # Filter out contact info at the end
                    if "Zdroj a poradenství" in p_text or "Lýdie Malchárková" in p_text:
                        continue
                    current_paragraphs.append(p_text)

        # Save last section
        if current_section:
            key = get_normalized_key(current_section)
            target_cat = "podprsenky" if current_section in podprsenky_headings else "kalhotky"
            cuts_data[target_cat][key] = {
                "title": current_section,
                "description": " ".join(current_paragraphs)
            }

        # Cache results to JSON file
        with open(DOCX_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cuts_data, f, ensure_ascii=False, indent=2)
            
        logging.info(f"Z Wordu úspěšně uloženo {len(cuts_data['podprsenky'])} střihů podprsenek a {len(cuts_data['kalhotky'])} střihů kalhotek do cache.")
        return cuts_data

    except Exception as e:
        logging.error(f"Chyba při parsování Word souboru: {e}")
        return {"podprsenky": {}, "kalhotky": {}}

if __name__ == "__main__":
    print("Testování parseru Word (.docx) střihů...")
    data = parse_docx_cuts(force_update=True)
    print("\nNalezené podprsenky:")
    for k, v in data["podprsenky"].items():
        print(f" - {k}: {v['title']} ({len(v['description'])} znaků)")
    print("\nNalezené kalhotky:")
    for k, v in data["kalhotky"].items():
        print(f" - {k}: {v['title']} ({len(v['description'])} znaků)")
