import requests


def classify_vulnerability(cve_description):
    """
    Sends the CVE text to the local Qwen 2.5 Coder container to classify its severity/exploitability.
    """
    url = "http://llm_service:11434/api/generate"

    prompt = f"""
    You are an expert cybersecurity analyst. Analyze the following Open Source Vulnerability description.
    Classify the likelihood of this vulnerability being easily exploitable into exactly one of these three categories:
    "Not Promising", "Slightly Promising", or "Very Promising".

    Description: {cve_description}

    Return ONLY the classification string.
    """

    payload = {
        "model": "qwen2.5-coder",
        "prompt": prompt,

        # Set to false to wait for the complete response
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        result = response.json()

        classification = result.get("response", "").strip()

        valid_classes = ["Not Promising", "Slightly Promising", "Very Promising"]
        if classification in valid_classes:
            return classification

        # Default fallback
        return "Not Promising"

    except requests.exceptions.RequestException as e:
        print(f"LLM connection failed: {e}")
        return "Classification Failed"
