import json
import os
import requests


def _get_ollama_url():
    # If inside Docker, use host.docker.internal
    if os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER'):
        return "http://host.docker.internal:11434/api/generate"
    return "http://localhost:11434/api/generate"

OLLAMA_URL = _get_ollama_url()
OLLAMA_MODEL = "gemma3:4b"


class AIAddressParser:
    _ollama_available = None

    @classmethod
    def _check_ollama(cls) -> bool:
        if cls._ollama_available is not None:
            return cls._ollama_available

        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=3)
            if resp.status_code == 200:
                models = [m['name'] for m in resp.json().get('models', [])]
                if any(OLLAMA_MODEL in m for m in models):
                    cls._ollama_available = True
                    print(f"✅ Ollama ready with model {OLLAMA_MODEL}")
                    return True
                else:
                    print(f"⚠️ Ollama running but model '{OLLAMA_MODEL}' not found. Available: {models}")
                    cls._ollama_available = False
                    return False
        except requests.ConnectionError:
            print("⚠️ Ollama not running. Start it with: ollama serve")
            cls._ollama_available = False
        except Exception as e:
            print(f"⚠️ Ollama check failed: {e}")
            cls._ollama_available = False

        return False

    @classmethod
    def parse(cls, title: str, description: str, breadcrumbs_text: str = "") -> dict | None:
        if not cls._check_ollama():
            return None

        desc_sample = description[:1500] if description else ""

        prompt = f"""Extract the property address from this Ukrainian real estate listing.

Title: {title}
Breadcrumbs: {breadcrumbs_text}
Description: {desc_sample}

Rules:
1. Extract: city, street, house number, region (oblast), district (raion).
2. Translate everything to Ukrainian (e.g., "Киев" -> "Київ", "ул." -> "вулиця").
3. Set null for missing fields.

Return ONLY valid JSON:
{{"city": "string or null", "street": "string or null", "number": "string or null", "district": "string or null", "region": "string or null"}}"""

        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 200
            }
        }

        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=60)

            if response.status_code == 200:
                result = response.json()
                text = result.get("response", "")

                # Clean and parse JSON
                clean_text = text.replace('```json', '').replace('```', '').strip()
                data = json.loads(clean_text)

                if not data.get('city'):
                    return None
                return data

            else:
                print(f"⚠️ Ollama Error {response.status_code}: {response.text[:200]}")
                return None

        except json.JSONDecodeError as e:
            print(f"⚠️ AI JSON parse error: {e}")
            return None
        except requests.ConnectionError:
            print("⚠️ Ollama connection lost")
            cls._ollama_available = None
            return None
        except Exception as e:
            print(f"⚠️ AI Request Error: {e}")
            return None
