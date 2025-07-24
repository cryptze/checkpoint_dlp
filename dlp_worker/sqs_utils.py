import asyncio
from aiobotocore.session import get_session
import botocore.exceptions

async def get_or_create_queue(queue_name: str, endpoint_url: str, max_retries: int = 5) -> str:
    """
    Obtiene la URL de una cola SQS existente o la crea si no existe.
    Maneja la construcción de la URL para LocalStack.
    """
    session = get_session()
    async with session.create_client(
        "sqs",
        region_name="us-east-1",
        endpoint_url=endpoint_url,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    ) as client:
        for attempt in range(1, max_retries + 1):
            try:
                print(f"Intento {attempt}: Verificando si la cola '{queue_name}' existe.")
                response = await client.get_queue_url(QueueName=queue_name)
                queue_url = response.get("QueueUrl")
                if queue_url:
                    print(f"Cola '{queue_name}' encontrada en: {queue_url}")
                    return queue_url
                else:
                    # Esto no debería ocurrir si la llamada es exitosa, pero por si acaso.
                    print("get_queue_url no retornó 'QueueUrl', intentando construirla.")
                    # El formato de LocalStack es predecible
                    queue_url = f"{endpoint_url.rstrip('/')}/000000000000/{queue_name}"
                    print(f"URL construida manually: {queue_url}")
                    return queue_url

            except botocore.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                    print(f"La cola '{queue_name}' no existe. Intentando crearla.")
                    try:
                        create_response = await client.create_queue(
                            QueueName=queue_name,
                            Attributes={'DelaySeconds': '0', 'VisibilityTimeout': '30'}
                        )
                        queue_url = create_response.get("QueueUrl")
                        if queue_url:
                            print(f"Cola '{queue_name}' creada exitosamente en: {queue_url}")
                            return queue_url
                        else:
                            # Si create_queue no devuelve la URL, la construimos
                            print("create_queue no retornó 'QueueUrl', construyendo manualmente.")
                            queue_url = f"{endpoint_url.rstrip('/')}/000000000000/{queue_name}"
                            print(f"URL construida manualmente: {queue_url}")
                            return queue_url
                    except Exception as create_error:
                        print(f"Error al crear la cola en el intento {attempt}: {create_error}")

                else:
                    print(f"Error de cliente inesperado en el intento {attempt}: {e}")
            
            except Exception as e:
                print(f"Error inesperado en el intento {attempt}: {type(e).__name__}: {e}")

            if attempt < max_retries:
                print(f"Reintentando en 2 segundos...")
                await asyncio.sleep(2)

    raise Exception(f"No se pudo obtener o crear la cola '{queue_name}' después de {max_retries} intentos.")

async def test_basic_sqs_queue():
    """
    Prueba una configuración mínima de SQS con LocalStack.
    """
    queue_name = "test-queue"
    # Asegúrate de que este sea el endpoint correcto para tu LocalStack
    endpoint_url = "http://localhost:4566"

    try:
        print("Iniciando prueba con configuración mínima de SQS...")
        queue_url = await get_or_create_queue(queue_name, endpoint_url)
        print(f"Prueba exitosa. URL de la cola: {queue_url}")
    except Exception as e:
        print(f"Error durante la prueba básica de SQS: {e}")

# Llamar a la función de prueba si se ejecuta este archivo directamente
if __name__ == "__main__":
    asyncio.run(test_basic_sqs_queue())