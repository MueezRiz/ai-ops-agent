import requests
import time

questions = [
    "What does standard shipping cost?",
    "How long does international shipping take?",
    "Can I return a worn item?",
    "How long do I have to return something?",
    "Can I cancel my order?",
    "How do I find my size?",
    "What payment methods do you accept?",
    "Can I use two discount codes at once?",
    "What are customer support hours?",
    "Does free shipping apply to express delivery?"
]

for q in questions:
    response = requests.post(
        "http://localhost:8000/chat",
        json={"message": q}
    )
    print(f"Q: {q}")
    print(f"Status: {response.status_code}")
    print(f"Raw: {response.text}")  # see exactly what the server sends back
    try:
        print(f"A: {response.json()}")
    except Exception as e:
        print(f"JSON parse error: {e}")
    print("-" * 50)
    time.sleep(1)