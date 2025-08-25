'''
Local voice assistant with wake words ("hi nick", "hey assistant", "nick").

Features:
- Speech-to-text (Google via speech_recognition) with text fallback
- Text-to-speech via pyttsx3
- Time-based greetings
- Intents: time, date, weather (OpenWeatherMap), Wikipedia, open websites, set timers, play music, run system commands, tell jokes, exit
- Uses .env for API keys
- Cross-platform media support and error handling
'''
import os
import sys
import time
import webbrowser
import threading
import subprocess
import traceback
from typing import Optional
import datetime
import requests
import pyttsx3
import wikipedia
import random
from dotenv import load_dotenv

# Try to import SpeechRecognition, else run in text-only mode
try:
    import speech_recognition as sr
    VOICE_AVAILABLE = True
except Exception:
    VOICE_AVAILABLE = False

load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# === TTS engine ===
engine = pyttsx3.init()

def say(text: str, wait: bool = False):
    """Speak text out loud (non-blocking)."""
    engine.say(text)
    engine.runAndWait()

# === STT helper ===
def listen_voice(timeout: Optional[int] = None, phrase_limit: Optional[int] = 7) -> str:
    """Listen and return recognized text. Returns empty string on failure."""
    if not VOICE_AVAILABLE:
        return input("You (text mode): ")

    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.6)
        print("Listening...")
        try:
            if timeout:
                audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
            else:
                audio = r.listen(source, phrase_time_limit=phrase_limit)
        except sr.WaitTimeoutError:
            print("Timeout waiting for phrase start.")
            return ""
        except Exception as e:
            print("Microphone/listen error:", e)
            return ""

    try:
        text = r.recognize_google(audio)
        print("Heard:", text)
        return text
    except sr.UnknownValueError:
        print("Could not understand audio")
        return ""
    except sr.RequestError as e:
        print("Could not request results; check your internet connection ->", e)
        return ""
    except Exception as e:
        print("STT error:", e)
        return ""

# === Time-based greeting function ===
def get_time_based_greeting() -> str:
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        return random.choice([
            "Good morning! How can I assist you today?",
            "Morning! Ready when you are.",
            "Top of the morning to you!"
        ])
    elif 12 <= hour < 17:
        return random.choice([
            "Good afternoon! What can I do for you?",
            "Afternoon! How may I help?",
            "Hope your day is going well!"
        ])
    elif 17 <= hour < 21:
        return random.choice([
            "Good evening! How can I help you tonight?",
            "Evening! What do you need?",
            "Hope you had a great day so far."
        ])
    else:
        return random.choice([
            "Hello! Burning the midnight oil?",
            "Hey there! It's quite late, hope I can assist.",
            "It's late! How can I help you?"
        ])

# === Jokes ===
JOKES = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "Why don't programmers like nature? It has too many bugs.",
    "Why did the math book look sad? Because it had too many problems.",
    "What do you call fake spaghetti? An impasta!",
    "Why did the bicycle fall over? Because it was two-tired!",
    "How do you organize a space party? You planet."
]

def tell_joke() -> str:
    return random.choice(JOKES)

# === Utilities / Intents ===
def tell_time() -> str:
    return datetime.datetime.now().strftime("It is %I:%M %p")

def tell_date() -> str:
    return datetime.date.today().strftime("Today is %B %d, %Y")

def weather_for(city: str) -> str:
    if not OPENWEATHER_API_KEY:
        return "Weather API key not set. Put OPENWEATHER_API_KEY in your .env"
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        name = data.get("name", city)
        main = data.get("main", {})
        temp = main.get("temp")
        hum = main.get("humidity")
        weather_list = data.get("weather", [])
        desc = weather_list[0]["description"].title() if weather_list else "N/A"
        return f"{name}: {desc}. Temperature {temp}°C, humidity {hum}%."
    except requests.HTTPError as e:
        return f"HTTP error while fetching weather: {e}"
    except Exception as e:
        return f"Error fetching weather: {e}"

def wiki_summary(query: str, sentences: int = 2) -> str:
    try:
        wikipedia.set_lang("en")
        summary = wikipedia.summary(query, sentences=sentences, auto_suggest=True, redirect=True)
        return summary
    except Exception as e:
        return f"Wikipedia error: {e}"

def open_website(domain: str) -> str:
    if not domain.startswith("http"):
        domain = "https://" + domain
    webbrowser.open(domain)
    return f"Opening {domain}"

