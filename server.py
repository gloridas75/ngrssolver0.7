#!/usr/bin/env python3
"""
Simple HTTP server to serve the HTML viewer and provide file listing API.
This allows the HTML viewer to browse and list files from the output folder.
"""

import http.server
import socketserver
import json
import pathlib
from urllib.parse import urlparse, parse_qs
import os

PORT = 8000

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler with API endpoints for file operations."""
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        # API endpoint: list output files
        if parsed_path.path == '/api/output-files':
            self.list_output_files()
            return
        
        # API endpoint: list input files
        if parsed_path.path == '/api/input-files':
            self.list_input_files()
            return
        
        # API endpoint: get output file content
        if parsed_path.path.startswith('/api/output-file/'):
            filename = parsed_path.path.replace('/api/output-file/', '')
            self.get_output_file(filename)
            return
        
        # API endpoint: get input file content
        if parsed_path.path.startswith('/api/input-file/'):
            filename = parsed_path.path.replace('/api/input-file/', '')
            self.get_input_file(filename)
            return
        
        # Default: serve static files
        super().do_GET()
    
    def list_output_files(self):
        """List all JSON files in the output folder."""
        try:
            output_dir = pathlib.Path("output")
            if not output_dir.exists():
                self.send_json({'error': 'output folder not found'}, 404)
                return
            
            # Get all .json files
            files = []
            for file in sorted(output_dir.glob("*.json")):
                stat = file.stat()
                files.append({
                    'name': file.name,
                    'size': stat.st_size,
                    'modified': stat.st_mtime,
                    'path': f'output/{file.name}'
                })
            
            self.send_json({'files': files})
        except Exception as e:
            self.send_json({'error': str(e)}, 500)
    
    def list_input_files(self):
        """List all JSON files in the input folder."""
        try:
            input_dir = pathlib.Path("input")
            if not input_dir.exists():
                self.send_json({'error': 'input folder not found'}, 404)
                return
            
            # Get all .json files
            files = []
            for file in sorted(input_dir.glob("*.json")):
                stat = file.stat()
                files.append({
                    'name': file.name,
                    'size': stat.st_size,
                    'modified': stat.st_mtime,
                    'path': f'input/{file.name}'
                })
            
            self.send_json({'files': files})
        except Exception as e:
            self.send_json({'error': str(e)}, 500)
    
    def get_output_file(self, filename):
        """Serve a file from the output folder."""
        try:
            output_file = pathlib.Path("output") / filename
            if not output_file.exists() or not output_file.is_file():
                self.send_json({'error': 'file not found'}, 404)
                return
            
            with open(output_file, 'r') as f:
                data = json.load(f)
            self.send_json(data)
        except Exception as e:
            self.send_json({'error': str(e)}, 500)
    
    def get_input_file(self, filename):
        """Serve a file from the input folder."""
        try:
            input_file = pathlib.Path("input") / filename
            if not input_file.exists() or not input_file.is_file():
                self.send_json({'error': 'file not found'}, 404)
                return
            
            with open(input_file, 'r') as f:
                data = json.load(f)
            self.send_json(data)
        except Exception as e:
            self.send_json({'error': str(e)}, 500)
    
    def send_json(self, data, status_code=200):
        """Send a JSON response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))


if __name__ == '__main__':
    # Change to the script directory
    script_dir = pathlib.Path(__file__).parent
    os.chdir(script_dir)
    
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}/")
        print(f"Open http://localhost:{PORT}/viewer.html in your browser")
        print(f"Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
