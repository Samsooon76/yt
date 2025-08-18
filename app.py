import os
import logging
import json
import re
from urllib.parse import urlparse, parse_qs
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
import yt_dlp
import tempfile
import threading
import time
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Global dictionary to store conversion progress
conversion_progress = {}

class ProgressHook:
    def __init__(self, progress_id):
        self.progress_id = progress_id
        
    def __call__(self, d):
        if d['status'] == 'downloading':
            if 'total_bytes' in d and d['total_bytes']:
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
            elif 'total_bytes_estimate' in d and d['total_bytes_estimate']:
                percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
            else:
                percent = 0
            
            conversion_progress[self.progress_id] = {
                'status': 'downloading',
                'percent': round(percent, 1),
                'message': f'Téléchargement... {round(percent, 1)}%'
            }
        elif d['status'] == 'finished':
            conversion_progress[self.progress_id] = {
                'status': 'processing',
                'percent': 90,
                'message': 'Conversion en cours...'
            }

def is_valid_youtube_url(url):
    """Validate if the URL is a valid YouTube URL"""
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/v/[\w-]+',
        r'(?:https?://)?(?:m\.)?youtube\.com/watch\?v=[\w-]+'
    ]
    
    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return True
    return False

def get_video_info(url):
    """Extract video information without downloading"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            return {
                'title': info.get('title', 'Titre non disponible'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Inconnu'),
                'view_count': info.get('view_count', 0),
                'thumbnail': info.get('thumbnail', ''),
                'id': info.get('id', '')
            }
    except Exception as e:
        logger.error(f"Error extracting video info: {str(e)}")
        return None

def download_and_convert(url, progress_id):
    """Download and convert YouTube video to MP3"""
    try:
        # Create downloads directory if it doesn't exist
        downloads_dir = os.path.join(os.getcwd(), 'downloads')
        os.makedirs(downloads_dir, exist_ok=True)
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(downloads_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [ProgressHook(progress_id)],
            'quiet': False,
            'no_warnings': False,
        }
        
        conversion_progress[progress_id] = {
            'status': 'starting',
            'percent': 0,
            'message': 'Initialisation...'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'unknown')
            
            # Start download
            ydl.download([url])
            
            # Find the downloaded file
            safe_title = re.sub(r'[^\w\s-]', '', title).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            mp3_file = os.path.join(downloads_dir, f'{safe_title}.mp3')
            
            # Look for any mp3 file that matches
            for file in os.listdir(downloads_dir):
                if file.endswith('.mp3') and safe_title.lower() in file.lower():
                    mp3_file = os.path.join(downloads_dir, file)
                    break
            
            conversion_progress[progress_id] = {
                'status': 'completed',
                'percent': 100,
                'message': 'Conversion terminée!',
                'file_path': mp3_file,
                'filename': os.path.basename(mp3_file)
            }
            
            return mp3_file
            
    except Exception as e:
        logger.error(f"Error during conversion: {str(e)}")
        conversion_progress[progress_id] = {
            'status': 'error',
            'percent': 0,
            'message': f'Erreur: {str(e)}'
        }
        return None

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/validate', methods=['POST'])
def validate_url():
    """Validate YouTube URL and return video info"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL manquante'}), 400
            
        if not is_valid_youtube_url(url):
            return jsonify({'error': 'URL YouTube invalide'}), 400
            
        video_info = get_video_info(url)
        if not video_info:
            return jsonify({'error': 'Impossible de récupérer les informations de la vidéo'}), 400
            
        return jsonify({
            'valid': True,
            'info': video_info
        })
        
    except Exception as e:
        logger.error(f"Error validating URL: {str(e)}")
        return jsonify({'error': 'Erreur lors de la validation'}), 500

@app.route('/convert', methods=['POST'])
def convert_video():
    """Start video conversion"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url or not is_valid_youtube_url(url):
            return jsonify({'error': 'URL YouTube invalide'}), 400
            
        # Generate unique progress ID
        progress_id = f"conv_{int(time.time())}_{hash(url) % 10000}"
        
        # Start conversion in background thread
        thread = threading.Thread(
            target=download_and_convert, 
            args=(url, progress_id)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'progress_id': progress_id,
            'message': 'Conversion démarrée'
        })
        
    except Exception as e:
        logger.error(f"Error starting conversion: {str(e)}")
        return jsonify({'error': 'Erreur lors du démarrage de la conversion'}), 500

@app.route('/progress/<progress_id>')
def get_progress(progress_id):
    """Get conversion progress"""
    progress = conversion_progress.get(progress_id, {
        'status': 'not_found',
        'percent': 0,
        'message': 'Conversion non trouvée'
    })
    return jsonify(progress)

@app.route('/download/<progress_id>')
def download_file(progress_id):
    """Download the converted MP3 file"""
    try:
        progress = conversion_progress.get(progress_id)
        
        if not progress or progress.get('status') != 'completed':
            return jsonify({'error': 'Fichier non disponible'}), 404
            
        file_path = progress.get('file_path')
        filename = progress.get('filename')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'Fichier non trouvé'}), 404
            
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='audio/mpeg'
        )
        
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': 'Erreur lors du téléchargement'}), 500

# API Routes for iOS Shortcuts
@app.route('/api/convert', methods=['POST'])
def api_convert():
    """API endpoint for iOS Shortcuts - convert YouTube URL to MP3"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            url = request.json.get('url', '').strip()
        else:
            url = request.form.get('url', '').strip()
            
        if not url:
            return jsonify({'error': 'URL required', 'success': False}), 400
            
        if not is_valid_youtube_url(url):
            return jsonify({'error': 'Invalid YouTube URL', 'success': False}), 400
            
        # Get video info
        video_info = get_video_info(url)
        if not video_info:
            return jsonify({'error': 'Could not extract video information', 'success': False}), 400
            
        # Start conversion
        progress_id = f"api_conv_{int(time.time())}_{hash(url) % 10000}"
        
        # For API, we'll do synchronous conversion (blocking)
        # This is simpler for iOS Shortcuts
        file_path = download_and_convert(url, progress_id)
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'Conversion failed', 'success': False}), 500
            
        return jsonify({
            'success': True,
            'title': video_info['title'],
            'progress_id': progress_id,
            'download_url': url_for('download_file', progress_id=progress_id, _external=True)
        })
        
    except Exception as e:
        logger.error(f"API conversion error: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/info', methods=['POST'])
def api_info():
    """API endpoint to get video information only"""
    try:
        if request.is_json:
            url = request.json.get('url', '').strip()
        else:
            url = request.form.get('url', '').strip()
            
        if not url:
            return jsonify({'error': 'URL required', 'success': False}), 400
            
        if not is_valid_youtube_url(url):
            return jsonify({'error': 'Invalid YouTube URL', 'success': False}), 400
            
        video_info = get_video_info(url)
        if not video_info:
            return jsonify({'error': 'Could not extract video information', 'success': False}), 400
            
        return jsonify({
            'success': True,
            'info': video_info
        })
        
    except Exception as e:
        logger.error(f"API info error: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
