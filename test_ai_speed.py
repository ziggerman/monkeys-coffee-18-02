
import os
import asyncio
import google.generativeai as genai
import time

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

    genai.configure(api_key=api_key)
    
    models = ['models/gemini-2.0-flash-lite', 'models/gemini-2.0-flash']
    
    for model_name in models:
        print(f"\n--- Testing {model_name} ---")
        try:
            model = genai.GenerativeModel(model_name)
            prompt = """
Ти — копірайтер бренду "MONKEYS COFFEE ROASTERS". Твій стиль: зухвалий, енергійний, професійний, але з гуримом (🐒🔥).
Напиши логічний (1-2 речення) та вибуховий опис для нової кави:
- Назва: Ethiopia Yirgacheffe
- Походження: Yirgacheffe
- Нотки: Жасмин, бобер, чорний чай
🔥 <b>Ethiopia Yirgacheffe</b>. Опис...
💡 Порада: ...
"""
            start_time = time.time()
            response = await model.generate_content_async(prompt)
            end_time = time.time()
            
            print(f"Time: {end_time - start_time:.2f}s")
            print(f"Response: {response.text[:100]}...")
            
        except Exception as e:
            print(f"Error with {model_name}: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai())
