"""
AI service integrations for image processing.
Supports ChatGPT Vision API, Azure Computer Vision, and Local OCR.
"""
import base64
import time
import requests
import json
from io import BytesIO
from PIL import Image


def send_to_chatgpt(image_base64, settings, prompt="What's in this image?", model="gpt-4o", max_tokens=300, timeout=30):
    """
    Sends an image and a prompt to OpenAI's ChatGPT with Vision API.

    Required `settings` keys:
      - chatgpt_api_key: Your OpenAI API key.

    Args:
      - image_base64: The base64-encoded string of the image.
      - settings: The application settings dictionary.
      - prompt: The text prompt to send along with the image.
      - model: The model to use (e.g., "gpt-4o", "gpt-4-vision-preview").
      - max_tokens: The maximum number of tokens to generate in the response.
      - timeout: The request timeout in seconds.

    Returns:
      - On success: The text content from the model's response.
      - On error: An error message string.
    """
    api_key = settings.get("chatgpt_api_key")
    if not api_key or api_key == "-":
        return "ChatGPT API key is missing or not set in settings."

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # OpenAI expects the image in a specific URL format, even for base64
    base64_image_url = f"data:image/png;base64,{image_base64}"

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": base64_image_url
                        }
                    }
                ]
            }
        ],
        "max_tokens": max_tokens
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()
        result = response.json()

        # Extract the content from the first choice
        if result.get("choices"):
            content = result["choices"][0].get("message", {}).get("content", "")
            return content.strip() if content else "Empty response from ChatGPT."
        else:
            return f"Unexpected response format from ChatGPT: {result}"

    except requests.exceptions.HTTPError as e:
        try:
            err_json = e.response.json()
        except Exception:
            err_json = None
        if err_json:
            return f"API request failed: {e} | details: {json.dumps(err_json)}"
        return f"API request failed: {e}"
    except requests.exceptions.RequestException as e:
        return f"API request failed: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


