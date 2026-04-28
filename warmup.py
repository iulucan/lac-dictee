"""
Run before demo to wake up the Infinity-Parser HuggingFace Space.
Usage: python3 warmup.py
"""
import sys
from pathlib import Path

print("Warming up Infinity-Parser... (takes ~30s on cold start)")

try:
    from gradio_client import Client, handle_file
    import tempfile, urllib.request

    # Tiny 1x1 white PNG — just enough to wake the Space
    PNG = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdc"
        b"\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(PNG)
        tmp = f.name

    client = Client("infly/infinity-parser", verbose=False)
    client.predict(
        doc_path=handle_file(tmp),
        prompt="ok",
        model_id="Infinity-Parser-7B",
        api_name="/doc_parser",
    )
    print("✅ Infinity-Parser is warm — ready for demo.")
except Exception as e:
    print(f"⚠️  Warmup failed ({e}). Re-upload image in the app after 30s.")
