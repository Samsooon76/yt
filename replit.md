# YouTube to MP3 Converter

## Overview

A Flask-based web application that allows users to convert YouTube videos to MP3 audio files. The application provides a modern, dark-themed interface where users can paste YouTube URLs, preview video information, and download the converted audio files. It features real-time progress tracking during the conversion process and handles the entire workflow from URL validation to file delivery.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 dark theme for responsive UI
- **Styling**: Custom CSS with Font Awesome icons for enhanced user experience
- **JavaScript**: Vanilla ES6 class-based architecture for client-side functionality
- **Progress Tracking**: Real-time progress updates using polling mechanism to track download and conversion status

### Backend Architecture
- **Framework**: Flask web framework with minimal configuration
- **Request Handling**: RESTful API endpoints for video validation, conversion, and file serving
- **Session Management**: Flask sessions with configurable secret key
- **Proxy Support**: ProxyFix middleware for deployment behind reverse proxies
- **Error Handling**: Comprehensive logging and user-friendly error messages

### Data Storage
- **In-Memory Storage**: Global dictionary for tracking conversion progress across requests
- **Temporary Files**: System temporary directory for storing converted audio files
- **File Cleanup**: Automatic cleanup of temporary files after serving downloads

### Video Processing
- **YouTube Integration**: yt-dlp library for robust YouTube video downloading and metadata extraction
- **Audio Conversion**: Built-in audio extraction to MP3 format
- **Progress Hooks**: Custom progress callback system for real-time status updates
- **URL Validation**: Pattern matching and URL parsing for YouTube link verification

### Threading Model
- **Background Processing**: Threaded conversion process to prevent blocking the main application
- **Progress Communication**: Thread-safe progress tracking using shared data structures
- **Async Operations**: Non-blocking download and conversion operations

## External Dependencies

### Core Libraries
- **Flask**: Web framework for HTTP request handling and routing
- **yt-dlp**: YouTube video downloading and audio extraction engine
- **Werkzeug**: WSGI utilities and middleware support

### Frontend Dependencies
- **Bootstrap 5**: Responsive CSS framework with dark theme support
- **Font Awesome**: Icon library for enhanced visual elements
- **CDN Resources**: External CDN delivery for styling and icons

### System Dependencies
- **Python Standard Library**: tempfile, threading, logging, urllib for core functionality
- **File System**: Temporary directory access for storing converted files
- **Network**: HTTP client capabilities for YouTube API interactions