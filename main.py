from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

app = FastAPI()

# 🌍 CORS — GitHub Pages se API call allow karne ke liye
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

GEMINI_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-4-hydrogen",
    "gemma-4-26b",
]


def google_se_pucho(question):
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
            if "candidates" in data:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text, model, None
            last_error = data
            print(f"[Quasar] {model} fail, agla try...")
        except requests.exceptions.RequestException as e:
            last_error = {"error": str(e)}
            print(f"[Quasar] {model} network fail, agla try...")
    return None, None, last_error


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
        "error": "sab busy",
        "google_ka_jawab": str(err),
        "message": "Sab models busy hain 😅 Thodi der baad try karo!"
    })        
