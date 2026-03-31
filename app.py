from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import os
import uuid
import asyncio
import edge_tts
from googletrans import Translator

# ---------------- FLASK APP SETUP ----------------
app = Flask(__name__)
app.secret_key = "secret123"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ---------------- TRANSLATOR ----------------
translator = Translator()

# ---------------- VOICE AND LANGUAGE MAP ----------------
VOICE_MAP = {
    "english": "en-IN-PrabhatNeural",
    "tamil": "ta-IN-ValluvarNeural",
    "malayalam": "ml-IN-MidhunNeural"
}

LANG_CODE = {
    "english": "en",
    "tamil": "ta",
    "malayalam": "ml"
}

# ---------------- TEMP USER STORAGE ----------------
# Format: {email: {"username": ..., "password": ...}}
users = {}

# ---------------- AUDIO GENERATION FUNCTION ----------------
async def generate_audio(text, output_path, voice):
    """
    Generate audio using edge_tts
    """
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate="-5%",
        pitch="-2Hz"
    )
    await communicate.save(output_path)

# ---------------- LOGIN + SIGNUP ROUTE ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # LOGIN
        if email in users:
            if users[email]["password"] == password:
                session["user"] = users[email]["username"]
                return redirect(url_for("home"))
            else:
                error = "Wrong password"

        # SIGNUP
        else:
            users[email] = {"username": username, "password": password}
            session["user"] = username
            return redirect(url_for("home"))

    return render_template("login.html", error=error)

# ---------------- MAIN APP ROUTE ----------------
@app.route("/home", methods=["GET", "POST"])
def home():
    if "user" not in session:
        return redirect(url_for("login"))

    audio_file = None
    error = None

    if request.method == "POST":
        text = request.form.get("text", "").strip()
        language = request.form.get("language")

        if not text:
            error = "Text is required"
            return render_template("index.html", error=error)

        try:
            # Translate if language is not English
            target_lang = LANG_CODE.get(language, "en")
            if target_lang != "en":
                translated = translator.translate(text, dest=target_lang)
                text = translated.text

            voice = VOICE_MAP.get(language)

            # Generate unique audio file
            file_id = str(uuid.uuid4())
            filename = f"{file_id}.mp3"
            path = os.path.join(OUTPUT_FOLDER, filename)

            # Generate audio
            asyncio.run(generate_audio(text, path, voice))

            audio_file = filename

        except Exception as e:
            error = str(e)

    return render_template("index.html", audio_file=audio_file, error=error)

# ---------------- SERVE AUDIO FILE ----------------
@app.route("/outputs/<filename>")
def serve_audio(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

# ---------------- LOGOUT ROUTE ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)