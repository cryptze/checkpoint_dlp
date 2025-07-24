import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import DetectedLeak, Pattern
import os
import boto3
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics
from .models import Pattern, DetectedLeak
from .serializers import PatternSerializer, DetectedLeakSerializer
import requests

def get_slack_username(user_id, token):
    url = f"https://slack.com/api/users.info?user={user_id}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    data = resp.json()
    if data.get("ok"):
        profile = data["user"].get("profile", {})
        return (
            profile.get("display_name") or
            profile.get("real_name") or
            data["user"].get("real_name") or
            data["user"].get("name") or
            user_id
        )
    return user_id

def get_slack_channel_name(channel_id, token):
    url = f"https://slack.com/api/conversations.info?channel={channel_id}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    data = resp.json()
    if data.get("ok"):
        return data["channel"].get("name", channel_id)
    return channel_id

class PatternList(generics.ListAPIView):
    queryset = Pattern.objects.all()
    serializer_class = PatternSerializer

class DetectedLeakCreate(generics.CreateAPIView):
    queryset = DetectedLeak.objects.all()
    serializer_class = DetectedLeakSerializer

@csrf_exempt
def slack_events_webhook(request):
    if request.method != "POST":
        return HttpResponse("Método no permitido", status=405)

    body_unicode = request.body.decode('utf-8')
    if not body_unicode:
        print("Cuerpo vacío recibido en /slack/events/")
        return HttpResponse("Cuerpo vacío", status=400)

    try:
        body = json.loads(body_unicode)
    except Exception as e:
        print("Error decodificando JSON en /slack/events/:", e)
        print("Contenido recibido:", body_unicode)
        return HttpResponse("JSON inválido", status=400)

    # Prints de depuración para variables de entorno SQS
    import os
    print("SQS_QUEUE_NAME:", os.getenv('SQS_QUEUE_NAME'))
    print("SQS_ENDPOINT_URL:", os.getenv('SQS_ENDPOINT_URL'))
    print("AWS_REGION:", os.getenv('AWS_REGION'))
    print("AWS_ACCESS_KEY_ID:", os.getenv('AWS_ACCESS_KEY_ID'))
    print("AWS_SECRET_ACCESS_KEY:", os.getenv('AWS_SECRET_ACCESS_KEY'))

    # --- 1. Verificación de la URL de Slack ---
    if 'challenge' in body:
        return HttpResponse(body['challenge'])

    # --- 2. Procesamiento de eventos reales ---
    event = body.get('event', {})
    print("Evento recibido de Slack:", event)

    # Ignorar mensajes de bots para evitar bucles infinitos
    if event.get('subtype') == 'bot_message':
        return HttpResponse(status=200)

    # Procesar un mensaje de texto
    if event.get('type') == 'message' and 'text' in event:
        print("Mensaje de Slack recibido:", event)
        message_text = event.get('text')
        channel_id = event.get('channel')
        message_ts = event.get('ts') # Timestamp, sirve como ID único del mensaje
        user_id = event.get('user', '')  # <-- Asegúrate de obtener el user

        # Obtén el token de Slack desde las variables de entorno
        slack_token = os.getenv('SLACK_BOT_TOKEN')

        # Obtén los nombres legibles
        user_name = get_slack_username(user_id, slack_token)
        channel_name = get_slack_channel_name(channel_id, slack_token)

        # Formatear la tarea para el worker DLP
        task_payload = {
            'task': 'scan_message',
            'kwargs': {
                'content': message_text,
                'channel': channel_name,  # <-- nombre legible
                'ts': message_ts,
                'user': user_name         # <-- nombre legible
            }
        }

        # Enviar la tarea a la cola SQS (LocalStack)
        try:
            sqs = boto3.client(
                'sqs',
                endpoint_url=os.getenv('SQS_ENDPOINT_URL'), # ej: 'http://localstack:4566'
                region_name=os.getenv('AWS_REGION'), # ej: 'us-east-1'
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), # ej: 'test'
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY') # ej: 'test'
            )
            queue_url = sqs.get_queue_url(QueueName=os.getenv('SQS_QUEUE_NAME'))['QueueUrl']

            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(task_payload)
            )
        except Exception as e:
            print(f"Error al enviar a SQS: {e}")
            return HttpResponse(status=500)

    # Podrías añadir lógica para event.get('type') == 'file_shared' aquí

    return HttpResponse(status=200)