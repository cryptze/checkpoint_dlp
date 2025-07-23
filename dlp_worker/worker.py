import asyncio
import json
import os
from typing import Dict, Any, Tuple, Callable

import aiobotocore


class Manager:
    def __init__(self, queue_name: str, tasks: Dict[str, Callable]):
        self.queue_name = queue_name
        self.tasks = tasks
        self.session = aiobotocore.get_session()
        self.aws_region = os.environ.get("AWS_REGION", "us-east-1")
        self.endpoint_url = "http://queue:4566"
        self.aws_access_key_id = "test"
        self.aws_secret_access_key = "test"

    async def _get_messages(self):
        """Leer y obtener mensajes de la cola SQS
        """
        try:
            async with self.session.create_client(
                "sqs",
                region_name=self.aws_region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
            ) as client:
                try:
                    response = await client.get_queue_url(QueueName=self.queue_name)
                    queue_url = response["QueueUrl"]
                except client.exceptions.QueueDoesNotExist:
                    print(f"Queue '{self.queue_name}' not found. Creating it...")
                    response = await client.create_queue(QueueName=self.queue_name)
                    queue_url = response["QueueUrl"]
                    print(f"Queue '{self.queue_name}' created with URL: {queue_url}")

                print("Polling for messages...")
                response = await client.receive_message(
                    QueueUrl=queue_url,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=5,
                )

                messages = response.get("Messages", [])
                for msg in messages:
                    # Ensure message is deleted after processing
                    await client.delete_message(
                        QueueUrl=queue_url, ReceiptHandle=msg["ReceiptHandle"]
                    )
                return messages
        except Exception as e:
            print(f"An error occurred while getting messages: {e}")
            return []

    async def main(self):
        """Para una tarea dada:
        >>> async def say(something):
                pass
        Se espera que los mensajes de la cola tengan el formato:
        >>> message = dict(task='say', args=('something',), kwargs={})
        >>> message = dict(task='say', args=(), kwargs={'something': 'something else'})
        """
        print("DLP Worker started...")
        while True:
            messages = await self._get_messages()
            for message in messages:
                try:
                    print(f"Received message: {message['Body']}")
                    body = json.loads(message["Body"])
                    task_name = body.get("task")
                    args: Tuple[Any, ...] = tuple(body.get("args", ()))
                    kwargs: Dict[str, Any] = body.get("kwargs", {})
                    task = self.tasks.get(task_name)
                    if task:
                        asyncio.create_task(task(*args, **kwargs))
                    else:
                        print(f"Task '{task_name}' not found.")
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from message: {message['Body']}")
                except Exception as e:
                    print(f"Error processing message: {e}")

            await asyncio.sleep(1)


# --- Definición de Tareas ---
async def process_text_for_dlp(text: str):
    """
    Placeholder for a real DLP processing task.
    This function will contain the logic to scan text for sensitive data.
    """
    print(f"--- DLP SCAN ---")
    print(f"Scanning text: '{text[:30]}...'")
    # In a real scenario, you would use a library or service to check for PII,
    # credit card numbers, etc.
    await asyncio.sleep(2)  # Simulate I/O bound operation
    print(f"--- SCAN COMPLETE ---")


# --- Punto de Entrada ---
if __name__ == "__main__":
    # El diccionario `tasks` mapea los nombres de las tareas a las funciones asíncronas
    # que deben ejecutarse.
    tasks_to_run = {
        "process_text": process_text_for_dlp,
    }

    # El nombre de la cola se obtiene de una variable de entorno para mayor flexibilidad.
    sqs_queue_name = os.environ.get("SQS_QUEUE_NAME", "dlp-queue")

    manager = Manager(queue_name=sqs_queue_name, tasks=tasks_to_run)

    try:
        asyncio.run(manager.main())
    except KeyboardInterrupt:
        print("DLP Worker stopped.")