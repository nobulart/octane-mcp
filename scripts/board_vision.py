#!/usr/bin/env python3
"""Local vision check for the pawn-on-board preview (default qwen2.5vl:7b)."""
import urllib.request, json, base64

p = "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/renders/pawn_on_board_preview.png"
b64 = base64.b64encode(open(p, "rb").read()).decode()
prompt = ('Output JSON only: {"chessboard_present": true/false, "pawn_is_green": true/false, '
          '"board_has_dark_and_light_squares": true/false, "studio_lit": true/false, "mismatch_risks": "..."}')
payload = {"model": "qwen2.5vl:7b", "prompt": prompt, "images": [b64], "stream": False,
           "options": {"temperature": 0, "num_predict": 140}}
try:
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.loads(r.read().decode())
    print("RAW qwen2.5vl:7b (board) response:")
    print(d.get("response", "").strip())
except Exception as e:
    print("OLLAMA_UNAVAILABLE:", e)
