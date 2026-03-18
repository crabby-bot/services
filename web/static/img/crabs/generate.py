#!/usr/bin/env python3
"""
generate.py — Generate crab images using OpenAI DALL-E API directly.
Run this once you have an OpenAI API key.

Usage:
    OPENAI_API_KEY=sk-... python3 generate.py
"""

import os, json, base64, urllib.request, urllib.parse, time

OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

CRABS = [
    ("papa",   "A wise, round robot crab sitting proudly like a proud parent, big glowing digital eyes, chunky red shell with circuit patterns, warm orange glow, small antenna with a blinking LED, cute and authoritative, transparent background, Studio Ghibli meets lo-fi tech aesthetic, soft warm lighting"),
    ("snappy", "A small robot crab wearing a tiny black hoodie and holding a magnifying glass, mischievous grin, glowing red eyes, circuit board shell, bug bounty hunter vibes, cute and sneaky, transparent background, lo-fi tech cartoon style"),
    ("crabby", "A small friendly robot crab with a little notepad and pen, soft blue glowing eyes, organised and helpful looking, wearing a tiny headset, personal assistant vibes, cyan and blue colour scheme, transparent background, Studio Ghibli tech aesthetic"),
    ("clicky", "A small robot crab typing on a tiny laptop, green terminal glow on its face, slightly nerdy but cute, web developer vibes, green colour scheme, little glasses, transparent background, lo-fi tech cartoon style"),
    ("pipey",  "A small robot crab wearing a tiny hard hat, holding a wrench, devops engineer vibes, purple and indigo colour scheme, sturdy and reliable looking, cute determination, transparent background, lo-fi tech cartoon style"),
    ("shelly", "A small robot crab wearing a tiny shield on its back, defender pose, blue team security vibes, calm and protective, orange colour scheme, transparent background, lo-fi tech cartoon style, adorable protector"),
    ("mimic",  "A small robot crab that looks slightly mysterious, shifting between appearances, one eye winking, decoy engineer vibes, pink and magenta colour scheme, playful trickster energy, transparent background, lo-fi tech cartoon style"),
    ("pinchy", "A small robot crab holding two tiny phones, talking to multiple people at once, AI wrangler vibes, gold and yellow colour scheme, social butterfly energy, cute and communicative, transparent background, lo-fi tech cartoon style"),
]

def generate(name, prompt):
    url = "https://api.openai.com/v1/images/generations"
    payload = json.dumps({
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "response_format": "b64_json",
        "style": "vivid",
        "quality": "standard"
    }).encode()
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {OPENAI_KEY}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    img = base64.b64decode(data["data"][0]["b64_json"])
    path = os.path.join(OUTPUT_DIR, f"{name}.png")
    with open(path, "wb") as f:
        f.write(img)
    print(f"  ✅ {name}.png ({len(img)//1024}KB)")
    return path

if __name__ == "__main__":
    if not OPENAI_KEY:
        print("❌ Set OPENAI_API_KEY env var first")
        exit(1)
    print(f"Generating {len(CRABS)} crab images with DALL-E 3...")
    for name, prompt in CRABS:
        print(f"  🦀 {name}...")
        try:
            generate(name, prompt)
            time.sleep(1)  # rate limit
        except Exception as e:
            print(f"  ❌ {name} failed: {e}")
    print("\nDone! Restart crabby-web to see the images.")
