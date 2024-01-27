from flask import Flask, request, send_file, render_template
from werkzeug.utils import secure_filename
import os
import moviepy.editor as mp

app = Flask(__name__)

#Set the directory for uploads
UPLOAD_FOLDER = '/home/parth/Desktop/Hackathon/uploads'
PROCESSED_FOLDER = '/home/parth/Desktop/Hackathon/processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Process the file
        output_file_path = process_file(file_path)
        
        # Send back the processed file
        return send_file(output_file_path, as_attachment=True)

def process_file(file_path):
    # Extract audio from video
    clip = mp.VideoFileClip(file_path)
    audio_path = file_path.rsplit('.', 1)[0] + '.mp3'
    clip.audio.write_audiofile(audio_path)

    import whisper

    # Transcribe audio to text with timestamps using Whisper
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)

    # Generate SRT file content
    srt_content = ""
    for i, segment in enumerate(result["segments"]):
        start_time = format_time(segment["start"])
        end_time = format_time(segment["end"])
        text = segment["text"]
        srt_content += f"{i+1}\n"
        srt_content += f"{start_time} --> {end_time}\n"
        srt_content += text + "\n\n"

    # Save SRT file
    srt_path = file_path.rsplit('.', 1)[0] + '.srt'
    with open(srt_path, 'w', encoding='utf-8') as file:
        for segment in result['segments']:
            start_time = format_time(segment["start"])
            end_time = format_time(segment["end"])
            text = segment["text"]
            segment_id = segment["id"]+1
            file.write(f"{segment_id}\n")
            file.write(f"{start_time} --> {end_time}\n")
            file.write(text + "\n\n")

    # Hardcode subtitles into video using FFmpeg
    output_path = file_path.rsplit('.', 1)[0] + '_with_subtitles.mp4'
    os.system(f'ffmpeg -i {file_path} -vf "subtitles={srt_path}" -c:a copy {output_path}')

    print(f"File processed successfully: {output_path}")

    return output_path

def format_time(time_in_seconds):
    # Your existing format_time function
    hours,remainder = divmod(time_in_seconds,3600)
    minutes,seconds = divmod(remainder,60)
    milliseconds = int((seconds-int(seconds))*1000)
    formatted_time = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d},{milliseconds:03d}"
    return formatted_time



if __name__ == '__main__':
    app.run(debug=True)

