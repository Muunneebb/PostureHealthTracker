#!/usr/bin/env python3
"""
Lightweight MJPEG HTTP server for real-time camera stream.
Serves binary JPEG frames from disk for high-speed, low-latency streaming.

Runs on http://localhost:8000/stream
"""

import time
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import logging

# ==========================================
# CONFIGURATION
# ==========================================
FRAME_FILE = Path('/tmp/posturehealthtracker_frame.jpg')
LISTEN_HOST = '0.0.0.0'
LISTEN_PORT = 8000
LOG_FILE = '/tmp/posturehealthtracker_mjpeg.log'

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==========================================
# MJPEG STREAM HANDLER
# ==========================================
class MJPEGHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MJPEG streaming."""

    def do_GET(self):
        """Handle GET requests for /stream endpoint."""
        if self.path == '/stream':
            self.stream_mjpeg()
        elif self.path == '/health':
            self.send_health()
        elif self.path == '/':
            self.send_index()
        else:
            self.send_error(404, 'Not Found')

    def stream_mjpeg(self):
        """Stream MJPEG data (Motion JPEG over HTTP)."""
        self.send_response(200)
        self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.end_headers()

        frame_interval = 0.033  # ~30fps target
        last_frame_size = 0

        try:
            while True:
                try:
                    # Read the latest JPEG frame from disk
                    if FRAME_FILE.exists():
                        with open(FRAME_FILE, 'rb') as f:
                            frame_data = f.read()

                        # Only send if frame has changed or is new
                        if len(frame_data) > 0:
                            # Write MJPEG boundary and headers
                            boundary = b'--frame\r\nContent-Type: image/jpeg\r\nContent-Length: ' + \
                                      str(len(frame_data)).encode() + b'\r\n\r\n'
                            self.wfile.write(boundary)
                            self.wfile.write(frame_data)
                            self.wfile.write(b'\r\n')
                            last_frame_size = len(frame_data)
                        else:
                            # Empty frame, wait and retry
                            time.sleep(0.01)
                    else:
                        # Frame file doesn't exist yet, wait
                        time.sleep(0.01)

                    # Pace the stream to ~30fps
                    time.sleep(frame_interval)

                except Exception as e:
                    logger.debug(f"Stream read error: {e}")
                    time.sleep(0.05)
                    continue

        except BrokenPipeError:
            logger.debug("Client disconnected from stream")
        except Exception as e:
            logger.warning(f"Stream error: {e}")
        finally:
            try:
                self.wfile.close()
            except:
                pass

    def send_health(self):
        """Health check endpoint returns 200 if frame file exists."""
        if FRAME_FILE.exists():
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"healthy"}')
        else:
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"no_frames"}')

    def send_index(self):
        """Serve a simple HTML test page."""
        html = b"""
<!DOCTYPE html>
<html>
<head>
    <title>PostureHealthTracker - MJPEG Stream</title>
    <style>
        body { font-family: Arial; margin: 20px; background: #f0f4fb; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #1a2942; }
        img { max-width: 100%; border: 1px solid #cad3e5; border-radius: 8px; }
        .status { padding: 10px; background: #e8f6ec; color: #2f8f46; border-radius: 6px; margin: 10px 0; }
        code { background: #eef2f7; padding: 2px 6px; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>PostureHealthTracker - Live Camera Stream</h1>
        <div class="status">✓ MJPEG Server running on :8000</div>
        <h2>Live Stream</h2>
        <img src="/stream" alt="Live camera stream" style="max-height: 600px;" />
        <h2>Integration</h2>
        <p>Use this URL in your HTML to embed the stream:</p>
        <code>&lt;img src="http://localhost:8000/stream" /&gt;</code>
        <p>Or from network: <code>http://&lt;pi-ip&gt;:8000/stream</code></p>
    </div>
</body>
</html>
"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def log_message(self, format, *args):
        """Suppress default logging to keep logs clean."""
        pass


# ==========================================
# SERVER STARTUP
# ==========================================
def start_mjpeg_server():
    """Start the MJPEG HTTP server."""
    server = HTTPServer((LISTEN_HOST, LISTEN_PORT), MJPEGHandler)
    logger.info(f"MJPEG server started on {LISTEN_HOST}:{LISTEN_PORT}")
    logger.info(f"Stream available at http://localhost:{LISTEN_PORT}/stream")
    logger.info(f"Health check at http://localhost:{LISTEN_PORT}/health")
    logger.info(f"Test page at http://localhost:{LISTEN_PORT}/")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
        server.shutdown()
        logger.info("Server stopped")


if __name__ == '__main__':
    start_mjpeg_server()
