import requests
import json

# Configura la URL de la API Django para registrar un leak
API_URL = "http://localhost:8000/api/leaks/"  # Ajusta el puerto si es diferente

# Datos simulados para el leak
payload = {
    "message_content": "test@test.com",
    "channel": "C123456",         # ID de canal de prueba
    "author": "usuario_test",     # Usuario de prueba
    "timestamp": "2025-07-23T22:00:00Z",  # Timestamp de prueba
    "pattern": 1                   # ID del patrón en la base de datos
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(API_URL, data=json.dumps(payload), headers=headers)

if response.status_code == 201:
    print("DetectedLeak registrado correctamente en el DLP API.")
    print("Respuesta:", response.json())
else:
    print(f"Error al registrar DetectedLeak: {response.status_code}")
    print(response.text)
