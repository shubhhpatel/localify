from flask import Flask, request, render_template, send_file
import moviepy.editor as mp
from pytube import YouTube
import eyed3
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

    yt = YouTube(url)

    vidName = yt.title.replace('.', '').replace('"', '').replace('$', '').replace('/', '').replace("'", "")
    yt.streams.get_highest_resolution().download()

    clip = mp.VideoFileClip(vidName + '.mp4')
    clip.audio.write_audiofile(song + '.mp3')

    filename = song + ".mp3"
    audio_file = eyed3.load(filename)

    audio_file.tag.title = song
    audio_file.tag.album = song
    audio_file.tag.album_artist = artist
    audio_file.tag.artist = artist
    audio_file.tag.images.set(3, cover_data, "image/jpeg")
    audio_file.tag.save()
    os.remove(clip.filename)

    try:
        return send_file(
            song + '.mp3',
            as_attachment=True,
            mimetype='audio/mpeg')
    finally:
        os.remove(filename)

  return render_template('index.html')

if __name__ == "__main__":
    app.run()
