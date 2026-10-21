#!/usr/bin/env python3
"""Create a simple CocoCloud Kids video using public RSS, a rhyme template, Piper TTS and FFmpeg.

This intentionally uses a reusable 2D cartoon bus scene, not AI-generated 3D footage.
All rendering is done on the GitHub Actions runner; no paid API is used.
"""
from __future__ import annotations

import html
import json
import math
import os
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
FRAMES = OUT / "frames"
WIDTH, HEIGHT = 1280, 720
FPS = 12
SCENE_SECONDS = 4
SCENES = 5
TOTAL_SECONDS = SCENE_SECONDS * SCENES
VOICE = os.getenv("PIPER_VOICE", "en_US-lessac-medium")
VOICE_DIR = OUT / "voice"
VOICE_MODEL = VOICE_DIR / f"{VOICE}.onnx"
VOICE_CONFIG = VOICE_DIR / f"{VOICE}.onnx.json"

RSS_FEEDS = [
    "https://www.nasa.gov/news-release/feed/",
    "https://www.noaa.gov/news-release/feed",
]
FALLBACK_TOPICS = [
    ("The Happy Little Bus", "bus"),
    ("A Rocket to the Moon", "space"),
    ("The Busy Little Bees", "bees"),
    ("Dancing Raindrops", "rain"),
    ("The Friendly Ocean", "ocean"),
    ("The Little Garden", "garden"),
    ("The Rainbow Train", "train"),
    ("The Sleepy Stars", "stars"),
]
KEYWORDS = [
    (("moon", "planet", "space", "rocket", "mars", "star", "astronaut"), ("A Rocket to the Moon", "space")),
    (("ocean", "sea", "whale", "dolphin", "coral", "fish"), ("The Friendly Ocean", "ocean")),
    (("bee", "pollinator", "honey"), ("The Busy Little Bees", "bees")),
    (("rain", "storm", "cloud", "weather", "rainbow"), ("Dancing Raindrops", "rain")),
    (("plant", "flower", "garden", "tree", "seed"), ("The Little Garden", "garden")),
    (("train", "transport", "vehicle", "bus"), ("The Happy Little Bus", "bus")),
    (("animal", "wildlife", "bird", "turtle"), ("The Friendly Animal Parade", "animals")),
]

def run(cmd: list[str], *, input_text: str | None = None) -> None:
    subprocess.run(cmd, input=input_text, text=True, check=True)

def fetch_topic() -> tuple[str, str, str]:
    override = os.getenv("TOPIC_OVERRIDE", "").strip()
    if override:
        return override[:100], "custom", "Manual workflow topic override"
    candidates: list[tuple[str, str]] = []
    for url in RSS_FEEDS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CocoCloudKidsVideoFactory/1.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                raw = response.read(1_500_000)
            root = ET.fromstring(raw)
            for item in root.findall(".//item")[:20]:
                title = html.unescape((item.findtext("title") or "").strip())
                desc = html.unescape(re.sub(r"<[^>]+>", " ", item.findtext("description") or "")).strip()
                text = f"{title} {desc}".lower()
                for words, topic in KEYWORDS:
                    if any(word in text for word in words):
                        candidates.append((topic[0], f"RSS match: {title[:180]}"))
                        break
        except Exception as exc:
            print(f"RSS unavailable ({url}): {exc}", file=sys.stderr)
    if candidates:
        # Stable enough for reproducibility, but rotate through matching items.
        index = int(datetime.now(timezone.utc).strftime("%j")) % len(candidates)
        title, source = candidates[index]
        return title, "rss", source
    day_index = int(datetime.now(timezone.utc).strftime("%j")) % len(FALLBACK_TOPICS)
    title, theme = FALLBACK_TOPICS[day_index]
    return title, theme, "Built-in fallback (RSS unavailable or no suitable kid-safe match)"

def make_poem(topic: str, theme: str) -> str:
    # Reusable original rhyme template. Topic/theme words are inserted into fresh lines.
    clean = topic.strip().rstrip(".!?") or "The Happy Little Bus"
    safe_theme = theme.replace("_", " ")
    verses = [
        f"{clean}, come along,",
        f"Clap your hands and sing our song!",
        f"Little smiles and feet that go,",
        f"Wave hello and off we go!",
        "",
        f"Round the {safe_theme}, bright and blue,",
        "Find a friendly thing to do.",
        "Hop and wiggle, count to four,",
        "Then let's giggle just once more!",
        "",
        "Sunshine dancing, skies so wide,",
        "Kind friends travelling side by side.",
        "When our happy day is through,",
        "We'll sing this little song for you!",
    ]
    return "\n".join(verses) + "\n"

