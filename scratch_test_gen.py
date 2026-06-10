import logging
from ai_service import generate_copywriting
from feed_parser import build_and_cache_products, search_products

# Configure logging
logging.basicConfig(level=logging.INFO)

print("Loading cached products...")
db = build_and_cache_products()

# Search for the bra model 28746
matches = search_products("28746", db)
if not matches:
    print("Product 28746 not found!")
    exit(1)

product = matches[0]
print(f"Found product: {product['generic_title']} ({product['model_code']})")

print("\n--- Testing Generation via OpenAI (gpt-4o-mini) ---")
try:
    copy = generate_copywriting(
        product_info=product,
        format_type="popisek",
        model_key="gpt-4o-mini",
        tone_key="empaticky",
        length_key="kratky",
        keywords="luxusní, bezchybná podpora",
        custom_instructions="Zdůrazni, že je skvělá pro horké letní dny."
    )
    print("OpenAI Copy Successful! Preview:")
    print("=" * 40)
    print(copy[:400] + "...")
    print("=" * 40)
except Exception as e:
    print("OpenAI Gen Error:", e)

print("\n--- Testing Generation via Anthropic (claude-sonnet-4-6) ---")
try:
    copy = generate_copywriting(
        product_info=product,
        format_type="socialni_site",
        model_key="claude-sonnet-4-6",
        tone_key="empaticky",
        length_key="kratky"
    )
    print("Anthropic Copy Successful! Preview:")
    print("=" * 40)
    print(copy[:400] + "...")
    print("=" * 40)
except Exception as e:
    print("Anthropic Gen Error:", e)

print("\n--- Testing Generation via Google Gemini (gemini-2.5-flash) ---")
try:
    copy = generate_copywriting(
        product_info=product,
        format_type="popisek",
        model_key="gemini-2.5-flash",
        tone_key="empaticky",
        length_key="kratky"
    )
    print("Google Gemini Copy Successful! Preview:")
    print("=" * 40)
    print(copy[:400] + "...")
    print("=" * 40)
except Exception as e:
    print("Gemini Gen Error:", e)
