from flask import Flask, request, send_file, jsonify
from rembg import remove
from PIL import Image
import io
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'service': 'Background Removal API',
        'endpoint': '/remove-background',
        'method': 'POST'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/remove-background', methods=['POST'])
def remove_background():
    """
    Remove background from uploaded image and return image with transparent background
    """
    try:
        # Check if file is present
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Read the image
        input_image = Image.open(file.stream)
        logger.info(f"Processing image: {file.filename}, Size: {input_image.size}")
        
        # Remove background using rembg
        output_image = remove(input_image)
        
        # Convert to bytes
        img_io = io.BytesIO()
        output_image.save(img_io, 'PNG')
        img_io.seek(0)
        
        logger.info(f"Successfully removed background for: {file.filename}")
        
        return send_file(
            img_io,
            mimetype='image/png',
            as_attachment=True,
            download_name='removed_bg.png'
        )
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use PORT environment variable for deployment platforms
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)