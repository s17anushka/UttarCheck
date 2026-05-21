<div align="center">

```
██╗   ██╗████████╗████████╗ █████╗ ██████╗  ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗
██║   ██║╚══██╔══╝╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝
██║   ██║   ██║      ██║   ███████║██████╔╝██║     ███████║█████╗  ██║     █████╔╝ 
██║   ██║   ██║      ██║   ██╔══██║██╔══██╗██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ 
╚██████╔╝   ██║      ██║   ██║  ██║██║  ██║╚██████╗██║  ██║███████╗╚██████╗██║  ██╗
 ╚═════╝    ╚═╝      ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝
```

**AI-Powered Handwritten Answer Evaluator for Indian Students**

*Built for the [Gemma 4 Challenge](https://dev.to/challenges/gemma) on DEV.to*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Gemma](https://img.shields.io/badge/Gemma_4-26B_MoE-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## The Problem

India has **250 million school students**. Most write handwritten answers for board exams — CBSE, UP Board, ICSE. Getting feedback means waiting days for a teacher.

**UttarCheck changes that.**

Photograph your handwritten answer. Get instant AI evaluation — score, mistakes, improvement tips — in **Hindi and English**. Powered by Gemma 4 running multimodal vision inference.

---

## Demo

```
Student photographs answer sheet
           ↓
    UttarCheck processes image
           ↓
  Gemma 4 reads handwriting
           ↓
  ┌─────────────────────────┐
  │  Score: 9/10  Grade: A+ │
  │  Subject: Science       │
  │                         │
  │  ✅ Correct Points      │
  │  • Accurate definition  │
  │  • Correct equation     │
  │                         │
  │  ❌ Mistakes            │
  │  • Minor grammar error  │
  │                         │
  │  💡 Tips                │
  │  • Add Calvin cycle     │
  └─────────────────────────┘
  Hindi + English feedback
```

---

## Why Gemma 4

| Requirement | Why Gemma 4 |
|---|---|
| Read handwritten text | Native multimodal vision |
| Hindi feedback | Strong multilingual capability |
| Fast inference | `gemma-4-26b-a4b-it` MoE — efficient architecture |
| Edge-ready future | E2B/E4B variants run on Android phones |
| No data leakage | Designed for local/offline deployment |

Specifically chose `gemma-4-26b-a4b-it` (Mixture-of-Experts) — activates only 4B parameters per inference, delivering Gemma 4 quality at fraction of compute cost. Perfect for high-throughput educational deployments.

---

## Architecture

```
Browser / Phone
      │
      │  POST /evaluate
      │  (image + question + subject)
      ▼
┌─────────────────────────────────────────────────┐
│                   Flask App                      │
│                                                  │
│  rate_limiter ──► validators ──► image_service   │
│       │               │               │          │
│  IP throttle    magic bytes      PIL resize +    │
│  10 req/min     MIME verify      contrast boost  │
│                 size cap         base64 encode   │
│                                       │          │
│                              evaluation_service  │
│                                       │          │
│                              prompt + sanitize   │
│                                       │          │
│                              gemma_service       │
│                                       │          │
│                         Google AI Studio API     │
│                         gemma-4-26b-a4b-it       │
│                                       │          │
│                              parsers (6 strats)  │
│                                       │          │
│                              EvaluationResult    │
└─────────────────────────────────────────────────┘
      │
      │  JSON response
      ▼
   UI renders score, feedback, mistakes, tips
```

### Request Flow

```
1. File upload        → magic byte verification (not just MIME)
2. Image received     → PIL resize to 1024px + contrast enhance
3. Prompt built       → system prompt from .txt file + user context
4. Gemma called       → multimodal: image_b64 + text prompt
5. Response parsed    → 6-strategy JSON extractor (Gemma 4 returns prose+JSON)
6. Result typed       → EvaluationResult dataclass → JSON response
7. UI renders         → score, grade, Hindi+English feedback, lists
```

---

## Project Structure

```
uttarcheck/
│
├── run.py                          # Dev entry point
├── config.py                       # All settings — env-aware
├── .env                            # Secrets (never commit)
├── requirements.txt
│
└── app/
    ├── __init__.py                 # Flask app factory
    │
    ├── routes/
    │   ├── evaluate.py             # POST /evaluate — HTTP only
    │   └── health.py               # GET /health
    │
    ├── services/
    │   ├── evaluation_service.py   # Pipeline orchestrator
    │   ├── gemma_service.py        # Google AI + Ollama backends
    │   └── image_service.py        # PIL preprocessing
    │
    ├── utils/
    │   ├── validators.py           # Secure file validation
    │   ├── parsers.py              # 6-strategy JSON extractor
    │   ├── security.py             # Prompt injection defense
    │   ├── rate_limiter.py         # Sliding window per IP
    │   └── error_handlers.py       # Global HTTP error responses
    │
    ├── prompts/
    │   └── evaluation_prompt.txt   # System prompt — outside code
    │
    └── templates/
        └── index.html              # Mobile-first dark UI
```

---

## Security

| Threat | Defense |
|---|---|
| File format spoofing | Magic byte verification — not just extension |
| Oversized uploads | 8MB hard cap + PIL dimension check |
| Corrupt images | PIL `verify()` before processing |
| Prompt injection | Regex pattern matching on user inputs |
| XSS | `html.escape()` on all user text |
| API abuse | Sliding window rate limiter (10 req/min per IP) |
| Secret exposure | `.env` + `.gitignore` — keys never in code |
| Large payloads | PIL resize to 1024px before sending to API |

---

## Setup

### Requirements

```
Python 3.11+
pip install flask Pillow
```

### Get API Key

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with Google account
3. Click **Get API Key** → **Create API Key**
4. Copy the key

### Configure

```bash
# .env
GEMMA_API_KEY=your_key_here
MODEL_NAME=gemma-4-26b-a4b-it
USE_PILLOW=true
FLASK_ENV=development
```

### Run

```bash
git clone https://github.com/yourusername/uttarcheck
cd uttarcheck
pip install flask Pillow
python run.py
```

```
======================================================
  UttarCheck — Running!
======================================================
  Laptop : http://localhost:5000
  Phone  : http://192.168.x.x:5000   ← same WiFi
  Health : http://localhost:5000/health
======================================================
```

### Mobile Access

Open `http://[your-laptop-ip]:5000` in your phone browser on the same WiFi. Camera capture works natively.

---

## API Reference

### `POST /evaluate`

**Request** — `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `image` | file | ✅ | JPEG/PNG/WEBP/GIF, max 8MB |
| `question` | string | ❌ | The exam question (max 500 chars) |
| `subject` | string | ❌ | Math / Science / Hindi / English / SST |

**Response 200**

```json
{
  "success": true,
  "subject": "Science",
  "question_detected": "Explain photosynthesis",
  "score": 9,
  "max_score": 10,
  "grade": "A+",
  "hindi_feedback": "आपका उत्तर बहुत विस्तृत और सटीक है।",
  "english_feedback": "Excellent and comprehensive answer.",
  "mistakes": ["Minor grammar: 'consist' should be 'consists'"],
  "correct_points": ["Correct definition", "Right equation", "Good diagram"],
  "improvement_tips": ["Add Calvin cycle name", "Include chemical equation"],
  "model_answer_hint": "Perfect answer includes equation + light/dark reactions",
  "confidence": "high"
}
```

**Response 422** — Validation failed

```json
{ "success": false, "error": "File too large. Max 8 MB." }
```

**Response 429** — Rate limited

```json
{ "success": false, "error": "Too many requests. Wait 1 minute." }
```

### `GET /health`

```json
{
  "status": "ok",
  "api_key_set": true,
  "model": "gemma-4-26b-a4b-it",
  "backend": "google",
  "pillow": true
}
```

---

## Parser — How It Handles Gemma 4's Output

Gemma 4 doesn't always return pure JSON. It reasons through the evaluation first, then outputs JSON inside ` ```json ``` ` blocks. The parser handles this with 6 strategies in order:

```python
1. Extract ```json ... ``` fenced block   ← Gemma 4's actual format
2. Direct JSON parse
3. Find block containing "score" key
4. Find largest { ... } block
5. Fix trailing commas, retry
6. Extract fields from bullet-point prose
```

If all strategies fail, a safe fallback result is returned — the app never crashes.

---

## Future Roadmap

### Phase 2 — Local Inference (Privacy-First)
```bash
# Switch to fully offline inference
INFERENCE_BACKEND=ollama
OLLAMA_MODEL=gemma3:4b

# Zero data leaves device
ollama serve
python run.py
```
`gemma_service.py` already has Ollama backend wired in.

### Phase 3 — Edge Deployment
When `gemma-4-e4b-it` becomes available via Google AI Edge Gallery API:
- Deploy on Android phones
- Fully offline — no server needed
- Student data never leaves device
- Works in areas with no internet

### Phase 4 — OCR Pipeline
```
image → Tesseract OCR → extracted text → Gemma evaluation
```
Preprocessing already in `image_service.py`. OCR layer is the next addition.

### Phase 5 — Scale
```
Flask → FastAPI (async)
In-memory rate limiter → Redis + Flask-Limiter
SQLite → PostgreSQL (evaluation history)
Single server → Docker + Gunicorn + Nginx
```

---

## Built With

- **[Gemma 4](https://ai.google.dev/gemma)** — Google's open multimodal model
- **[Google AI Studio](https://aistudio.google.com)** — Free API access
- **[Flask](https://flask.palletsprojects.com)** — Python web framework
- **[Pillow](https://python-pillow.org)** — Image preprocessing

---

## The Story

Built in Meerut, Uttar Pradesh — where millions of students prepare for UP Board and CBSE exams, often without access to instant teacher feedback. UttarCheck is designed for them.

*"Every student deserves a personal tutor available at 3am before their board exam."*

---

<div align="center">

**Made for the [Gemma 4 Challenge](https://dev.to/challenges/gemma) · DEV.to · May 2026**

*Built with Gemma 4 · Flask · Python · Pillow*

</div>