import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import json

from database import init_db, save_record, get_all_records, get_record_by_id
from utils import get_sha256, get_perceptual_hash, extract_exif, analyze_video_frames, dummy_deepfake_detect_image, dummy_deepfake_detect_video
from ml_model import nlp_model

app = Flask(__name__)
app.secret_key = "truthscan_secret_key_student_project"

UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # 50 MB max

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize DB
init_db()

ALLOWED_EXTENSIONS_IMAGE = {'png', 'jpg', 'jpeg'}
ALLOWED_EXTENSIONS_VIDEO = {'mp4', 'avi', 'mov'}

def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/news', methods=['GET', 'POST'])
def news_analysis():
    if request.method == 'POST':
        text = request.form.get('news_text', '')
        headline = request.form.get('headline', '')
        if not text:
            flash('Please enter news text to analyze.', 'error')
            return redirect(request.url)
        
        # Analyze
        full_text = f"{headline}. {text}"
        result = nlp_model.predict(full_text)
        
        record_id = str(uuid.uuid4())
        record_data = {
            'record_id': record_id,
            'analysis_type': 'News Analysis',
            'input_name': headline if headline else "News Snippet",
            'file_type': 'text',
            'file_size': len(full_text),
            'sha256_hash': None,
            'perceptual_hash': None,
            'result': result['prediction'],
            'confidence': result['confidence'],
            'metadata_json': json.dumps({"text_length": len(text)}),
            'fact_check_info': result['fact_check_info']
        }
        save_record(record_data)
        return redirect(url_for('report', record_id=record_id))
        
    return render_template('news.html')

@app.route('/image', methods=['GET', 'POST'])
def image_analysis():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        if file and allowed_file(file.filename, ALLOWED_EXTENSIONS_IMAGE):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Perform Analysis
            sha256 = get_sha256(filepath)
            phash = get_perceptual_hash(filepath)
            exif_data = extract_exif(filepath)
            result_str, confidence = dummy_deepfake_detect_image(filepath)
            file_size = os.path.getsize(filepath)
            
            record_id = str(uuid.uuid4())
            record_data = {
                'record_id': record_id,
                'analysis_type': 'Image Analysis',
                'input_name': filename,
                'file_type': filename.rsplit('.', 1)[1].lower(),
                'file_size': file_size,
                'sha256_hash': sha256,
                'perceptual_hash': phash,
                'result': result_str,
                'confidence': confidence,
                'metadata_json': json.dumps(exif_data),
                'fact_check_info': None
            }
            save_record(record_data)
            
            # Clean up uploaded file for space (optional, but good practice)
            # os.remove(filepath) 
            
            return redirect(url_for('report', record_id=record_id))
        else:
            flash('Allowed image types are -> png, jpg, jpeg', 'error')
            return redirect(request.url)
    return render_template('image.html')

@app.route('/video', methods=['GET', 'POST'])
def video_analysis():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        if file and allowed_file(file.filename, ALLOWED_EXTENSIONS_VIDEO):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            sha256 = get_sha256(filepath)
            video_info = analyze_video_frames(filepath)
            result_str, confidence = dummy_deepfake_detect_video(filepath)
            file_size = os.path.getsize(filepath)
            
            record_id = str(uuid.uuid4())
            record_data = {
                'record_id': record_id,
                'analysis_type': 'Video Analysis',
                'input_name': filename,
                'file_type': filename.rsplit('.', 1)[1].lower(),
                'file_size': file_size,
                'sha256_hash': sha256,
                'perceptual_hash': None,
                'result': result_str,
                'confidence': confidence,
                'metadata_json': json.dumps(video_info),
                'fact_check_info': None
            }
            save_record(record_data)
            
            return redirect(url_for('report', record_id=record_id))
        else:
            flash('Allowed video types are -> mp4, avi, mov', 'error')
            return redirect(request.url)
    return render_template('video.html')

@app.route('/integrity', methods=['GET', 'POST'])
def file_integrity():
    if request.method == 'POST':
        if 'file_a' not in request.files:
            flash('Original file is required.', 'error')
            return redirect(request.url)
            
        file_a = request.files['file_a']
        file_b = request.files.get('file_b')
        
        if file_a.filename == '':
            flash('Original file not selected', 'error')
            return redirect(request.url)
            
        filename_a = secure_filename(file_a.filename)
        filepath_a = os.path.join(app.config['UPLOAD_FOLDER'], filename_a)
        file_a.save(filepath_a)
        
        sha256_a = get_sha256(filepath_a)
        phash_a = None
        if allowed_file(filename_a, ALLOWED_EXTENSIONS_IMAGE):
            phash_a = get_perceptual_hash(filepath_a)
            
        result_str = "Integrity Checked"
        metadata = {"file_a_hash": sha256_a, "file_a_phash": phash_a}
        
        if file_b and file_b.filename != '':
            filename_b = secure_filename(file_b.filename)
            filepath_b = os.path.join(app.config['UPLOAD_FOLDER'], filename_b)
            file_b.save(filepath_b)
            
            sha256_b = get_sha256(filepath_b)
            phash_b = None
            if allowed_file(filename_b, ALLOWED_EXTENSIONS_IMAGE):
                phash_b = get_perceptual_hash(filepath_b)
                
            metadata["file_b_hash"] = sha256_b
            metadata["file_b_phash"] = phash_b
            
            if sha256_a == sha256_b:
                result_str = "Match (Identical)"
            else:
                result_str = "Mismatch (Altered)"
                
        record_id = str(uuid.uuid4())
        record_data = {
            'record_id': record_id,
            'analysis_type': 'File Integrity',
            'input_name': filename_a,
            'file_type': filename_a.rsplit('.', 1)[1].lower() if '.' in filename_a else 'unknown',
            'file_size': os.path.getsize(filepath_a),
            'sha256_hash': sha256_a,
            'perceptual_hash': phash_a,
            'result': result_str,
            'confidence': 100.0,
            'metadata_json': json.dumps(metadata),
            'fact_check_info': None
        }
        save_record(record_data)
        
        return redirect(url_for('report', record_id=record_id))
        
    return render_template('integrity.html')

@app.route('/history')
def history():
    records = get_all_records()
    return render_template('history.html', records=records)

@app.route('/report/<record_id>')
def report(record_id):
    record = get_record_by_id(record_id)
    if not record:
        flash("Record not found.", "error")
        return redirect(url_for('dashboard'))
        
    record_copy = dict(record)
    if record_copy.get('metadata_json'):
        record_copy['metadata'] = json.loads(record_copy['metadata_json'])
    else:
        record_copy['metadata'] = {}
        
    return render_template('report.html', record=record_copy)

if __name__ == '__main__':
    app.run(debug=True)
