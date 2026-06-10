import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Verify dependencies
try:
    import flask
    import requests
    import openai
    import anthropic
    from google import genai
except ImportError as e:
    print(f"Chyba: Chybějící závislost '{e.name}'. Nainstalujte závislosti příkazem: pip install -r requirements.txt")
    sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("      SPOUŠTĚNÍ ASISTENTA AI COPYWRITING PRO TRIOLA.CZ")
    print("=" * 60)
    print("Aplikace bude spuštěna na adrese: http://127.0.0.1:5000")
    print("Ukončení serveru provedete stisknutím CTRL+C")
    print("-" * 60)
    
    from app import app
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
