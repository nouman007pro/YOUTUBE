from flask import Flask, request, render_template, send_file
import yt_dlp
import os
import re

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def safe_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

@app.route("/", methods=["GET", "POST"])
def home():
    title = None
    thumbnail = None
    url = None
    error = None
    formats = []

    if request.method == "POST":
        url = request.form.get("url")
        try:
            ydl_opts = {
                "quiet": True,
                "skip_download": True,
                "js_runtimes": ["node"]
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            title = info.get("title")
            thumbnail = info.get("thumbnail")

            # Saare available formats list
            for f in info.get("formats", []):
                fmt = {
                    "format_id": f.get("format_id"),
                    "ext": f.get("ext"),
                    "resolution": f.get("resolution") or f"{f.get('height','?')}p",
                    "acodec": f.get("acodec"),
                    "vcodec": f.get("vcodec")
                }
                formats.append(fmt)

        except Exception as e:
            error = str(e)

    return render_template(
        "index.html",
        title=title,
        thumbnail=thumbnail,
        url=url,
        error=error,
        formats=formats
    )

@app.route("/download")
def download():
    url = request.args.get("url")
    fmt = request.args.get("format")

    if not url:
        return "No URL provided"

    base_opts = {
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",
        "cookiesfrombrowser": ("chrome",),
        "merge_output_format": "mp4",
        "js_runtimes": ["node"]
    }

    if fmt == "mp3":
        ydl_opts = {
            **base_opts,
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }]
        }
    else:
        # fmt is format_id
        ydl_opts = {**base_opts, "format": fmt}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if fmt == "mp3":
                filename = os.path.splitext(filename)[0] + ".mp3"

        return send_file(filename, as_attachment=True)
    except Exception as e:
        return f"Download failed: {e}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)