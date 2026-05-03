import sys
import os
import uvicorn

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.main import app

if __name__ == "__main__":
    print("Starting WeChatRSS Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
