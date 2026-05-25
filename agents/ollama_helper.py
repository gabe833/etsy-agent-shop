import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.1:8b"


def ask_ollama(prompt, model=DEFAULT_MODEL):
    """
    Sends a prompt to Ollama and returns the model's response as text.
    """

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=180)
        response.raise_for_status()

        data = response.json()
        return data.get("response", "").strip()

    except requests.exceptions.ConnectionError:
        return "ERROR: Could not connect to Ollama. Make sure Ollama is running."

    except requests.exceptions.Timeout:
        return "ERROR: Ollama took too long to respond."

    except Exception as e:
        return f"ERROR: {e}"