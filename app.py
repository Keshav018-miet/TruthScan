import os
import uuid
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename
import json

from database import (
    init_db, save_record, get_all_records, get_record_by_id,
    create_user, verify_user_password, get_user_by_username
)
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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return redirect(request.url)
            
        success, user = verify_user_password(username, password)
        if success:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            flash(f"Welcome back, {user['username']}!", 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(request.url)
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return redirect(request.url)
            
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(request.url)
            
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return redirect(request.url)
            
        success, message = create_user(username, email, password)
        if success:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'error')
            return redirect(request.url)
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/news', methods=['GET', 'POST'])
@login_required
def news_analysis():
    if request.method == 'POST':
        text = request.form.get('news_text', '')
        headline = request.form.get('headline', '')
        channel_url = request.form.get('channel_url', '')
        
        if not text:
            flash('Please enter news text to analyze.', 'error')
            return redirect(request.url)
        
        # Analyze
        full_text = f"{headline}. {text}" if headline else text
        result = nlp_model.predict(full_text, channel_url=channel_url)
        
        record_id = str(uuid.uuid4())
        
        metadata = {
            "text_length": len(text),
            "channel_url": channel_url,
            "source_verification": result.get("source_verification")
        }
        
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
            'metadata_json': json.dumps(metadata),
            'fact_check_info': result['fact_check_info']
        }
        save_record(record_data)
        return redirect(url_for('report', record_id=record_id))
        
    return render_template('news.html')

@app.route('/image', methods=['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
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
@login_required
def history():
    records = get_all_records()
    return render_template('history.html', records=records)

@app.route('/report/<record_id>')
@login_required
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
