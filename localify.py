from flask import Flask, request, render_template, send_file
import yt_dlp
import moviepy.editor as mp
import eyed3
import tempfile
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['youtube-link']
        artist = request.form['artist-name']
        song = request.form['song-name']
        cover = request.files['files']
        cover_data = cover.read()

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            audio_filename = f"{info_dict['title']}.mp3"

        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_filename = tmp_file.name

        clip = mp.AudioFileClip(audio_filename)
        clip.write_audiofile(tmp_filename)

        audio_file = eyed3.load(tmp_filename)
        audio_file.tag.title = song
        audio_file.tag.album = song
        audio_file.tag.album_artist = artist
        audio_file.tag.artist = artist
        audio_file.tag.images.set(3, cover_data, "image/jpeg")
        audio_file.tag.save()

        try:
            response = send_file(
                tmp_filename,
                as_attachment=True,
                mimetype='audio/mpeg'
            )
            response.headers['Content-Disposition'] = f"attachment; filename={song}.mp3"
            return response
        finally:
            os.remove(audio_filename)
            os.remove(tmp_filename)

    return render_template('index.html')

if __name__ == "__main__":
    app.run()
