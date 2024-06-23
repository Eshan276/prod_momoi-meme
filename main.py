from flask import Flask, request, jsonify, send_file, url_for
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips
from pydub import AudioSegment
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'

def generate_video(name, profile_image_path, song_path, start_time):
    first_video = VideoFileClip("first.mp4")
    second_video = VideoFileClip("second.mp4")
    third_video = VideoFileClip("third.mp4")

    #font_path = os.path.join("fonts", "arial.ttf")  # Updated font path
    font_size = 70
    font = ImageFont.load_default()
    text = name
    image_size = (second_video.w, second_video.h)
    text_image = Image.new('RGBA', image_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_image)
    text_width, text_height = draw.textsize(text, font=font)
    text_position = ((image_size[0] - text_width) // 2, (image_size[1] - text_height) // 2)
    draw.text(text_position, text, font=font, fill="black")

    text_image_path = os.path.join(app.config['UPLOAD_FOLDER'], f"text_{name}.png")
    text_image.save(text_image_path)

    txt_clip = ImageClip(text_image_path, duration=second_video.duration)

    tts = gTTS(text=name, lang='en')
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f"audio_{name}.wav")
    tts.save(audio_path)

    sound = AudioSegment.from_file(audio_path)
    chipmunk_sound = sound._spawn(sound.raw_data, overrides={
        "frame_rate": int(sound.frame_rate * 1.5)
    }).set_frame_rate(sound.frame_rate)

    chipmunk_audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f"chipmunk_audio_{name}.wav")
    chipmunk_sound.export(chipmunk_audio_path, format="wav")

    audio_clip_second = AudioFileClip(chipmunk_audio_path)

    second_video = CompositeVideoClip([second_video, txt_clip.set_position((45, 170))])
    second_video = second_video.set_audio(audio_clip_second)

    song = AudioSegment.from_file(song_path)
    start_ms = start_time * 1000
    cropped_song = song[start_ms:start_ms + 20000]

    chipmunk_song = cropped_song._spawn(cropped_song.raw_data, overrides={
        "frame_rate": int(cropped_song.frame_rate * 1.5)
    }).set_frame_rate(cropped_song.frame_rate)

    chipmunk_song_path = os.path.join(app.config['UPLOAD_FOLDER'], f"chipmunk_song_{name}.wav")
    chipmunk_song.export(chipmunk_song_path, format="wav")

    audio_clip_third = AudioFileClip(chipmunk_song_path)
    third_video = third_video.set_audio(audio_clip_third)

    profile_image = ImageClip(profile_image_path).set_duration(first_video.duration).resize(height=first_video.h / 8).set_position((950, 500))
    first_video = CompositeVideoClip([first_video, profile_image])
    
    profile_image = ImageClip(profile_image_path).set_duration(second_video.duration).resize(height=second_video.h / 8).set_position((950, 500))
    second_video = CompositeVideoClip([second_video, profile_image])
    
    profile_image = ImageClip(profile_image_path).set_duration(third_video.duration).resize(height=third_video.h / 8).set_position((950, 500))
    third_video = CompositeVideoClip([third_video, profile_image])

    final_video = concatenate_videoclips([first_video, second_video, third_video])
    final_video = final_video.subclip(0, 10)

    output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"output_{name}.mp4")
    final_video.write_videofile(output_path, codec="libx264", audio_codec='aac')

    final_video.close()
    first_video.close()
    second_video.close()
    third_video.close()
    audio_clip_second.close()
    audio_clip_third.close()

    os.remove(audio_path)
    os.remove(text_image_path)
    os.remove(chipmunk_song_path)
    os.remove(chipmunk_audio_path)
    
    return output_path

@app.route('/generate', methods=['POST'])
async def generate():
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    name = request.form['name']
    start_time = float(request.form['start_time'])

    profile_image = request.files['profile_image']
    profile_image_path = os.path.join(app.config['UPLOAD_FOLDER'], profile_image.filename)
    profile_image.save(profile_image_path)

    song = request.files['song']
    song_path = os.path.join(app.config['UPLOAD_FOLDER'], song.filename)
    song.save(song_path)

    video_path = generate_video(name, profile_image_path, song_path, start_time)
    return jsonify({"video_url": url_for('uploaded_file', filename=os.path.basename(video_path))})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(host='0.0.0.0', port=5000)
