
import os
import time
import boto3
import sys

# Configuración desde variables de entorno
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID', 'test')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY', 'test')
aws_region = os.getenv('AWS_REGION', 'us-east-1')
sqs_endpoint_url = os.getenv('SQS_ENDPOINT_URL', 'http://queue:4566')
sqs_queue_name = os.getenv('SQS_QUEUE_NAME', 'dlp-queue')

# Espera inicial para que el servicio SQS se levante
print("--- Waiting for SQS service to be ready... ---")
time.sleep(10)

# Bucle para intentar conectar y crear la cola
max_retries = 15
retry_delay = 5  # segundos
for i in range(max_retries):
    try:
        print(f"Attempt {i + 1}/{max_retries}: Connecting to SQS at {sqs_endpoint_url}...")
        sqs = boto3.client(
            'sqs',
            endpoint_url=sqs_endpoint_url,
            region_name=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )

        print(f"Creating/verifying SQS queue: {sqs_queue_name}")
        sqs.create_queue(QueueName=sqs_queue_name)

        print("--- SQS queue is ready! ---")
        sys.exit(0)  # Éxito, salir del script

    except Exception as e:
        print(f"Could not connect to SQS or create queue: {e}")
        print(f"Retrying in {retry_delay} seconds...")
        time.sleep(retry_delay)

print("--- SQS service not available after multiple retries. Exiting. ---")
sys.exit(1)  # Fallo, el contenedor no se iniciará correctamente
