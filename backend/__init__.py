# Backend Module
"""
Loads environment variables from the project's .env file as soon as any
backend module is imported.

This must happen here (at package import time) because modules like db.py and
llm.py read os.getenv(...) at import/construction time. Without it, GOOGLE_API_KEY
and DATABASE_URL are never populated and analysis fails with
"GOOGLE_API_KEY not provided".
"""

from pathlib import Path

from dotenv import load_dotenv

# Project root is the parent of the backend/ package
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# override=False so real environment variables (e.g. in production/Docker)
# always win over the local .env file.
load_dotenv(dotenv_path=ENV_FILE, override=False)
