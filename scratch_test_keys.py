import os
from dotenv import load_dotenv
import openai
import anthropic
from google import genai

# Load env variables
load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
google_key = os.getenv("GOOGLE_API_KEY")

print("Checking API Keys...")
print(f"OpenAI key present: {bool(openai_key)}")
print(f"Anthropic key present: {bool(anthropic_key)}")
print(f"Google key present: {bool(google_key)}")

# 1. Test OpenAI
if openai_key:
    print("\n--- Testing OpenAI (GPT-4o) ---")
    try:
        client = openai.OpenAI(api_key=openai_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Use mini for cheap/fast test
            messages=[{"role": "user", "content": "Ahoj, napis jedno slovo: Test"}]
        )
        print("OpenAI Success:", response.choices[0].message.content.strip())
    except Exception as e:
        print("OpenAI Error:", e)

# 2. Test Anthropic
if anthropic_key:
    print("\n--- Testing Anthropic (Listing Models) ---")
    try:
        client = anthropic.Anthropic(api_key=anthropic_key)
        # Use client.models.list()
        models = client.models.list()
        for m in models.data:
            print(f" - ID: {m.id} | Display Name: {m.display_name}")
            
        # Try calling the first model in the list
        if models.data:
            first_model = models.data[0].id
            print(f"Trying a completion with {first_model}...")
            message = client.messages.create(
                model=first_model,
                max_tokens=50,
                messages=[{"role": "user", "content": "Ahoj, napis jedno slovo: Test"}]
            )
            print(f"Anthropic {first_model} Success:", message.content[0].text.strip())
    except Exception as e:
        print("Anthropic List Error:", e)

# 3. Test Google Gemini
if google_key:
    print("\n--- Testing Google Gemini ---")
    try:
        client = genai.Client(api_key=google_key)
        print("Listing available models:")
        for m in client.models.list():
            print(f" - {m.name} (Supported: {m.supported_actions})")
            
        # Try a direct generation with gemini-2.5-flash since 2.5 is the latest
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents='Ahoj, napis jedno slovo: Test',
            )
            print("Google GenAI gemini-2.5-flash Success:", response.text.strip())
        except Exception as ex:
            print("Google GenAI direct generate error:", ex)
    except Exception as e:
        print("Google GenAI Error:", e)
