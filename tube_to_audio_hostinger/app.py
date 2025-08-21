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

# Optional FFmpeg path detection
def _detect_ffmpeg_path():
    # Priority: env var, then local bin/ffmpeg, else None
    env_path = os.environ.get("FFMPEG_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path
    local_path = os.path.join(os.getcwd(), "bin", "ffmpeg")
    if os.path.isfile(local_path):
        return local_path
    return None

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
    
    # Try multiple configurations for maximum compatibility
    configs = [
        # Configuration 1: Most compatible
        {
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios'],
                    'skip': ['dash', 'hls']
                }
            }
        },
        # Configuration 2: Android fallback
        {
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'com.google.android.youtube/19.09.36 (Linux; U; Android 11) gzip',
            'extractor_args': {
                'youtube': {
                    'player_client': ['android'],
                    'skip': ['dash']
                }
            }
        },
        # Configuration 3: Basic web fallback
        {
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
    ]
    
    for i, ydl_opts in enumerate(configs):
        try:
            logger.debug(f"Trying configuration {i+1} for URL: {url}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if info:
                    logger.debug(f"Successfully extracted info with config {i+1}: {info.get('title', 'Unknown')}")
                    
                    return {
                        'title': info.get('title', 'Titre non disponible'),
                        'duration': info.get('duration', 0),
                        'uploader': info.get('uploader', 'Inconnu'),
                        'view_count': info.get('view_count', 0),
                        'thumbnail': info.get('thumbnail', ''),
                        'id': info.get('id', '')
                    }
                    
        except Exception as e:
            logger.warning(f"Configuration {i+1} failed: {str(e)}")
            continue
    
    logger.error(f"All configurations failed for URL: {url}")
    return None

def download_and_convert(url, progress_id):
    """Download and convert YouTube video to MP3"""
    try:
        # Create downloads directory if it doesn't exist
        downloads_dir = os.path.join(os.getcwd(), 'downloads')
        os.makedirs(downloads_dir, exist_ok=True)
        
        # Detect ffmpeg location if available (Hostinger/shared hosting friendly)
        ffmpeg_path = _detect_ffmpeg_path()
        
        # Configure yt-dlp options with iOS client for better compatibility
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(downloads_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            # Use custom ffmpeg if provided
            **({ 'ffmpeg_location': ffmpeg_path } if ffmpeg_path else {}),
            'progress_hooks': [ProgressHook(progress_id)],
            'quiet': False,
            'no_warnings': False,
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios'],
                    'skip': ['dash', 'hls']
                }
            }
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
            
            # Find the downloaded MP3 file
            mp3_file = None
            
            # Look for the most recently created MP3 file
            mp3_files = []
            for file in os.listdir(downloads_dir):
                if file.endswith('.mp3'):
                    file_path = os.path.join(downloads_dir, file)
                    mp3_files.append((file_path, os.path.getctime(file_path)))
            
            if mp3_files:
                # Sort by creation time and get the most recent
                mp3_files.sort(key=lambda x: x[1], reverse=True)
                mp3_file = mp3_files[0][0]
            
            if not mp3_file or not os.path.exists(mp3_file):
                # Fallback: look for any mp3 file that might match the title
                safe_title = re.sub(r'[^\w\s-]', '', title).strip().lower()
                for file in os.listdir(downloads_dir):
                    if file.endswith('.mp3'):
                        file_lower = file.lower()
                        # Check if any words from the title are in the filename
                        title_words = safe_title.split()
                        if any(word in file_lower for word in title_words if len(word) > 3):
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
            return jsonify({
                'error': 'Impossible de récupérer les informations de la vidéo',
                'details': 'Restrictions YouTube sur serveurs cloud. Essayez une vidéo publique récente.',
                'suggestion': 'Certaines vidéos fonctionnent mieux que d\'autres sur les serveurs hébergés.'
            }), 400
            
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
        downloads_dir = os.path.join(os.getcwd(), 'downloads')
        file_path = None
        filename = None
        
        # First, try to get from progress if available
        progress = conversion_progress.get(progress_id)
        if progress and progress.get('status') == 'completed':
            file_path = progress.get('file_path')
            filename = progress.get('filename')
            
            if file_path and os.path.exists(file_path):
                logger.debug(f"Using file from progress: {file_path}")
            else:
                file_path = None
        
        # If no valid file from progress, find any available MP3 file
        if not file_path:
            mp3_files = [f for f in os.listdir(downloads_dir) if f.endswith('.mp3')]
            
            if mp3_files:
                # Get the most recent MP3 file
                latest_file = max(mp3_files, key=lambda x: os.path.getctime(os.path.join(downloads_dir, x)))
                file_path = os.path.join(downloads_dir, latest_file)
                filename = latest_file
                logger.debug(f"Using most recent file: {file_path}")
            else:
                logger.error(f"No MP3 files found in downloads directory")
                return jsonify({'error': 'Aucun fichier MP3 disponible'}), 404
        
        if not os.path.exists(file_path):
            logger.error(f"File does not exist: {file_path}")
            return jsonify({'error': 'Fichier non trouvé'}), 404
            
        # Clean the filename for download
        clean_filename = re.sub(r'[^\w\s\-\.]', '', filename)
        clean_filename = re.sub(r'[\-\s]+', '-', clean_filename)
        if not clean_filename.endswith('.mp3'):
            clean_filename += '.mp3'
            
        logger.debug(f"Sending file: {file_path} as {clean_filename}")
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=clean_filename,
            mimetype='audio/mpeg'
        )
        
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': 'Erreur lors du téléchargement'}), 500

# Debug route to see current conversions
@app.route('/debug/conversions')
def debug_conversions():
    """Debug endpoint to see current conversions"""
    return jsonify({
        'conversions': conversion_progress,
        'downloads_dir_files': os.listdir(os.path.join(os.getcwd(), 'downloads'))
    })

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
