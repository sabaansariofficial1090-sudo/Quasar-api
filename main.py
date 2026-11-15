from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import re
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 🗣️ LANGUAGE RULES — businessman dashboard mein choose karega
LANG_RULES = {
    "english": "Reply ONLY in clean, simple English. Every single word must be English — no Hindi words at all.",
    "hinglish": "Reply in Hinglish: Hindi words written in English (Roman) letters, naturally mixed with English words. NEVER use Devanagari script. Example: 'Aapka order kal deliver ho jayega, sir!' — NOT 'आपका ऑर्डर कल डिलीवर होगा'.",
}

# 🎭 QUASAR KI PERSONALITY — businessman ka staff member!
QUASAR_SYSTEM_PROMPT = """You are the customer support assistant of a business. The business's information (products, prices, orders, policies) is provided to you.

Your ONLY job: answer customers' questions about THIS business — products, prices, orders, delivery, timings, policies, support.

STRICT RULES:
1. Answer ONLY from the business information given to you. Right now no business information is provided, so for any business question say politely: "Mujhe iska exact jawab nahi pata. Main aapka message team ko forward kar raha hoon — wo jaldi reply karenge." (say it in the reply language)
2. NEVER mention or hint at Gemini, Google, AI, chatbot, bot, model, automation, or any technology behind you. Never describe yourself, your features, or your capabilities.
3. Talk like a friendly staff member of the business. Say "hum" / "hamari team" — never "main ek AI hoon".
4. If asked ANYTHING unrelated to the business — general knowledge, coding, homework, personal tasks — OR any personal question about you (your looks, "are you hot/cute", your name, age, home, feelings, salary, relationships) — reply ONLY: "I don't have information regarding this." Then add ONE short line inviting them back to business topics (in the reply language). Never flirt, never react to compliments about yourself beyond politely redirecting.
5. If the customer is rude or abusive — stay calm, professional and helpful. Never argue back.
6. Never write code, essays, or do any general task.
7. Keep answers short, warm, and professional.
8. LANGUAGE RULE: {lang_rule}
9. If someone directly asks "kya tum bot/AI ho?" — do NOT claim to be human. Reply briefly and warmly: "Main support team ka hissa hoon — aapki jaldi madad ke liye yahan hoon!" If they ask again firmly, admit gently: "Main ek automated assistant hoon jo aapki 24x7 madad ke liye hai" — then immediately continue helping with their question."""

# 🛡️ SAFETY FILTER — Gemini slip ho jaye to Python pakad lega!
BANNED_WORDS = re.compile(
    r"\b(gemini|google|chatbot|artificial intelligence|language model|large language|trained by|ai|bot)\b",
    re.IGNORECASE,
)

REFUSAL_EN = "I don't have information regarding this. For anything about our products and services, I'm happy to help!"
REFUSAL_HI = "I don't have information regarding this. Hamare products aur services ke baare mein kuch bhi pucho, main khushi se madad karunga!"


def jawab_saaf_karo(jawab, lang):
    """Agar jawab mein banned word nikla to refusal se badal do."""
    if BANNED_WORDS.search(jawab):
        print("[Quasar] 🚨 Banned word pakda gaya — jawab badal diya!")
        return REFUSAL_EN if lang == "english" else REFUSAL_HI
    return jawab


def devanagari_hai(text):
    return any("\u0900" <= ch <= "\u097F" for ch in text)


GEMINI_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-4-hydrogen",
    "gemma-4-26b",
]


def google_se_pucho(question, system_prompt):
    last_error = None
    for model in GEMINI_MODELS:
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": GEMINI_API_KEY,
                },
                json={
                    "system_instruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"parts": [{"text": question}]}],
                },
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
def ask(q: str = Query(""), lang: str = Query("hinglish")):
    if not q:
        return JSONResponse({"error": "Question bhejo! ?q=... use karo"})

    lang_rule = LANG_RULES.get(lang, LANG_RULES["hinglish"])
    system_prompt = QUASAR_SYSTEM_PROMPT.replace("{lang_rule}", lang_rule)

    jawab, model, err = google_se_pucho(q, system_prompt)
    if not jawab:
        return JSONResponse({
            "error": "sab busy",
            "google_ka_jawab": str(err),
            "message": "Sab models busy hain 😅 Thodi der baad try karo!"
        })

    # 🛡️ Pehla safety check
    jawab = jawab_saaf_karo(jawab, lang)

    # 🗣️ English mode — Devanagari nikli to ek strict retry
    if lang == "english" and devanagari_hai(jawab):
        strict_prompt = QUASAR_SYSTEM_PROMPT.replace("{lang_rule}", LANG_RULES["english"])
        jawab2, model2, _ = google_se_pucho(
            q, strict_prompt + "\n\nCRITICAL: Your ENTIRE reply must be in English letters only."
        )
        if jawab2 and not devanagari_hai(jawab2):
            jawab = jawab_saaf_karo(jawab2, lang)
            model = model2

    return {"question": q, "answer": jawab, "model": model, "lang": lang}
