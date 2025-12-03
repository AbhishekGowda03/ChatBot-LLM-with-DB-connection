import requests
import json

def ask_llm(prompt):
    res = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt
        },
        stream=True
    )

    response_text = ""
    for line in res.iter_lines():
        if line:
            try:
                data = json.loads(line.decode("utf-8"))
                if "response" in data:
                    response_text += data["response"]
            except json.JSONDecodeError:
                continue

    return response_text
