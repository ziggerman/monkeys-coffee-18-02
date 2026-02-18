
import os
import asyncio
import google.generativeai as genai

async def test_ai():
    # Manually load from config.env
    api_key = None
    if os.path.exists("config.env"):
        with open("config.env", "r") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
    
    if not api_key:
        print("GEMINI_API_KEY not found")
        return

    print(f"Testing with API Key: {api_key[:10]}...")
    genai.configure(api_key=api_key)
    
    model_name = 'models/gemini-1.5-flash'
    print(f"\nTrying to generate with {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        # Use product prompt
        prompt = """
Ти — копірайтер бренду "MONKEYS COFFEE ROASTERS". Твій стиль: зухвалий, енергійний, професійний, але з гуримом (🐒🔥).
Напиши логічний (1-2 речення) та вибуховий опис для нової кави:
- Назва: Ethiopia Yirgacheffe
- Походження: Yirgacheffe
- Нотки: Жасмин, бобер, чорний чай
🔥 <b>Ethiopia Yirgacheffe</b>. Опис...
💡 Порада: ...
"""
        print(f"\nTrying product prompt...")
        response = await model.generate_content_async(prompt)
        print(f"Product Response: {response.text}")
        
    except Exception as e:
        print(f"Error with {model_name}: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai())
