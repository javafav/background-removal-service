from flask import Flask, request, send_file, jsonify
from PIL import Image
import io
import logging
import os
import numpy as np
import cv2

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration for free tier
MAX_IMAGE_SIZE = 800
MAX_FILE_SIZE = 3 * 1024 * 1024  # 3MB

def remove_background_grabcut(image):
    """
    Remove background using OpenCV's GrabCut algorithm
    Lighter alternative to AI models, works well for photos with clear subjects
    """
    # Convert PIL to numpy array
    img_array = np.array(image)
    
    # Convert RGB to BGR for OpenCV
    if len(img_array.shape) == 3 and img_array.shape[2] == 3:
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    else:
        img_bgr = img_array
    
    # Create mask
    mask = np.zeros(img_bgr.shape[:2], np.uint8)
    
    # Define rectangle around the center (assume subject is in center)
    height, width = img_bgr.shape[:2]
    margin = int(min(width, height) * 0.05)
    rect = (margin, margin, width - margin * 2, height - margin * 2)
    
    # GrabCut algorithm
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    
    cv2.grabCut(img_bgr, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
    
    # Create binary mask
    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
    
    # Apply mask to create RGBA image
    img_rgba = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGBA)
    img_rgba[:, :, 3] = mask2 * 255
    
    # Convert back to PIL
    result = Image.fromarray(img_rgba, 'RGBA')
    return result

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'service': 'Background Removal API (Lightweight)',
        'endpoint': '/remove-background',
        'method': 'POST',
        'algorithm': 'GrabCut (OpenCV)',
        'max_file_size': '3MB',
        'max_dimensions': '800x800',
        'note': 'Works best with photos where subject is in center',
        'tip': 'For better results, ensure subject is clearly separated from background'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/remove-background', methods=['POST'])
def remove_background():
    """
    Remove background using GrabCut algorithm (memory efficient)
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': f'File too large. Max size is {MAX_FILE_SIZE // (1024*1024)}MB'}), 400
        
        # Read image
        input_image = Image.open(file.stream)
        
        # Convert to RGB if necessary
        if input_image.mode != 'RGB':
            input_image = input_image.convert('RGB')
        
        logger.info(f"Processing: {file.filename}, Size: {input_image.size}")
        
        # Resize if needed
        if input_image.width > MAX_IMAGE_SIZE or input_image.height > MAX_IMAGE_SIZE:
            input_image.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), Image.Resampling.LANCZOS)
            logger.info(f"Resized to: {input_image.size}")
        
        # Remove background
        output_image = remove_background_grabcut(input_image)
        
        # Save to bytes
        img_io = io.BytesIO()
        output_image.save(img_io, 'PNG', optimize=True)
        img_io.seek(0)
        
        logger.info(f"Success: {file.filename}")
        
        return send_file(
            img_io,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'no_bg_{file.filename.rsplit(".", 1)[0]}.png'
        )
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)