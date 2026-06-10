import urllib.request
import xml.etree.ElementTree as ET
import sys

url = "https://www.triola.cz/feed/4/72b922270b116de2b42cd75019b78366af898d0a"

print("Downloading feed header...")
try:
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    with urllib.request.urlopen(req) as response:
        # Read first 50KB to check the structure
        chunk = response.read(50000)
        print("Downloaded 50KB.")
        # Let's write this chunk to a file to inspect it
        with open("scratch_feed_chunk.xml", "wb") as f:
            f.write(chunk)
        print("Saved chunk to scratch_feed_chunk.xml")
except Exception as e:
    print(f"Error: {e}")
