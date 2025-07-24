import asyncio
import os
from dotenv import load_dotenv
from manager import Manager
from tasks import TASKS

# Cargar variables de entorno
load_dotenv()

SQS_QUEUE_NAME = os.getenv('SQS_QUEUE_NAME', 'dlp-queue')

def main():
    """
    Punto de entrada principal para iniciar el worker.
    Crea una instancia del Manager y ejecuta su bucle principal.
    """
    print("Iniciando DLP Worker...")
    try:
        # El Manager ahora se encarga de la lógica de la cola y el procesamiento
        manager = Manager(queue_name=SQS_QUEUE_NAME, tasks=TASKS)
        asyncio.run(manager.main())
    except Exception as e:
        print(f"Error fatal en el worker: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
