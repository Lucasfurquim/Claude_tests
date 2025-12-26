"""
Daily scheduled run script
Can be used with Task Scheduler (Windows) or cron (Linux/Mac)
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import main

if __name__ == "__main__":
    print("Running daily news analysis...")
    main()
