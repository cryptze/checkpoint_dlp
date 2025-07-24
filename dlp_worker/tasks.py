import asyncio
import os
import re
import aiohttp
import json
from aiobotocore.session import get_session
from dotenv import load_dotenv

load_dotenv()

SQS_ENDPOINT_URL = os.getenv('SQS_ENDPOINT_URL')
SQS_QUEUE_NAME = os.getenv('SQS_QUEUE_NAME')
AWS_REGION = os.getenv('AWS_REGION')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
# URL base de la API de Django
DJANGO_API_URL = os.getenv('DJANGO_API_URL')
# Token de Slack para las acciones del bot
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')

async def get_slack_username(session, user_id):
    url = f"https://slack.com/api/users.info?user={user_id}"
    headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
    async with session.get(url, headers=headers) as resp:
        data = await resp.json()
        print("Respuesta de users.info:", data)  # <-- Este print es clave
        if data.get("ok"):
            profile = data["user"].get("profile", {})
            return (
                profile.get("display_name") or
                profile.get("real_name") or
                data["user"].get("real_name") or
                data["user"].get("name") or
                user_id
            )
        return user_id  # fallback

async def get_slack_channel_name(session, channel_id):
    url = f"https://slack.com/api/conversations.info?channel={channel_id}"
    headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
    async with session.get(url, headers=headers) as resp:
        data = await resp.json()
        if data.get("ok"):
            return data["channel"]["name"]
        return channel_id  # fallback

async def scan_message(content: str, channel: str, ts: str, user: str):
    """
    Tarea principal que escanea un mensaje en busca de fugas de datos.
    """
    print(f"Escaneando mensaje en canal {channel} de usuario {user}: '{content[:50]}...'")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Obtener nombres legibles
            user_name = await get_slack_username(session, user)
            channel_name = await get_slack_channel_name(session, channel)

            # --- Paso 1: Obtener patrones de la API de Django ---
            patterns_url = f"{DJANGO_API_URL}/patterns/"
            async with session.get(patterns_url) as response:
                if response.status != 200:
                    print(f"Error al obtener patrones: {response.status}")
                    return
                patterns = await response.json()

            print(f"Patrones obtenidos: {patterns}")  # Debug: mostrar patrones
            
            # --- Paso 2: Buscar coincidencias con Regex ---
            found_leak = None
            for pattern in patterns:
                print(f"Verificando patrón: {pattern['name']} con regex: {pattern['regex']}")  # Debug
                try:
                    if re.search(pattern['regex'], content, re.MULTILINE):
                        print(f"¡FUGA DETECTADA! Patrón: '{pattern['name']}' en contenido: '{content}'")
                        found_leak = pattern
                        break # Nos detenemos en la primera coincidencia
                except re.error as e:
                    print(f"Error en el patrón regex '{pattern['name']}': {e}")

            if found_leak:
                # --- Paso 3: Reportar la fuga a la API de Django ---
                leaks_url = f"{DJANGO_API_URL}/leaks/"
                leak_data = {
                    'pattern': found_leak['id'],
                    'message_content': content,
                    'channel': channel,   # <-- Solo el ID
                    'author': user,       # <-- Solo el ID
                    'timestamp': ts
                }
                async with session.post(leaks_url, json=leak_data) as post_response:
                    if post_response.status == 201:
                        print("Fuga registrada exitosamente en Django.")
                    else:
                        print(f"Error al registrar la fuga: {post_response.status} - {await post_response.text()}")

                # --- Paso 4 (Bonus): Actuar sobre el mensaje en Slack ---
                await reply_with_warning(session, channel, ts)

    except Exception as e:
        print(f"Error en la tarea scan_message: {e}")