def send_to_azure(image_base64, settings, feature="ocr", *, timeout=30, read_poll_timeout=20, read_poll_interval=1.5):
    """
    Perform analysis on an image using Azure Computer Vision (direct endpoint).

    Required `settings` keys:
      - azure_endpoint: e.g. "https://your-resource-name.cognitiveservices.azure.com/"
      - azure_api_key:  Key1 or Key2 from the SAME resource (your-resource-name)

    Supported features:
      - "ocr"   : Legacy OCR (one call). Deprecated by Microsoft but kept for compatibility.
      - "read"  : Read 3.2 (two-step with polling). Recommended for OCR.
      - "describe": Returns a single caption string (if available).
      - "analyze" : Returns tags & categories (basic extraction demo).

    Returns:
      - On success: feature-specific value (see below)
      - On HTTP error: "API request failed: <...>"
      - On parse error: "JSON parsing error: <...>"
    """

    endpoint = (settings.get("azure_endpoint") or "").strip()
    key = settings.get("azure_api_key") or settings.get("azure_subscription_key")

    if not key:
        raise ValueError("Azure API key is missing in settings (use Key1/Key2 from your CV resource).")
    if not endpoint:
        raise ValueError("Azure endpoint is missing in settings.")
    # Normalize endpoint (no trailing slash to avoid //)
    if endpoint.endswith("/"):
        endpoint = endpoint[:-1]

    # Build base URLs safely
    def u(path):
        # path should NOT start with slash to avoid urljoin quirks across domains
        return f"{endpoint}/{path}"

    # Decode base64 image once
    try:
        image_bytes = base64.b64decode(image_base64)
    except Exception as e:
        return f"Image decode error: {e}"

    # Common headers for key auth
    bin_headers = {"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/octet-stream"}
    json_headers = {"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/json"}

    try:
        if feature == "read":
            # --- Read 3.2 (recommended) ---
            submit_url = u("vision/v3.2/read/analyze")
            # You can send bytes (octet-stream) or a JSON URL payload. We'll send bytes:
            resp = requests.post(submit_url, headers=bin_headers, data=image_bytes, timeout=timeout)
            resp.raise_for_status()

            # Poll the Operation-Location
            op_loc = resp.headers.get("Operation-Location")
            if not op_loc:
                # Some proxies strip headers; fallback to body (rare)
                try:
                    j = resp.json()
                except Exception:
                    j = {}
                # Return what we have to help debug
                return {"warning": "Operation-Location header missing", "submit_response": j}

            # Poll until succeeded/failed or timeout
            deadline = time.time() + read_poll_timeout
            while True:
                poll = requests.get(op_loc, headers={"Ocp-Apim-Subscription-Key": key}, timeout=timeout)
                poll.raise_for_status()
                j = poll.json()
                status = j.get("status")
                if status in ("succeeded", "failed"):
                    if status == "succeeded":
                        # Return lines joined for convenience; also return raw if you want it
                        lines = []
                        try:
                            for page in j["analyzeResult"]["readResults"]:
                                for line in page.get("lines", []):
                                    txt = line.get("text", "")
                                    if txt:
                                        lines.append(txt)
                        except Exception:
                            pass
                        return "\n".join(lines) if lines else j  # fall back to raw if nothing parsed
                    else:
                        return j  # failed with details
                if time.time() > deadline:
                    return {"error": "READ polling timed out", "last_response": j}
                time.sleep(read_poll_interval)

        elif feature == "ocr":
            # --- Legacy OCR endpoint (kept for compatibility) ---
            url = u("vision/v3.2/ocr")
            resp = requests.post(url, headers=bin_headers, data=image_bytes, timeout=timeout)
            resp.raise_for_status()
            j = resp.json()

            # Extract text lines similar to your original code
            lines = []
            for region in j.get("regions", []):
                for line in region.get("lines", []):
                    words = [w.get("text", "") for w in line.get("words", [])]
                    if any(words):
                        lines.append(" ".join(words))
            return "\n".join(lines) if lines else "Text not found"

        elif feature == "describe":
            # Simple caption using Describe
            url = u("vision/v3.2/describe")
            resp = requests.post(url, headers=bin_headers, data=image_bytes, timeout=timeout)
            resp.raise_for_status()
            j = resp.json()
            return j.get("description", {}).get("captions", [{}])[0].get("text", "Description not found")

        elif feature == "analyze":
            # Minimal example: call analyze and return tags/categories if present.
            # NOTE: Visual features are usually provided via query params; here we let service infer.
            url = u("vision/v3.2/analyze")
            # Without visualFeatures param, the service may return limited info; adapt as needed:
            resp = requests.post(url, headers=bin_headers, data=image_bytes, timeout=timeout)
            resp.raise_for_status()
            j = resp.json()
            tags = [t.get("name", "") for t in j.get("tags", [])]
            categories = [c.get("name", "") for c in j.get("categories", [])]
            return {"tags": tags, "categories": categories, "raw": j}

        else:
            return f"Unsupported feature: {feature}. Try one of: 'read', 'ocr', 'describe', 'analyze'."

    except requests.exceptions.HTTPError as e:
        # Show server message if available
        try:
            err_json = e.response.json()
        except Exception:
            err_json = None
        if err_json:
            return f"API request failed: {e} | details: {json.dumps(err_json)}"
        return f"API request failed: {e}"
    except requests.exceptions.RequestException as e:
        return f"API request failed: {e}"
    except ValueError as e:
        return f"JSON parsing error: {e}"


def send_to_local_ocr(image_base64, settings, timeout=30):
    """
    Perform OCR on an image using local Tesseract OCR.
    
    Args:
      - image_base64: The base64-encoded string of the image.
      - settings: The application settings dictionary (not used for local OCR).
      - timeout: The request timeout in seconds (not used for local OCR).
    
    Returns:
      - On success: The extracted text from the image.
      - On error: An error message string.
    """
    try:
        import pytesseract
        from PIL import Image
        import base64
        from io import BytesIO
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_base64)
        image_buffer = BytesIO(image_bytes)
        image = Image.open(image_buffer)
        
        # Perform OCR using pytesseract
        text = pytesseract.image_to_string(image)
        
        # Clean up the text
        text = text.strip()
        
        if text:
            return text
        else:
            return "Text not found"
            
    except ImportError:
        return "pytesseract library not installed. Please install it with: pip install pytesseract"
    except Exception as e:
        return f"Local OCR error: {e}"

