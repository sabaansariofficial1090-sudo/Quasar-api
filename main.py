import os
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="Quasar API")

# Homepage ko backend call karne ki permission
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password code mein NAHI — Render ke Environment se aayega (safe!)
DATABASE_URL = os.environ.get("DATABASE_URL")


@app.get("/")
def home():
    return {"status": "Quasar API zinda hai 🚀"}


@app.get("/db-test")
def db_test():
    """Neon database se connection test"""
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = sorted(r["table_name"] for r in cur.fetchall())
        cur.close()
        conn.close()
        return {"connected": True, "tables": tables}
    except Exception as e:
        return {"connected": False, "error": str(e)}
# ============ QUASAR KA DIMAAG (AI BRAIN) 🧠 ============

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.8-flash"     

QUASAR_PERSONA = (
    "Tum 'Quasar' ho - ek smart aur friendly AI business assistant. "
    "Har jawab simple, chhota aur clear do."
)

@app.get("/ask")
def ask(q: str):
    if not GEMINI_API_KEY:
        return {"error": "GEMINI_API_KEY missing - Render env vars check karo"}
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        headers = {"x-goog-api-key": GEMINI_API_KEY}
        prompt = QUASAR_PERSONA + "\n\nCustomer ka sawaal: " + q
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        data = r.json()
        answer = data["candidates"][0]["content"]["parts"][0]["text"]
        return {"question": q, "answer": answer}
    except Exception as e:
                return {"error": str(e), "google_ka_jawab": str(locals().get("data", "n/a"))}
