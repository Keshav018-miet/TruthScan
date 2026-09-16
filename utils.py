import hashlib
import os
import cv2
import imagehash
from PIL import Image
from PIL.ExifTags import TAGS
import exifread

def get_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_perceptual_hash(filepath):
    try:
        img = Image.open(filepath)
        return str(imagehash.phash(img))
    except Exception as e:
        print(f"Error generating phash: {e}")
        return None

def extract_exif(filepath):
    metadata = {}
    try:
        # Try ExifRead first for deeper metadata
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            for tag in tags.keys():
                if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
                    metadata[tag] = str(tags[tag])
                    
        # If nothing found, try Pillow
        if not metadata:
            img = Image.open(filepath)
            exif = img.getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    metadata[tag] = str(value)
    except Exception as e:
        print(f"Error extracting EXIF: {e}")
        
    return metadata

def analyze_video_frames(filepath, num_frames=5):
    """
    Extracts a few frames from the video to simulate analysis.
    Returns basic video info.
    """
    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        return {"error": "Could not open video file."}
    
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps if fps > 0 else 0
    
    frames_extracted = 0
    # Actually extract a few frames just to prove it works
    for i in range(min(num_frames, frame_count)):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i * (frame_count // num_frames))
        ret, frame = cap.read()
        if ret:
            frames_extracted += 1
            
    cap.release()
    
    return {
        "frame_count": frame_count,
        "fps": fps,
        "resolution": f"{width}x{height}",
        "duration_seconds": round(duration, 2),
        "frames_analyzed": frames_extracted
    }

def dummy_deepfake_detect_image(filepath):
    # This is a placeholder for a real deepfake model.
    # In a real scenario, this would load a PyTorch/TF model.
    # We will simulate a result based on arbitrary factors or just random for demonstration.
    # Here we'll just check if it has metadata. Lack of metadata can be a tiny flag, but we'll just return a static-ish result.
    size = os.path.getsize(filepath)
    # Pseudo-random but deterministic result
    confidence = (size % 50) + 40 # 40 to 89
    if size % 2 == 0:
        return "Potentially Real", confidence
    else:
        return "Potentially Manipulated", confidence

def dummy_deepfake_detect_video(filepath):
    size = os.path.getsize(filepath)
    confidence = (size % 40) + 50 # 50 to 89
    if size % 3 == 0:
        return "Potentially Manipulated", confidence
    else:
        return "Potentially Real", confidence
