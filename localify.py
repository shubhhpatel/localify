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
        if request.form['conversion-type'] == 'YouTube Song' or request.form['conversion-type'] == 'SoundCloud Song' or request.form['conversion-type'] == 'TikTok Sound' or request.form['conversion-type'] == 'Instagram Reel Audio':
            url = request.form['link']
            artist = request.form['artist-name']
            song = request.form['song-name']
            use_cover_art = request.form.get('use-cover-art') == 'true'

            if use_cover_art and request.form['conversion-type'] == 'SoundCloud Song':
                cover_art_url = get_soundcloud_thumbnail(url)
                cover_data = get_image_data(cover_art_url)
            else:
                cover = request.files['files']
                cover_data = cover.read()

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'song',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                audio_filename = "song.mp3"

            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                tmp_filename = tmp_file.name

            audio = AudioSegment.from_file(audio_filename)
            audio.export(tmp_filename, format='mp3')

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

        elif request.form['conversion-type'] == 'YouTube Playlist' or request.form['conversion-type'] == 'SoundCloud Playlist':
            playlist_url = request.form['link']
            artist = request.form['artist-name']
            song = request.form['song-name']
            use_cover_art = request.form.get('use-cover-art') == 'true'

            if use_cover_art and request.form['conversion-type'] == 'SoundCloud Song':
                cover_art_url = get_soundcloud_thumbnail(url)
                cover_data = get_image_data(cover_art_url)
            else:
                cover = request.files['files']
                cover_data = cover.read()

            sanitized_song_name = re.sub(r'[<>:"/\\|?*]', '', song)

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
                playlist_info = ydl.extract_info(playlist_url, download=False)
                video_urls = [video['webpage_url'] for video in playlist_info['entries']]

                try:
                    zip_filename = f"{sanitized_song_name}.zip"
                    sanitized_zip_filename = sanitize_filename(zip_filename)
                    zip_path = os.path.join(os.getcwd(), sanitized_zip_filename)

                    with zipfile.ZipFile(zip_path, 'w') as zip_file:
                        for video_url in video_urls:
                            info_dict = ydl.extract_info(video_url, download=True)
                            audio_filename = f"{info_dict['title']}.mp3"

                            sanitized_audio_filename = re.sub(r'[<>:"/\\|?*]', '', audio_filename)
                            sanitized_audio_filename = sanitize_filename(sanitized_audio_filename)

                            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                                tmp_filename = tmp_file.name

                            audio = AudioSegment.from_file(audio_filename)
                            audio.export(tmp_filename, format='mp3')

                            audio_file = eyed3.load(tmp_filename)
                            audio_file.tag.title = info_dict.get('track')
                            audio_file.tag.album = sanitized_song_name
                            audio_file.tag.album_artist = artist
                            audio_file.tag.artist = info_dict.get('artist')
                            audio_file.tag.images.set(3, cover_data, "image/jpeg")
                            audio_file.tag.save()

                            zip_file.write(tmp_filename, sanitized_audio_filename)

                            os.remove(tmp_filename)

                    response = send_file(
                        zip_path,
                        as_attachment=True,
                        mimetype='application/zip'
                    )
                    response.headers["Content-Disposition"] = f"attachment; filename={sanitized_zip_filename}"
                    return response
                finally:
                    root_files = glob.glob(os.path.join(os.getcwd(), '*.mp3'))

                    for file in root_files:
                        os.remove(file)

                    if os.path.exists(zip_path):
                        os.remove(zip_path)

    return render_template('index.html')

def get_soundcloud_thumbnail(url):
    soundcloud_api_url = f"https://soundcloud.com/oembed?url={url}&format=json"
    response = requests.get(soundcloud_api_url)
    response_data = response.json()
    return response_data.get('thumbnail_url', '')

def get_audio_data(url):
    response = requests.get(url)
    return response.content

def sanitize_filename(filename):
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
    return ''.join(c for c in filename if c in valid_chars)

def get_image_data(url):
    response = requests.get(url)
    return response.content

if __name__ == "__main__":
    app.run()
