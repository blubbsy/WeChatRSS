import sys
import os
import asyncio

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.auth_ultimate import run

if __name__ == "__main__":
    asyncio.run(run())
