# Installation

Follow these steps to set up WeChatRSS on your server or local machine.

## Prerequisites

*   Python 3.10 or higher.
*   A WeChat account (to scan the login QR code).

## Step-by-Step Setup

### 1. Clone and Install Dependencies
```bash
git clone <repo_url>
cd WeChatRSS
pip install -r requirements.txt
```

### 2. Install Playwright Browsers
The system requires Chromium to be installed via Playwright:
```bash
python -m playwright install chromium
```

### 3. Initialize Database
Run the database script once to set up the schema and create the default admin.
```bash
python database.py
```
*   **Default Admin:** `admin` / `admin`

### 4. Perform Initial Authentication
This step must be done with a display (or via remote VNC/RDP) as it opens a browser window.
```bash
python auth.py
```
*   Scan the QR code with your phone.
*   Wait for the "Login detected!" message.

### 5. Start the Server
```bash
python main.py
```
Access the dashboard at `http://localhost:8000`.

## Deployment Recommendations

For production, it is recommended to use **Gunicorn** with the **Uvicorn** worker:
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Reverse Proxy
Always run WeChatRSS behind a reverse proxy like **Nginx** with SSL enabled (using Let's Encrypt). This protects your session cookies and dashboard access.
