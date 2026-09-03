# -*- coding: utf-8 -*-
"""
Jednorázové přihlášení k Disku pod TVÝM účtem (ne pod služebním).

Proč: služební účet umí zakládat složky, ale nemá vlastní úložiště, takže
soubory nahrát nemůže. Nahrávat je proto bude tvůj účet — soubory pak budou
i normálně tvoje a uvidíš je na svém Disku.

Postup (jednou):
  1. V Google Cloud stáhni OAuth klienta typu "Desktop app" a ulož ho sem
     jako  oauth_client.json
  2. Spusť:  python google_oauth_setup.py
  3. Otevře se prohlížeč, potvrdíš přístup ke svému Disku.
  4. Vznikne soubor google_user_token.json — ten pak vlož do GitHub secrets
     jako GOOGLE_USER_TOKEN_JSON (a případně na Render jako Secret File).
"""
import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_FILE = os.path.join(BASE_DIR, "oauth_client.json")
TOKEN_FILE = os.path.join(BASE_DIR, "google_user_token.json")
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if not os.path.exists(CLIENT_FILE):
        print("Chybí oauth_client.json.")
        print("V Google Cloud → APIs & Services → Credentials → Create credentials")
        print("→ OAuth client ID → Desktop app → stáhnout JSON a uložit sem jako:")
        print("  ", CLIENT_FILE)
        sys.exit(1)

    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_FILE, SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent",
                                  authorization_prompt_message="Otevírám prohlížeč pro přihlášení…")
    data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes or SCOPES),
    }
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"\nHotovo. Token uložen do: {TOKEN_FILE}")
    print("Obsah tohoto souboru vlož do GitHub secrets jako GOOGLE_USER_TOKEN_JSON.")
    if not creds.refresh_token:
        print("\nPOZOR: token neobsahuje refresh_token - zopakuj přihlášení, "
              "ať robot funguje i po vypršení platnosti.")


if __name__ == "__main__":
    main()
