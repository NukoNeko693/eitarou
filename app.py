import os
import tempfile
from flask import Flask, render_template, request, send_file, after_this_request
import yt_dlp

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    query = request.args.get("q", "").strip()
    videos = []

    if query:
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch10:{query}", download=False)

        for entry in result.get("entries", []):
            video_id = entry.get("id")
            title = entry.get("title")
            thumbnail = entry.get("thumbnail")

            if video_id and title:
                videos.append({
                    "id": video_id,
                    "title": title,
                    "thumbnail": thumbnail,
                    "url": f"https://www.youtube.com/watch?v={video_id}"
                })

    return render_template("index.html", query=query, videos=videos)


@app.route("/download/<video_id>")
def download(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    tmpdir = tempfile.mkdtemp()
    output_path = os.path.join(tmpdir, "%(title).80s.%(ext)s")

    ydl_opts = {
        "outtmpl": output_path,
        "format": "best[ext=mp4][vcodec!=none][acodec!=none]/best[ext=mp4]/best",
        "quiet": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        downloaded_file = ydl.prepare_filename(info)

    @after_this_request
    def cleanup(response):
        try:
            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)
            os.rmdir(tmpdir)
        except Exception:
            pass
        return response

    return send_file(
        downloaded_file,
        as_attachment=True,
        download_name=os.path.basename(downloaded_file)
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
