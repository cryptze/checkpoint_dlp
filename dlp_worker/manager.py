import asyncio
import json
import os
from dotenv import load_dotenv
from sqs_utils import get_or_create_queue # Importar la función de utilidad
from aiobotocore.session import get_session
from django.views.decorators.csrf import csrf_exempt

# Cargar variables de entorno
load_dotenv()

SQS_ENDPOINT_URL = os.getenv('SQS_ENDPOINT_URL', 'http://localhost:4566')
SQS_QUEUE_NAME = os.getenv('SQS_QUEUE_NAME', 'dlp-queue')


print("SQS_QUEUE_NAME:", os.getenv('SQS_QUEUE_NAME'))
print("SQS_ENDPOINT_URL:", os.getenv('SQS_ENDPOINT_URL'))
print("AWS_REGION:", os.getenv('AWS_REGION'))
print("AWS_ACCESS_KEY_ID:", os.getenv('AWS_ACCESS_KEY_ID'))
print("AWS_SECRET_ACCESS_KEY:", os.getenv('AWS_SECRET_ACCESS_KEY'))

class Manager:
    def __init__(self, queue_name: str, tasks: dict):
        self.queue_name = queue_name
        self.tasks = tasks
        self.session = get_session()
        self.queue_url = None

    async def initialize(self):
        """
        Inicializa la conexión con SQS y obtiene la URL de la cola.
        """
        print("Inicializando el Manager...")
        self.queue_url = await get_or_create_queue(self.queue_name, SQS_ENDPOINT_URL)
        print(f"Manager inicializado. Escuchando en la cola: {self.queue_url}")

    async def _get_messages(self):
        """
        Obtiene mensajes de la cola SQS de forma asíncrona.
        """
        if not self.queue_url:
            print("Error: La URL de la cola no ha sido inicializada.")
            return []

        try:
            async with self.session.create_client(
                'sqs',
                endpoint_url=SQS_ENDPOINT_URL,
                region_name=os.getenv('AWS_REGION', 'us-east-1'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', 'test'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', 'test')
            ) as client:
                response = await client.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=5
                )
                messages = response.get('Messages', [])
                
                if messages:
                    entries = [
                        {'Id': msg['MessageId'], 'ReceiptHandle': msg['ReceiptHandle']}
                        for msg in messages
                    ]
                    await client.delete_message_batch(QueueUrl=self.queue_url, Entries=entries)

                return messages
        except Exception as e:
            print(f"Error al conectar con SQS: {e}")
            return []

    async def main(self):
        """
        Bucle principal que obtiene mensajes y los procesa.
        """
        await self.initialize()
        print("Worker DLP iniciado. Esperando mensajes...")
        while True:
            messages = await self._get_messages()
            for message in messages:
                try:
                    body = json.loads(message['Body'])
                    task_name = body.get('task')
                    kwargs = body.get('kwargs', {})

                    if task_name in self.tasks:
                        task_function = self.tasks[task_name]
                        # Ejecutar la tarea directamente de forma asíncrona
                        await task_function(**kwargs)
                    else:
                        print(f"Tarea desconocida: {task_name}")
                except json.JSONDecodeError:
                    print(f"Error al decodificar mensaje: {message['Body']}")
                except Exception as e:
                    print(f"Error al procesar tarea: {e}")
            
            await asyncio.sleep(1)

if __name__ == "__main__":
    from tasks import TASKS

    manager = Manager(queue_name=SQS_QUEUE_NAME, tasks=TASKS)
    asyncio.run(manager.main()) 