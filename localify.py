from flask import Flask, request, render_template, send_file
import yt_dlp
from pydub import AudioSegment
import eyed3
import tempfile
import os
import re
import zipfile
import glob
import requests
import string


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
   if request.method == 'POST':
       if request.form['conversion-type'] in ['YouTube Song', 'SoundCloud Song', 'TikTok Sound']:
           url = request.form['link']
           artist = request.form['artist-name']
           song = request.form['song-name']
           use_cover_art = request.form.get('use-cover-art') == 'true'


           if use_cover_art and request.form['conversion-type'] == 'SoundCloud Song':
               cover_art_url = get_soundcloud_thumbnail(url)
               cover_data = get_image_data(cover_art_url)
           else:
               cover = request.files['cover-art']
               cover_data = cover.read()


           ydl_opts = {
               'format': 'bestaudio/best',
               'outtmpl': '%(title)s.%(ext)s',
               'postprocessors': [{
                   'key': 'FFmpegExtractAudio',
                   'preferredcodec': 'mp3',
                   'preferredquality': '192',
               }],
               'verbose': True
           }


           with yt_dlp.YoutubeDL(ydl_opts) as ydl:
               info_dict = ydl.extract_info(url, download=True)
               audio_filename = ydl.prepare_filename(info_dict)


           if not os.path.exists(audio_filename) or os.path.getsize(audio_filename) == 0:
               return "Error: File not found or is empty", 500


           with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
               tmp_filename = tmp_file.name


           try:
               audio = AudioSegment.from_file(audio_filename)
               audio.export(tmp_filename, format='mp3')
           except Exception as e:
               return f"Error processing audio file: {e}", 500


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


       # Similar code for handling 'YouTube Playlist' or 'SoundCloud Playlist'


   return render_template('index.html')


def get_soundcloud_thumbnail(url):
   soundcloud_api_url = f"https://soundcloud.com/oembed?url={url}&format=json"
   response = requests.get(soundcloud_api_url)
   response_data = response.json()
   return response_data.get('thumbnail_url', '')


def get_image_data(url):
   response = requests.get(url)
   return response.content


def sanitize_filename(filename):
   valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
   return ''.join(c for c in filename if c in valid_chars)


if __name__ == "__main__":
   app.run()



