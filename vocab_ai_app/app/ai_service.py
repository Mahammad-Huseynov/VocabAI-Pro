import os
import json
from google import genai
from google.genai import types
from groq import Groq
from dotenv import load_dotenv

# .env faylındakı dəyişənləri RAM-a yükləyirik
load_dotenv()

# API açarlarını birbaşa .env-dən təhlükəsiz şəkildə çəkirik
GEMINI_REAL_KEY = os.getenv("GEMINI_API_KEY")
GROQ_REAL_KEY = os.getenv("GROQ_API_KEY")

# ----------------- API QOŞULMALARI -----------------
client_gemini = None
if GEMINI_REAL_KEY:
    try:
        client_gemini = genai.Client(api_key=GEMINI_REAL_KEY)
        print("🚀 Gemini API .env üzərindən işə salındı.")
    except Exception as e:
        print(f"⚠️ Gemini işə salınma xətası: {e}")

client_groq = None
if GROQ_REAL_KEY:
    try:
        client_groq = Groq(api_key=GROQ_REAL_KEY)
        print("🛡️ Groq API .env üzərindən işə salındı.")
    except Exception as e:
        print(f"⚠️ Groq işə salınma xətası: {e}")


def generate_words_by_path(category: str, level: str) -> list:
    prompt = f"""
    You are an expert English teacher specializing in professional terminology and CEFR language levels.
    Generate exactly 5 distinct, practical English words suitable for the category '{category}' and language level '{level}'.

    CRITICAL OUTPUT FORMAT REQUIREMENTS:
    Return STRICTLY a JSON object with a single root key 'words' containing an array of 5 objects.
    
    Each object MUST have exactly these keys with these specific contents:
    1. 'word': The English word itself.
    2. 'meaning': A clear, short English definition/explanation of the word.
    3. 'translation': The direct, accurate Azerbaijani translation of the word.
    4. 'context': An English example sentence using the word, perfectly matching the '{level}' level grammar.

    Do not wrap the response in markdown blocks or write conversational text. Just raw JSON string.

    CRITICAL TRANSLATION & CEFR RULES:
    1. Technical & Domain Accuracy: Use professional Azerbaijani IT/Cybersecurity terms for the 'translation' field.
       - 'network' -> 'şəbəkə', 'firewall' -> 'təhlükəsizlik divarı', 'log' -> 'loq / qeyd dəftəri', 'salt' -> 'duzlama / xəşə əlavə məlumat qatma'.
    2. Clean Values: No prefixes like "azərbaycanca - " or "Tərcümə: " in the fields.
    3. Strict Level Matching: The 'context' sentence MUST perfectly match the '{level}' level grammar.
    """
    if client_gemini:
        try:
            response = client_gemini.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            data = json.loads(response.text)
            if "words" in data and len(data["words"]) > 0:
                return data["words"]
        except Exception as e:
            print(f"❌ Gemini Word Generation Xətası: {e}")

    if client_groq:
        try:
            completion = client_groq.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            data = json.loads(completion.choices[0].message.content)
            if "words" in data and len(data["words"]) > 0:
                return data["words"]
        except Exception as e:
            print(f"❌ Groq Word Generation Xətası: {e}")
            
    return []


def generate_story_from_words(words_list: list, level: str):
    if not words_list:
        return {"story": []}

    prompt = f"""
    You are an expert English teacher and professional translator.
    Generate exactly ONE distinct, clear sentence for each English word in this list: {", ".join(words_list)}.
    The grammatical complexity MUST strictly match the '{level}' CEFR proficiency level.
    
    CRITICAL AZERBAIJANI TRANSLATION RULES (STRICT QUALITY CONTROL):
    1. NEVER translate literally. The Azerbaijani translation MUST sound natural, smooth, and idiomatic to a native speaker.
    2. Use correct IT/Cybersecurity terminology:
       - 'computer got infected with malware' -> 'kompüter ziyankar proqram təminatına (malware) yoluxub' (NEVER use 'bulaqlanıb' or 'yoluxdurulub var').
       - 'hacker tries to break into/attack' -> 'haker kompüterə/sistemə sızmağa çalışır' (NEVER use 'basdırığı var' or 'qırmağa çalışır').
       - 'bad software / malicious software' -> 'ziyankar proqram'.
       - 'keep me safe' -> 'məni qoruyur' (NEVER use 'mənimə xasdırki').
       - 'secret word' -> 'şifrə / parol'.
    
    CRITICAL OUTPUT FORMAT REQUIREMENTS:
    Return STRICTLY a JSON object with a single root key 'story' containing an array of objects.
    Each object MUST have exactly these keys: 'eng' and 'aze'.
    Do not use markdown blocks. Just raw JSON string.
    """
    
    if client_gemini:
        try:
            response = client_gemini.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            data = json.loads(response.text)
            if "story" in data:
                return data
        except Exception as e:
            print(f"❌ Gemini Story Generation Xətası: {e}")

    if client_groq:
        try:
            completion = client_groq.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            data = json.loads(completion.choices[0].message.content)
            if "story" in data:
                return data
        except Exception as e:
            print(f"❌ Groq Story Generation Xətası: {e}")

    return {"story": [{"eng": f"Studying {w}.", "aze": f"{w} sözünü öyrənirəm."} for w in words_list]}