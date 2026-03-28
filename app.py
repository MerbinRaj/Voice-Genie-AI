from flask import Flask, render_template, request, send_from_directory
import os
import uuid
import asyncio
import edge_tts
from googletrans import Translator

app = Flask(__name__)

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Folders for uploads and outputs
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Translator
translator = Translator()

# Language → Voice mapping
VOICE_MAP = {
    "english": "en-IN-PrabhatNeural",
    "tamil": "ta-IN-ValluvarNeural",
    "malayalam": "ml-IN-MidhunNeural"
}

# Language → Code mapping
LANG_CODE = {
    "english": "en",
    "tamil": "ta",
    "malayalam": "ml"
}

# Generate audio
async def generate_audio(text, output_path, voice):
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate="-5%",
        pitch="-2Hz"
    )
    await communicate.save(output_path)

@app.route("/", methods=["GET", "POST"])
def home():
    audio_file = None
    error = None

    if request.method == "POST":
        text = request.form.get("text", "").strip()
        language = request.form.get("language")

        if not text:
            error = "Text is required"
            return render_template("index.html", error=error)

        try:
            # Translate if needed
            target_lang = LANG_CODE.get(language, "en")

            if target_lang != "en":
                translated = translator.translate(text, dest=target_lang)
                text = translated.text

            voice = VOICE_MAP.get(language, "en-IN-PrabhatNeural")

            file_id = str(uuid.uuid4())
            output_filename = f"{file_id}.mp3"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)

            asyncio.run(generate_audio(text, output_path, voice))

            audio_file = output_filename

        except Exception as e:
            error = str(e)

    return render_template("index.html", audio_file=audio_file, error=error)

@app.route("/outputs/<filename>")
def serve_audio(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)