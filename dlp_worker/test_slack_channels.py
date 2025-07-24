import requests
import os

# Token de autenticación de Slack (debes obtenerlo de tu app en https://api.slack.com/apps)
SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN", "xoxb-tu-token-aqui")
CHANNEL_LIST_URL = "https://slack.com/api/conversations.list"

headers = {
    "Authorization": f"Bearer {SLACK_TOKEN}"
}

params = {
    "limit": 10  # Puedes ajustar el límite
}

response = requests.get(CHANNEL_LIST_URL, headers=headers, params=params)

if response.status_code == 200:
    data = response.json()
    if data.get("ok"):
        print("Canales encontrados:")
        for channel in data.get("channels", []):
            print(f"ID: {channel['id']}, Nombre: {channel['name']}")
    else:
        print("Error en la respuesta de Slack:", data.get("error"))
else:
    print(f"Error HTTP: {response.status_code}")
    print(response.text)
