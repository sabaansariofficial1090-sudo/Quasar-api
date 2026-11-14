from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import requests
import os

app = FastAPI()

# 🔑 API key Render ke environment se aayegi
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 🔄 FALLBACK CHAIN — high-quota pehle, keemti models baad mein!
GEMINI_MODELS = [
    "gemini-3.5-flash-lite",   # 💎 500/din — MAIN workhorse
    "gemini-3.1-flash-lite",   # 💎 500/din — doosra tank
    "gemini-3.8-flash",        # ⭐ 20/din — best quality
    "gemini-3.6-flash",        # ⭐ 20/din
    "gemini-4-hydrogen",       # 🔥 20/din — naya Gemini 4
    "gemma-4-26b",             # 🛟 14,400/din — LAST RESORT backup
]


def google_se_pucho(question):
    """Ek model busy/quota-khatam ho to agle pe jump 🔄"""
    last_error = None

    for model in GEMINI_MODELS:
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": GEMINI_API_KEY,
                },
                json={"contents": [{"parts": [{"text": question}]}]},
                timeout=20,
            )
            data = r.json()

            if "candidates" in data:  # ✅ Jawab mil gaya!
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text, model, None

            last_error = data  # ❌ Busy — agla model
            print(f"[Quasar] {model} fail hua, agla try kar raha hoon...")

        except requests.exceptions.RequestException as e:
            last_error = {"error": str(e)}
            print(f"[Quasar] {model} network fail, agla try...")

    return None, None, last_error  # 😢 sab busy


@app.get("/")
def home():
    return {"status": "Quasar API zinda hai 🚀"}


@app.get("/ask")
def ask(q: str = Query("")):
    if not q:
        return JSONResponse({"error": "Question bhejo! ?q=... use karo"})

    jawab, model, err = google_se_pucho(q)

    if jawab:
        return {"question": q, "answer": jawab, "model": model}

    return JSONResponse({
        "error": "'candidates'",
        "google_ka_jawab": str(err),
        "message": "Sab models busy hain 😅 Thodi der baad try karo!"
    })
