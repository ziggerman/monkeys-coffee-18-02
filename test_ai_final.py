
import os
import asyncio
import google.generativeai as genai

async def test_ai():
    # Manually load from config.env
    api_key = None
    with open("config.env", "r") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
    
    if not api_key:
        print("GEMINI_API_KEY not found in config.env")
        return

    print(f"Testing with API Key: {api_key[:10]}...")
    genai.configure(api_key=api_key)
    
    # Try generating with models/gemini-pro-latest
    model_name = 'models/gemini-pro-latest'
    print(f"\nTrying to generate with {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Напиши короткий опис кави Бразилія Сантос.")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error with {model_name}: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai())
