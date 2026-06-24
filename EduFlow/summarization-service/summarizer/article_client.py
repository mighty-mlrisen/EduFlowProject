import os
import json
import urllib.request
import urllib.error


def fetch_article_text(article_id: int) -> str:
    base_url = os.getenv("ARTICLE_SERVICE_URL", "http://localhost:8080")
    url = f"{base_url}/internal/article/{article_id}/text"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
        return data["text"]
    except urllib.error.URLError as e:
        raise RuntimeError(f"Cannot reach article service: {e}")
    except (KeyError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Unexpected response from article service: {e}")
