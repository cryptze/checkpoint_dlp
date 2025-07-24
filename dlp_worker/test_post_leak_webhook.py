import requests
import json
import time

# Datos simulados del evento de Slack
message_text = "test@test.com"
channel_id = "C123456"
author = "usuario_test"
timestamp = str(time.time())
pattern_id = 1  # Ajusta según el patrón real en tu base de datos

leak_payload = {
    "message_content": message_text,
    "channel": channel_id,
    "author": author,
    "timestamp": timestamp,
    "pattern": pattern_id
}

API_URL = "http://localhost:8000/api/leaks/"
headers = {"Content-Type": "application/json"}

response = requests.post(API_URL, json=leak_payload, headers=headers)

if response.status_code == 201:
    print("DetectedLeak registrado correctamente en el DLP API.")
    print("Respuesta:", response.json())
else:
    print(f"Error al registrar DetectedLeak: {response.status_code}")
    print(response.text)
