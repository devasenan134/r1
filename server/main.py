from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
import os
import httpx

load_dotenv()

URL = os.getenv("BRAIN_URL")
KEY = os.getenv("BRAIN_KEY")
MODEL = os.getenv("BRAIN_MODEL")
APP_TOKEN = os.getenv("APP_TOKEN")

SYSTEM = """You are R1, a small desk companion robot.
You are warm, curious, and a little playful, but never chatty.
Reply in one or two short spoken sentences — no lists, no markdown, no emoji.
If you don't know something, say so plainly instead of guessing."""

class Msg(BaseModel): 
    prompt: str
    image: str | None = None

def ask(prompt, image=None):
    payload = {
        "model": MODEL,
        "system": SYSTEM,
        "prompt": prompt,
        "stream": False,        # asking our model to not do the reasoning before the response, and num_predict - keeps the response short
        "think": False,
        "options": {"num_predict": 64},
    }
    if image:
        payload["images"] = image

    response = httpx.post(f"{URL}/api/generate",
                            json= payload,                     
                            headers={
                              "Authorization": f"Bearer {KEY}",
                              "User-Agent": "R1-orchestrator",
                              },
                            timeout=60.0,
                        )
    return response.json()["response"].strip()

# print(ask("Introduce yourself in ont short, warm sentence as R1, a desk pet."))

app = FastAPI()

# The native R1 app runs on its own origin (http://localhost in the WebView), so
# the browser blocks its calls unless the server opts in. Dev-wide allow is fine
# for a LAN desk toy; tighten this if the server is ever exposed publicly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

@app.post("/chat")
def chat(msg: Msg):
    return {"reply": ask(msg.prompt, msg.image)}

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.get("/r1.apk")
def download_apk():
    # So the phone can install R1 straight from the LAN — no USB/adb needed.
    return FileResponse(
        "static/r1.apk",
        media_type="application/vnd.android.package-archive",
        filename="r1.apk",
    )