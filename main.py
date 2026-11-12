import os
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
