
import os
import google.generativeai as genai

# Manually load from config.env
api_key = None
with open("config.env", "r") as f:
    for line in f:
        if line.startswith("GEMINI_API_KEY="):
            api_key = line.split("=", 1)[1].strip()

if api_key:
    genai.configure(api_key=api_key)
    print("ALL MODELS:")
    for m in genai.list_models():
        print(f"- {m.name} (Methods: {m.supported_generation_methods})")
else:
    print("No API Key")
