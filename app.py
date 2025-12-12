from flask import Flask, request, send_file, jsonify
from rembg import remove
from PIL import Image
import io
import logging
import os

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration for free tier
MAX_IMAGE_SIZE = 2048  # Limit image dimensions to reduce memory usage
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB max file size

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'service': 'Background Removal API',
        'endpoint': '/remove-background',
        'method': 'POST',
        'max_file_size': '5MB',
        'supported_formats': ['JPEG', 'PNG', 'WEBP'],
        'note': 'Service may take 30-60s to wake up after inactivity'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/remove-background', methods=['POST'])
def remove_background():
    """
    Remove background from uploaded image and return image with transparent background
    Optimized for free tier hosting
    """
    try:
        # Check if file is present
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
        
        # Read the image
        input_image = Image.open(file.stream)
        logger.info(f"Processing image: {file.filename}, Size: {input_image.size}, Format: {input_image.format}")
        
        # Resize if too large to reduce memory usage
        if input_image.width > MAX_IMAGE_SIZE or input_image.height > MAX_IMAGE_SIZE:
            logger.info(f"Resizing image from {input_image.size}")
            input_image.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), Image.Resampling.LANCZOS)
            logger.info(f"Resized to {input_image.size}")
        
        # Remove background using rembg
        output_image = remove(input_image)
        
        # Convert to bytes
        img_io = io.BytesIO()
        output_image.save(img_io, 'PNG', optimize=True)
        img_io.seek(0)
        
        logger.info(f"Successfully removed background for: {file.filename}")
        
        return send_file(
            img_io,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'no_bg_{file.filename.rsplit(".", 1)[0]}.png'
        )
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

if __name__ == '__main__':
    # Use PORT environment variable for deployment platforms
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)