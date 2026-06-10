import urllib.request
import xml.etree.ElementTree as ET
import re

url = "https://www.triola.cz/feed/4/72b922270b116de2b42cd75019b78366af898d0a"

print("Downloading entire feed...")
try:
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    with urllib.request.urlopen(req) as response:
        xml_data = response.read()
        print(f"Downloaded {len(xml_data)} bytes.")
        
        # Parse XML
        root = ET.fromstring(xml_data)
        
        # XML namespace
        # The XML root has xmlns="http://www.w3.org/2005/Atom"
        # and xmlns:g="http://base.google.com/ns/1.0"
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'g': 'http://base.google.com/ns/1.0'
        }
        
        entries = root.findall('atom:entry', ns)
        print(f"Found {len(entries)} entries.")
        
        # Let's inspect some properties
        triola_count = 0
        panache_count = 0
        brands = {}
        
        # Let's see what products match code 28746
        matches = []
        
        for entry in entries:
            title = entry.find('atom:title', ns)
            title_text = title.text if title is not None else ""
            
            brand = entry.find('g:brand', ns)
            brand_text = brand.text if brand is not None else ""
            
            brands[brand_text] = brands.get(brand_text, 0) + 1
            
            # Look for 5 digit number in title
            model_match = re.search(r'\b\d{5}\b', title_text)
            model_code = model_match.group(0) if model_match else None
            
            if model_code == "28746":
                matches.append(title_text)
                
        print("\nBrand statistics:")
        for b, count in brands.items():
            print(f" - {b}: {count}")
            
        print(f"\nFound {len(matches)} matching entries for code '28746':")
        for m in matches[:5]:
            print(f" - {m}")
            
except Exception as e:
    print(f"Error: {e}")
