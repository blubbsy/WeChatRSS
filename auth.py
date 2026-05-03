import sys
import os
import asyncio

# Ensure the root directory is in sys.path so we can import 'src' as a package
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Also add 'src' to path so that modules inside 'src' can import each other directly
src_dir = os.path.join(root_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from src.auth import run

if __name__ == "__main__":
    asyncio.run(run())
