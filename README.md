# MinIO Share

A simple Flask web application for sharing files using MinIO object storage. The application allows users to configure their MinIO settings directly in the browser and provides an easy-to-use interface for uploading and sharing files.

## Features

- Browser-based MinIO configuration
- File upload functionality
- File listing with size and last modified date
- Generate shareable links for files
- Bootstrap-based responsive UI
- Copy-to-clipboard functionality for share links

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open your browser and navigate to `http://localhost:5000`

## Usage

1. First Visit:
   - You'll be presented with the MinIO configuration page
   - Enter your MinIO server details:
     - Endpoint (e.g., "play.min.io:9000")
     - Access Key
     - Secret Key
     - Bucket Name
     - Choose whether to use HTTPS

2. After Configuration:
   - Upload files using the upload form at the top of the page
   - View all uploaded files in the table below
   - Click the "Share" button next to any file to generate a shareable link
   - Use the copy button in the share dialog to copy the link to your clipboard

## Security Notes

- The MinIO configuration is stored in the browser session
- No sensitive information is stored on the server
- Share links are generated with a 1-hour expiration time
- Make sure to use HTTPS in production environments

## Requirements

- Python 3.7+
- Flask
- MinIO Python Client
- Modern web browser with JavaScript enabled