async def reply_with_warning(session: aiohttp.ClientSession, channel: str, thread_ts: str):
    """
    Publica una respuesta de advertencia a un mensaje que contiene una fuga.
    """
    slack_api_url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json; charset=utf-8"
    }
    payload = {
        "channel": channel,
        "thread_ts": thread_ts,
        "text": ":warning: Este mensaje parece contener información sensible y viola las políticas de seguridad.",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":warning: *Posible Fuga de Datos Detectada*\nEste mensaje parece contener información sensible. Por favor, revísalo y elimínalo si es necesario."
                }
            }
        ]
    }
    
    async with session.post(slack_api_url, headers=headers, json=payload) as response:
        response_data = await response.json()
        if response_data.get('ok'):
            print(f"Respuesta de advertencia enviada al hilo {thread_ts} en el canal {channel}.")
        else:
            print(f"Error al enviar respuesta a Slack: {response_data.get('error')}")

# Diccionario que el Manager usará para encontrar la función correcta
TASKS = {
    'scan_message': scan_message,
}

async def process_task(task):
    """
    Procesa una tarea recibida del SQS
    """
    print(f"Procesando tarea: {task}")
    try:
        task_type = task.get('task')
        if task_type not in TASKS:
            print(f"Tipo de tarea desconocido: {task_type}")
            return
        
        task_func = TASKS[task_type]
        kwargs = task.get('kwargs', {})
        
        print(f"Ejecutando {task_type} con argumentos: {kwargs}")
        await task_func(**kwargs)
        
    except Exception as e:
        print(f"Error procesando tarea: {e}")

async def create_queue(sqs):
    """
    Crea una nueva cola SQS y espera hasta que esté disponible
    """
    print(f"Intentando crear cola: {SQS_QUEUE_NAME}")
    try:
        response = await sqs.create_queue(
            QueueName=SQS_QUEUE_NAME,
            Attributes={
                'DelaySeconds': '0',
                'MessageRetentionPeriod': '86400'  # 24 horas
            }
        )
        queue_url = response['QueueUrl']
        print(f"Cola creada: {queue_url}")
        
        # Esperar hasta que la cola esté disponible
        retries = 5
        while retries > 0:
            try:
                await sqs.get_queue_attributes(
                    QueueUrl=queue_url,
                    AttributeNames=['All']
                )
                print("Cola verificada y lista para usar")
                return queue_url
            except Exception as e:
                print(f"Esperando a que la cola esté disponible... {retries} intentos restantes")
                await asyncio.sleep(2)
                retries -= 1
        
        if retries == 0:
            raise Exception("La cola no estuvo disponible después de varios intentos")
        
        return queue_url
    except Exception as e:
        print(f"Error creando la cola: {str(e)}")
        raise

async def main_worker():
    print(f"Iniciando worker con endpoint: {SQS_ENDPOINT_URL}")
    session = get_session()
    async with session.create_client(
        'sqs',
        endpoint_url=SQS_ENDPOINT_URL,
        region_name=AWS_REGION,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_access_key_id=AWS_ACCESS_KEY_ID
    ) as sqs:
        # Intentar obtener o crear la cola con reintentos
        retries = 3
        queue_url = None
        
        while retries > 0 and queue_url is None:
            try:
                queue_url = (await sqs.get_queue_url(QueueName=SQS_QUEUE_NAME))['QueueUrl']
                print(f"Cola existente encontrada: {queue_url}")
            except Exception as e:
                print(f"Intento {4-retries}: Cola no encontrada, intentando crearla...")
                try:
                    queue_url = await create_queue(sqs)
                except Exception as create_error:
                    print(f"Error al crear la cola: {str(create_error)}")
                    if retries > 1:
                        await asyncio.sleep(5)
                retries -= 1
        
        if queue_url is None:
            raise Exception("No se pudo obtener o crear la cola después de varios intentos")
        print(f"Escuchando tareas en la cola: {SQS_QUEUE_NAME}")
        while True:
            response = await sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10
            )
            messages = response.get('Messages', [])
            for message in messages:
                body = json.loads(message['Body'])
                await process_task(body)
                await sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )