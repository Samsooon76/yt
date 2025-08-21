// YouTube to MP3 Converter JavaScript

class YouTubeConverter {
    constructor() {
        this.currentProgressId = null;
        this.progressInterval = null;
        this.initializeElements();
        this.bindEvents();
    }

    initializeElements() {
        // Get DOM elements
        this.urlInput = document.getElementById('youtube-url');
        this.validateBtn = document.getElementById('validate-btn');
        this.convertBtn = document.getElementById('convert-btn');
        this.videoInfo = document.getElementById('video-info');
        this.progressContainer = document.getElementById('progress-container');
        this.downloadContainer = document.getElementById('download-container');
        this.errorContainer = document.getElementById('error-container');
        
        // Video info elements
        this.videoThumbnail = document.getElementById('video-thumbnail');
        this.videoTitle = document.getElementById('video-title');
        this.videoUploader = document.getElementById('video-uploader');
        this.videoDuration = document.getElementById('video-duration');
        this.videoViews = document.getElementById('video-views');
        
        // Progress elements
        this.progressBar = document.getElementById('progress-bar');
        this.progressPercent = document.getElementById('progress-percent');
        this.progressMessage = document.getElementById('progress-message');
        
        // Download and error elements
        this.downloadLink = document.getElementById('download-link');
        this.errorMessage = document.getElementById('error-message');
    }

    bindEvents() {
        // Validate button click
        this.validateBtn.addEventListener('click', () => this.validateUrl());
        
        // Convert button click
        this.convertBtn.addEventListener('click', () => this.startConversion());
        
        // Enter key in URL input
        this.urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.validateUrl();
            }
        });

        // Auto-validate when URL changes
        this.urlInput.addEventListener('input', () => {
            this.resetUI();
            if (this.urlInput.value.trim()) {
                this.validateBtn.disabled = false;
            } else {
                this.validateBtn.disabled = true;
                this.convertBtn.disabled = true;
            }
        });
    }

    resetUI() {
        // Hide all sections except input
        this.videoInfo.style.display = 'none';
        this.progressContainer.style.display = 'none';
        this.downloadContainer.style.display = 'none';
        this.errorContainer.style.display = 'none';
        
        // Reset buttons
        this.convertBtn.disabled = true;
        this.validateBtn.disabled = false;
        
        // Clear progress
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }

    showError(message) {
        this.errorMessage.textContent = message;
        this.errorContainer.style.display = 'block';
        
        // Auto-hide error after 5 seconds
        setTimeout(() => {
            this.errorContainer.style.display = 'none';
        }, 5000);
    }

    formatDuration(seconds) {
        if (!seconds) return 'Inconnue';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }

    formatViews(views) {
        if (!views) return '0';
        
        if (views >= 1000000) {
            return (views / 1000000).toFixed(1) + 'M vues';
        } else if (views >= 1000) {
            return (views / 1000).toFixed(1) + 'K vues';
        }
        return views.toLocaleString() + ' vues';
    }

    async validateUrl() {
        const url = this.urlInput.value.trim();
        
        if (!url) {
            this.showError('Veuillez entrer une URL YouTube valide');
            return;
        }

        // Show loading state
        this.validateBtn.disabled = true;
        this.validateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            const API_BASE = (window.API_BASE || '').replace(/\/$/, '');
            const response = await fetch(`${API_BASE}/validate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            });

            const data = await response.json();

            if (response.ok && data.valid) {
                // Show video info
                this.displayVideoInfo(data.info);
                this.convertBtn.disabled = false;
            } else {
                this.showError(data.error || 'URL YouTube invalide');
            }
        } catch (error) {
            console.error('Validation error:', error);
            this.showError('Erreur de connexion. Veuillez réessayer.');
        } finally {
            // Restore button
            this.validateBtn.disabled = false;
            this.validateBtn.innerHTML = '<i class="fas fa-search"></i>';
        }
    }

    displayVideoInfo(info) {
        // Set thumbnail
        this.videoThumbnail.src = info.thumbnail || '';
        this.videoThumbnail.alt = info.title || 'Video thumbnail';
        
        // Set video details
        this.videoTitle.textContent = info.title || 'Titre non disponible';
        this.videoUploader.textContent = info.uploader || 'Inconnu';
        this.videoDuration.textContent = this.formatDuration(info.duration);
        this.videoViews.textContent = this.formatViews(info.view_count);
        
        // Show video info section
        this.videoInfo.style.display = 'block';
        
        // Smooth scroll to video info
        this.videoInfo.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    async startConversion() {
        const url = this.urlInput.value.trim();
        
        if (!url) {
            this.showError('URL manquante');
            return;
        }

        // Disable convert button
        this.convertBtn.disabled = true;
        this.convertBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Conversion en cours...';

        try {
            const API_BASE = (window.API_BASE || '').replace(/\/$/, '');
            const response = await fetch(`${API_BASE}/convert`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            });

            const data = await response.json();

            if (response.ok) {
                this.currentProgressId = data.progress_id;
                this.showProgress();
                this.startProgressTracking();
            } else {
                this.showError(data.error || 'Erreur lors de la conversion');
                this.resetConvertButton();
            }
        } catch (error) {
            console.error('Conversion error:', error);
            this.showError('Erreur de connexion. Veuillez réessayer.');
            this.resetConvertButton();
        }
    }

    showProgress() {
        this.progressContainer.style.display = 'block';
        this.downloadContainer.style.display = 'none';
        this.progressContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    startProgressTracking() {
        this.progressInterval = setInterval(async () => {
            try {
                const API_BASE = (window.API_BASE || '').replace(/\/$/, '');
                const response = await fetch(`${API_BASE}/progress/${this.currentProgressId}`);
                const data = await response.json();

                this.updateProgress(data);

                if (data.status === 'completed') {
                    clearInterval(this.progressInterval);
                    this.showDownload();
                } else if (data.status === 'error') {
                    clearInterval(this.progressInterval);
                    this.showError(data.message || 'Erreur lors de la conversion');
                    this.resetConvertButton();
                }
            } catch (error) {
                console.error('Progress tracking error:', error);
                clearInterval(this.progressInterval);
                this.showError('Erreur lors du suivi de progression');
                this.resetConvertButton();
            }
        }, 1000);
    }

    updateProgress(data) {
        const percent = data.percent || 0;
        const message = data.message || 'Traitement en cours...';

        this.progressBar.style.width = percent + '%';
        this.progressBar.setAttribute('aria-valuenow', percent);
        this.progressPercent.textContent = percent + '%';
        this.progressMessage.textContent = message;

        // Update progress bar color based on status
        this.progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
        
        if (data.status === 'completed') {
            this.progressBar.classList.add('bg-success');
        } else if (data.status === 'error') {
            this.progressBar.classList.add('bg-danger');
        } else {
            this.progressBar.classList.add('bg-primary');
        }
    }

    showDownload() {
        this.progressContainer.style.display = 'none';
        this.downloadContainer.style.display = 'block';
        
        // Set download link
        const API_BASE = (window.API_BASE || '').replace(/\/$/, '');
        this.downloadLink.href = `${API_BASE}/download/${this.currentProgressId}`;
        
        this.downloadContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        this.resetConvertButton();
    }

    resetConvertButton() {
        this.convertBtn.disabled = false;
        this.convertBtn.innerHTML = '<i class="fas fa-download me-2"></i>Convertir en MP3';
    }
}

// Initialize the converter when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new YouTubeConverter();
});

// Add some utility functions for better UX
document.addEventListener('DOMContentLoaded', () => {
    // Add paste functionality
    const urlInput = document.getElementById('youtube-url');
    
    // Auto-focus on URL input
    urlInput.focus();
    
    // Handle paste events
    urlInput.addEventListener('paste', (e) => {
        setTimeout(() => {
            if (urlInput.value.trim()) {
                document.getElementById('validate-btn').click();
            }
        }, 100);
    });
    
    // Add keyboard shortcut for conversion (Ctrl/Cmd + Enter)
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const convertBtn = document.getElementById('convert-btn');
            if (!convertBtn.disabled) {
                convertBtn.click();
            }
        }
    });
});
