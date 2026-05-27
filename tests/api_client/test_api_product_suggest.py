import requests
import json

# TODO Port in zentrale Config
url = 'https://localhost:6000/api/process'

# API-Schlüssel (für die Authentifizierung)
headers = {
    'X-API-KEY': '1234567890abcdef',
    'Content-Type': 'application/json'
}

# JSON-Daten, die gesendet werden
data = {
    "name": "Alice",
    "age": 30,
    "location": "Berlin"
}

try:
    # Sende den POST-Request mit den JSON-Daten
    response = requests.post(url, headers=headers, data=json.dumps(data), verify=False)

    # Prüfe, ob die Anfrage erfolgreich war
    if response.status_code == 200:
        print("Server Response:", response.json())
    else:
        print(f"Fehler: {response.status_code}, Nachricht: {response.text}")

except Exception as e:
    print(f"Ein Fehler ist aufgetreten: {e}")