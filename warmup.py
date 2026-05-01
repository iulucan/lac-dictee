"""
Run before demo to verify OCR and correction engines are ready.
Usage: python3 warmup.py
"""
import os, base64, sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Small white 10x10 PNG generated at runtime
import io
from PIL import Image as _Img
_buf = io.BytesIO()
_Img.new("RGB", (10, 10), (255, 255, 255)).save(_buf, format="PNG")
_PNG_B64 = base64.b64encode(_buf.getvalue()).decode()

print("Checking OCR + correction engines...\n")

# 1. Groq Vision
print("1. Groq Vision (primary OCR)... ", end="", flush=True)
try:
    from groq import Groq
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        max_tokens=5,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "reply ok"},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{_PNG_B64}"
                }},
            ],
        }],
    )
    print("✅ ready")
except Exception as e:
    print(f"❌ {e}")

# 2. Groq text (correction)
print("2. Groq correction engine...     ", end="", flush=True)
try:
    from groq import Groq
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=5,
        messages=[{"role": "user", "content": "ping"}],
    )
    print("✅ ready")
except Exception as e:
    print(f"❌ {e}")

# 3. Claude Vision (optional — needs credits)
print("3. Claude Vision (optional)...   ", end="", flush=True)
try:
    import anthropic
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠️  ANTHROPIC_API_KEY not set — skipped")
    else:
        ac = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        ac.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=5,
            messages=[{"role": "user", "content": "ping"}],
        )
        print("✅ ready")
except anthropic.BadRequestError as e:
    if "credit" in str(e).lower():
        print("⚠️  No credits — Groq Vision will be used instead")
    else:
        print(f"❌ {e}")
except Exception as e:
    print(f"❌ {e}")

print("\nDemo ready. Run: streamlit run app.py")