def play_music(filepath: str) -> str:
    try:
        if sys.platform.startswith("win"):
            os.startfile(filepath)
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", filepath])
        else:
            subprocess.Popen(["xdg-open", filepath])
        return f"Playing {filepath}"
    except Exception as e:
        return f"Could not play music: {e}"

def run_shell_command(cmd: str) -> str:
    try:
        completed = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=8)
        out = completed.stdout.strip()
        err = completed.stderr.strip()
        if out:
            return out[:1000]
        if err:
            return f"Error: {err[:1000]}"
        return "Command executed."
    except Exception as e:
        return f"Shell command error: {e}"

# === Reminders / Timers ===
timers = []

def set_timer(seconds: int, message: str):
    def _alarm():
        say(f"Timer: {message}", wait=True)
        print(f"[TIMER] {message}")
    t = threading.Timer(seconds, _alarm)
    t.daemon = True
    t.start()
    timers.append(t)
    return f"Timer set for {seconds} seconds"

# === Intent parsing ===
WAKE_WORDS = ["hi nick", "hi, nick", "hey assistant", "nick"]

def is_wake(text: str) -> bool:
    t = text.lower()
    return any(t.startswith(w) or (" " + w + " ") in (" " + t + " ") or w in t for w in WAKE_WORDS)

def parse_and_execute(command: str) -> str:
    c = command.lower().strip()
    for w in sorted(WAKE_WORDS, key=len, reverse=True):
        if c.startswith(w):
            c = c[len(w):].strip()
            break
        if (" " + w + " ") in (" " + c + " "):
            c = c.replace(w, "").strip()
            break

    greeting_keywords = ["hello", "hi", "hey"]
    if any(word in c for word in greeting_keywords):
        return get_time_based_greeting()

    # Joke intent
    if "joke" in c or "funny" in c or "make me laugh" in c:
        return tell_joke()

    if not c:
        return "Yes?"

    if "who invented you" in c or "who created you" in c:
        return "I was coded by a curious human—maybe someone a bit like you!"

    if any(x in c for x in ["time", "what time"]):
        return tell_time()

    if any(x in c for x in ["date", "what date", "day is it"]):
        return tell_date()

    if c.startswith("weather"):
        parts = c.split()
        if "in" in parts:
            city = " ".join(parts[parts.index("in") + 1 :])
        else:
            city = " ".join(parts[1:]) or "your city"
        return weather_for(city)

    if c.startswith("search ") or c.startswith("google "):
        q = command.split(maxsplit=1)[1]
        webbrowser.open(f"https://www.google.com/search?q={requests.utils.requote_uri(q)}")
        return f"Searching the web for {q}"

    if c.startswith("open "):
        domain = c.replace("open ", "").strip()
        return open_website(domain)

    if c.startswith("wikipedia ") or c.startswith("wiki "):
        query = command.split(maxsplit=1)[1]
        return wiki_summary(query, sentences=2)

    if c.startswith("set timer for"):
        try:
            parts = c.split()
            if "seconds" in parts:
                n = int(parts[parts.index("seconds") - 1])
                secs = n
            elif "minutes" in parts:
                n = int(parts[parts.index("minutes") - 1])
                secs = n * 60
            else:
                secs = int(parts[-1])
            msg = "timer"
            return set_timer(secs, msg)
        except Exception:
            return "I couldn't parse the timer duration. Say: set timer for 10 seconds"

    if c.startswith("play "):
        filepath = command.split(maxsplit=1)[1]
        return play_music(filepath)

    if c.startswith("run "):
        cmd = command.split(maxsplit=1)[1]
        return run_shell_command(cmd)

    if any(x in c for x in ["exit", "quit", "goodbye", "stop"]):
        say("It’s been nice talking to you. Have a great day!")
        return "exit"

    return wiki_summary(command, sentences=1)

# === Main loop ===
def assistant_loop():
    say(get_time_based_greeting())
    print("Assistant ready. (Press Ctrl+C to quit)")

    while True:
        try:
            text = listen_voice(timeout=None, phrase_limit=7)
            print(f"DEBUG: Recognized text: {text}")
            if not text:
                text = input("You (type a command or press Enter to listen again): ").strip()
                if not text:
                    continue

            result = parse_and_execute(text)
            if result == "exit":
                say("Goodbye!")
                print("Exiting assistant.")
                break

            if result:
                print("Assistant:", result)
                say(result)

        except KeyboardInterrupt:
            print("\nKeyboard interrupt received. Exiting.")
            say("Goodbye!")
            break
        except Exception:
            print("Unhandled error in assistant loop:")
            traceback.print_exc()
            say("Sorry, I encountered an error.")

if __name__ == "__main__":
    assistant_loop()

