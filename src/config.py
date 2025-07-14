import os
from httpx import Timeout

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
} if GITHUB_TOKEN else {}

# Standard timeout settings for all requests
TIMEOUT = Timeout(
    connect=15.0,
    read=60.0,
    write=15.0,
    pool=10.0
)
