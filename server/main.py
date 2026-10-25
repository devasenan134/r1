from dotenv import load_dotenv
import os
import httpx

load_dotenv()          

URL = os.getenv("R1_BRAIN_URL")
KEY = os.getenv("R1_BRAIN_KEY")
MODEL = os.getenv("R1_BRAIN_MODEL")

def ask(prompt):
    response = httpx.post(
        f"{URL}/api/generate",
        json={                      # asking our model to not do the reasoning before the response, and num_predict - keeps the response short
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {"num_predict": 64},
        },
        headers={
            "Authorization": f"Bearer {KEY}",
            "User-Agent": "Mozilla/5.0",
        },
        timeout=60.0,
    )
    return response.json()["response"].strip()


print(ask("Introduce yourself in ont short, warm sentence as R1, a desk pet."))