import zipfile
import xml.etree.ElementTree as ET
import re

z = zipfile.ZipFile('Typy podprsenek a kalhotek.docx')
doc_xml = z.read('word/document.xml')
root = ET.fromstring(doc_xml)
namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
paragraphs = root.findall('.//w:p', namespaces)

raw = [''.join(node.text for node in p.iter() if node.text is not None).strip() for p in paragraphs if any(node.text for node in p.iter() if node.text is not None)]

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

def remove_diacritics(text):
    accent_map = {
        'á': 'a', 'č': 'c', 'ď': 'd', 'é': 'e', 'ě': 'e', 'í': 'i', 'ň': 'n',
        'ó': 'o', 'ř': 'r', 'š': 's', 'ť': 't', 'ú': 'u', 'ů': 'u', 'ý': 'y', 'ž': 'z',
        'Á': 'a', 'Č': 'c', 'Ď': 'd', 'É': 'e', 'Ě': 'e', 'Í': 'i', 'Ň': 'n',
        'Ó': 'o', 'Ř': 'r', 'Š': 's', 'Ť': 't', 'Ú': 'u', 'Ů': 'u', 'Ý': 'y', 'Ž': 'z'
    }
    return "".join(accent_map.get(c, c) for c in text)

def clean(text):
    # Remove layout prefixes and suffixes
    t = re.sub(r'(left\d*|right\d*|righttop|lefttop|left|right)', '', text, flags=re.IGNORECASE)
    # Remove any non-alphabetic characters (except spaces) - handles quotes, dashes, digits
    t = re.sub(r'[^a-zA-Zá-žÁ-ŽČŠŽÍěščřžýáíéóúůďťňĎŤŇ\s]', '', t)
    # Normalize spaces
    return re.sub(r'\s+', ' ', t).strip()

print("Original text -> Cleaned -> Match")
print("=" * 60)
matches_count = 0
for idx, p in enumerate(raw):
    cleaned = clean(p)
    if not cleaned:
        continue
    
    # We check if it is a heading
    if len(cleaned) < 80:
        matched = None
        # Normalize and remove accents
        p_clean_no_acc = remove_diacritics(cleaned).lower()
        p_norm = re.sub(r'\s+', '', p_clean_no_acc).replace('kosicky', 'kosiky').replace('kosky', 'kosiky').replace('castecni', 'castecne').replace('stresni', 'castecne')
        
        for h in headings:
            h_clean_no_acc = remove_diacritics(h).lower()
            h_norm = re.sub(r'\s+', '', h_clean_no_acc).replace('kosicky', 'kosiky')
            # Check for close match
            if h_norm == p_norm or h_norm in p_norm or p_norm in h_norm:
                matched = h
                break
        
        if matched:
            print(f"MATCH: {p[:30]}... -> {cleaned} -> {matched}")
            matches_count += 1
        
        if matched:
            print(f"MATCH: {p[:30]}... -> {cleaned} -> {matched}")
            matches_count += 1

print("Total matches found:", matches_count)
