import urllib.request
import openpyxl
import os

sheet_id = "1WO2WWAQrgb2PvpHkokl4r6TpWEI36mCC"
download_url = f"https://drive.google.com/uc?export=download&id={sheet_id}"
output_file = "triola_marketing_data.xlsx"

print(f"Downloading sheet from {download_url}...")
try:
    req = urllib.request.Request(
        download_url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    with urllib.request.urlopen(req) as response:
        with open(output_file, "wb") as f:
            f.write(response.read())
    print("Download completed successfully!")
    
    # Load sheet names
    wb = openpyxl.load_workbook(output_file, read_only=True)
    print("\nAvailable Sheets:")
    for name in wb.sheetnames:
        print(f" - {name}")
        
except Exception as e:
    print(f"Error: {e}")
