import os
from dotenv import load_dotenv
from httpx import Timeout

load_dotenv()

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

GITHUB_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

TIMEOUT = Timeout(
    connect=15.0,
    read=60.0,
    write=15.0,
    pool=10.0
)
