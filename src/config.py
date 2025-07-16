import os
from dotenv import load_dotenv
from httpx import Timeout

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
} if GITHUB_TOKEN else {}

TIMEOUT = Timeout(
    connect=15.0,
    read=60.0,
    write=15.0,
    pool=10.0
)
