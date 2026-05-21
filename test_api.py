import urllib.request
import json

API_KEY = "AIzaSyCRvz0bGRhieEEFqDm-klcOHtm-THtjb3s"

MODEL   = "gemma-4-26b-a4b-it"
URL     = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

PROMPT = """You are a JSON API. Output ONLY a JSON object, nothing else.

Evaluate this student answer about photosynthesis:
"Photosynthesis is process where plants make food using sunlight water and CO2"

Output ONLY this JSON (fill in the values):
{"subject":"Science","question_detected":"photosynthesis","score":7,"max_score":10,"grade":"A","hindi_feedback":"अच्छा उत्तर है।","english_feedback":"Good answer.","mistakes":["incomplete"],"correct_points":["correct process"],"improvement_tips":["add more detail"],"model_answer_hint":"include light and dark reactions","confidence":"high"}"""

payload = {
    "contents": [{"parts": [{"text": PROMPT}]}],
    "generationConfig": {"maxOutputTokens": 300, "temperature": 0.0}
}

data = json.dumps(payload).encode("utf-8")
req  = urllib.request.Request(
    URL, data=data,
    headers={"Content-Type": "application/json", "x-goog-api-key": API_KEY},
    method="POST"
)

print("Calling API... (may take 30-60 seconds)")
try:
    with urllib.request.urlopen(req, timeout=90) as r:
        res  = json.loads(r.read())
        text = res["candidates"][0]["content"]["parts"][0]["text"]
        print("RESPONSE:")
        print(text)
except urllib.error.HTTPError as e:
    print(f"HTTP ERROR {e.code}: {e.read().decode()[:200]}")
except Exception as e:
    print(f"ERROR: {e}")