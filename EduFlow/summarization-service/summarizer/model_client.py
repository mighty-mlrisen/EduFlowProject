import json
import os
import urllib.request
import urllib.error


def call_model_service(text: str) -> str:
    base_url = os.getenv("MODEL_SERVICE_URL", "http://host.docker.internal:8001")
    url = f"{base_url}/generate"
    data = json.dumps({"text": text}).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            result = json.loads(response.read())
        return result["summary"]
    except urllib.error.URLError as e:
        raise RuntimeError(f"Cannot reach model service at {base_url}: {e}")
    except (KeyError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Unexpected response from model service: {e}")