def load_font(size: int, bold: bool = False):
    choices = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in choices:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def draw_cloud(draw, x, y, scale=1.0):
    r = int(28 * scale)
    draw.ellipse((x, y, x+2*r, y+2*r), fill="#FFFFFF")
    draw.ellipse((x+r, y-r//2, x+3*r, y+2*r), fill="#FFFFFF")
    draw.ellipse((x+2*r, y, x+4*r, y+2*r), fill="#FFFFFF")

def draw_bus(draw, x, bounce, scene_index):
    y = 420 + bounce
    # bus shadow
    draw.ellipse((x+20, y+140, x+390, y+180), fill="#B6D7D5")
    # body and roof
    draw.rounded_rectangle((x, y, x+390, y+145), radius=28, fill="#FFC83D", outline="#C17A18", width=5)
    draw.rounded_rectangle((x+25, y-42, x+320, y+35), radius=24, fill="#FFDB67", outline="#C17A18", width=4)
    # windows
    for wx in (x+28, x+105, x+182, x+259):
        draw.rounded_rectangle((wx, y+20, wx+62, y+72), radius=10, fill="#B9ECFF", outline="#398CB5", width=3)
    # windshield and friendly face
    draw.rounded_rectangle((x+323, y+20, x+375, y+88), radius=12, fill="#B9ECFF", outline="#398CB5", width=3)
    draw.ellipse((x+330, y+91, x+345, y+106), fill="#382E52")
    draw.ellipse((x+355, y+91, x+370, y+106), fill="#382E52")
    draw.arc((x+338, y+95, x+365, y+125), 5, 170, fill="#C64B48", width=4)
    # bumper and wheels
    draw.rounded_rectangle((x-8, y+116, x+398, y+141), radius=8, fill="#E65F57")
    for cx in (x+78, x+305):
        draw.ellipse((cx-39, y+112, cx+39, y+190), fill="#34364A")
        draw.ellipse((cx-20, y+131, cx+20, y+171), fill="#D7E5EC")
        draw.ellipse((cx-7, y+144, cx+7, y+158), fill="#7D8DA0")
    # little pennant
    draw.line((x+45, y-38, x+45, y-86), fill="#5C4AB1", width=5)
    draw.polygon([(x+47, y-84), (x+100, y-70), (x+47, y-55)], fill="#F36F91")

def draw_scene(frame_index: int, scene_index: int, topic: str, theme: str):
    t = frame_index / FPS
    bounce = int(7 * math.sin(t * math.pi * 2))
    im = Image.new("RGB", (WIDTH, HEIGHT), "#9DE4FF")
    d = ImageDraw.Draw(im)
    # sunny sky
    d.ellipse((1040, 42, 1160, 162), fill="#FFE46B", outline="#F5B93B", width=5)
    draw_cloud(d, 80 + int((t*28) % 120), 105, 0.9)
    draw_cloud(d, 710 + int((t*18) % 100), 155, 0.7)
    # distant hills and grassy ground
    d.ellipse((-120, 390, 620, 650), fill="#7ED58A")
    d.ellipse((480, 365, 1380, 660), fill="#66C77B")
    d.rectangle((0, 520, WIDTH, HEIGHT), fill="#72CF7B")
    # flowers along the road
    for fx in range(70, WIDTH, 170):
        fy = 590 + (fx % 3) * 12
        d.line((fx, fy, fx, fy+28), fill="#2F9B55", width=5)
        d.ellipse((fx-12, fy-12, fx+12, fy+12), fill=["#FF6B9D", "#FFD65A", "#FFFFFF"][(fx//170+scene_index)%3])
        d.ellipse((fx-4, fy-4, fx+4, fy+4), fill="#F6A33B")
    # road
    d.rounded_rectangle((0, 625, WIDTH, 720), radius=0, fill="#777D8E")
    for rx in range(-40, WIDTH, 170):
        d.rounded_rectangle((rx + int(t*90)%170, 665, rx+80 + int(t*90)%170, 674), radius=4, fill="#FFF2C2")
    # title banner
    d.rounded_rectangle((35, 28, 840, 94), radius=22, fill="#FFFFFF", outline="#6C8CC8", width=3)
    title = topic[:42]
    d.text((58, 42), title, font=load_font(30, True), fill="#493B83")
    # bus slides slowly across center; loop motion keeps it visible
    x = 370 + int(20 * math.sin(t * math.pi / 2))
    draw_bus(d, x, bounce, scene_index)
    # friendly stars/scene decoration
    if scene_index % 2 == 0:
        for sx, sy in ((930, 270), (1080, 330), (220, 310)):
            d.text((sx, sy + int(6*math.sin(t*3+sx))), "★", font=load_font(36, True), fill="#FFF5A5")
    caption = ["Come along and sing!", "Wave hello, friends!", "Clap your hands!", "Wiggle and go!", "See you next time!"][scene_index]
    d.rounded_rectangle((300, 215, 980, 278), radius=22, fill="#FFFFFF", outline="#F39AAB", width=3)
    bbox = d.textbbox((0, 0), caption, font=load_font(30, True))
    d.text(((WIDTH-(bbox[2]-bbox[0]))//2, 229), caption, font=load_font(30, True), fill="#E45B83")
    return im

def download_voice():
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    if VOICE_MODEL.exists() and VOICE_CONFIG.exists():
        return
    base = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/{VOICE}"
    for suffix, dest in ((".onnx", VOICE_MODEL), (".onnx.json", VOICE_CONFIG)):
        url = base + suffix
        print(f"Downloading free Piper voice file: {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "CocoCloudKidsVideoFactory/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as out:
            out.write(resp.read())

def make_audio(poem: str):
    download_voice()
    poem_for_speech = re.sub(r"\n+", ". ", poem).strip()
    # piper-tts installs the `piper` CLI on the runner.
    run(["piper", "--model", str(VOICE_MODEL), "--config", str(VOICE_CONFIG),
         "--output_file", str(OUT / "narration.wav")], input_text=poem_for_speech)
    # Add a gentle, royalty-free-by-creation synthesized backing melody using FFmpeg's sine source.
    # The sine layer is deliberately subtle and has no third-party music asset.
    narration = OUT / "narration.wav"
    music = OUT / "music.wav"
    run(["ffmpeg", "-y", "-f", "lavfi", "-i",
         f"sine=frequency=523.25:duration={TOTAL_SECONDS}:sample_rate=44100",
         "-af", "volume=0.025", "-c:a", "pcm_s16le", str(music)])
    # Loop or trim narration to target duration, mixing a quiet generated tone underneath.
    run(["ffmpeg", "-y", "-i", str(narration), "-i", str(music), "-filter_complex",
         f"[0:a]apad,atrim=0:{TOTAL_SECONDS},asetpts=PTS-STARTPTS[voice];"
         f"[1:a]atrim=0:{TOTAL_SECONDS},asetpts=PTS-STARTPTS[music];"
         "[voice][music]amix=inputs=2:duration=first:dropout_transition=1[a]",
         "-map", "[a]", "-ar", "44100", "-ac", "2", str(OUT / "final_audio.wav")])

def render_video(topic: str, theme: str):
    FRAMES.mkdir(parents=True, exist_ok=True)
    frames_per_scene = FPS * SCENE_SECONDS
    for idx in range(SCENES):
        scene_dir = FRAMES / f"scene_{idx+1:02d}"
        scene_dir.mkdir(parents=True, exist_ok=True)
        for fidx in range(frames_per_scene):
            im = draw_scene(fidx, idx, topic, theme)
            im.save(scene_dir / f"frame_{fidx:04d}.png", optimize=True)
        clip = OUT / f"scene_{idx+1:02d}.mp4"
        run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
             "-i", str(scene_dir / "frame_%04d.png"), "-c:v", "libx264",
             "-pix_fmt", "yuv420p", "-preset", "ultrafast", "-crf", "25",
             "-an", str(clip)])
    concat_file = OUT / "clips.txt"
    concat_file.write_text("".join(f"file '{OUT / f'scene_{i+1:02d}.mp4'}'\n" for i in range(SCENES)), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
         "-i", str(OUT / "final_audio.wav"), "-c:v", "copy", "-c:a", "aac",
         "-b:a", "128k", "-shortest", "-movflags", "+faststart",
         str(OUT / "cococloud_kids_video.mp4")])

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    topic, theme, source = fetch_topic()
    poem = make_poem(topic, theme)
    (OUT / "poem.txt").write_text(poem, encoding="utf-8")
    (OUT / "topic.json").write_text(json.dumps({
        "topic": topic, "theme": theme, "source": source,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "generation_note": "Original reusable rhyme template; no paid AI API used."
    }, indent=2), encoding="utf-8")
    print(f"Selected topic: {topic} ({source})")
    print("Poem:\n" + poem)
    make_audio(poem)
    render_video(topic, theme)
    # Thumbnail from the first frame
    draw_scene(0, 0, topic, theme).save(OUT / "thumbnail.png")
    print(f"Video ready: {OUT / 'cococloud_kids_video.mp4'}")

if __name__ == "__main__":
    main()
