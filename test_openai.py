
import asyncio
from openai import AsyncOpenAI

async def test_openai():
    api_key = None
    with open("config.env", "r") as f:
        for line in f:
            if line.startswith("OPENAI_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
    
    if not api_key:
        print("OPENAI_API_KEY not found in config.env")
        return

    print(f"Testing with OpenAI API Key: {api_key[:10]}...")
    client = AsyncOpenAI(api_key=api_key)
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Напиши короткий опис кави Бразилія Сантос."}],
            max_tokens=100
        )
        print(f"Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"Error with OpenAI: {e}")

if __name__ == "__main__":
    asyncio.run(test_openai())
