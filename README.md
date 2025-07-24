# Checkpoint DLP

Sistema de Prevención de Fugas de Datos (DLP) para Slack, basado en Django y un worker asíncrono.

## Descripción
Este proyecto detecta y bloquea mensajes sensibles en Slack usando patrones definidos por el usuario. Utiliza Django para la API y administración, y un worker asíncrono para procesar mensajes desde una cola SQS.

## Requisitos
- Docker
- Docker Compose

## Configuración
1. Clona el repositorio.
2. Crea el archivo `.env` en `dlp_worker/` con las siguientes variables:

```
DJANGO_API_URL=http://backend:8000/api
SQS_ENDPOINT_URL=http://localstack:4566
SQS_QUEUE_NAME=dlp_tasks
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
SLACK_BOT_TOKEN=TU_TOKEN_DE_SLACK
```

3. Asegúrate de tener tus credenciales y tokens correctos.

## Ejecución
Desde la raíz del proyecto, ejecuta:

```
docker-compose up --build
    ```

Esto levantará todos los servicios necesarios: Django, LocalStack (SQS), y el worker DLP.

## Uso
1. Accede al admin de Django en `http://localhost:8000/admin` y añade patrones de regex para detectar información sensible.
2. Envía un mensaje en Slack en el canal conectado al bot.
3. Si el mensaje coincide con algún patrón, será bloqueado y registrado como fuga en el sistema.

---

## Pruebas
- Prueba los endpoints de la API de Django usando herramientas como Postman o curl.
- Prueba la lógica de regex en una función aislada (ver ejemplo en `dlp_worker/tasks.py`).
- Verifica que los modelos de Django guardan los datos correctamente desde el admin o la shell de Django.

---

¡Exactamente! Si los logs del `dlp_worker` están vacíos, pero el backend está enviando mensajes a la cola, el problema está en el worker. Aquí tienes una guía para depurar y solucionar esto:

---

## **1. Verifica que el worker esté corriendo**

Ejecuta:
```bash
docker-compose ps
```
- El estado del contenedor `dlp_worker` debe ser `Up`.
- Si está en `Exited`, revisa los logs con:
  ```bash
  docker-compose logs dlp_worker
  ```

---

## **2. Ejecuta el worker manualmente para ver errores en tiempo real**

Entra al contenedor:
```bash
docker-compose run --rm dlp_worker bash
```
Y dentro del contenedor, ejecuta:
```bash
python manager.py
```
- Observa si imprime mensajes de inicialización o si muestra algún error.

---

## **3. Verifica las variables de entorno en el worker**

Asegúrate de que el servicio `dlp_worker` en tu `docker-compose.yml` tenga las mismas variables de entorno que el backend:

```yaml
<code_block_to_apply_changes_from>
```

---

## **4. Agrega prints de depuración en el worker**

En el inicio de `manager.py`, antes de crear la sesión SQS, agrega:

```python
import os
print("SQS_QUEUE_NAME:", os.getenv('SQS_QUEUE_NAME'))
print("SQS_ENDPOINT_URL:", os.getenv('SQS_ENDPOINT_URL'))
print("AWS_REGION:", os.getenv('AWS_REGION'))
print("AWS_ACCESS_KEY_ID:", os.getenv('AWS_ACCESS_KEY_ID'))
print("AWS_SECRET_ACCESS_KEY:", os.getenv('AWS_SECRET_ACCESS_KEY'))
```

Esto te permitirá ver si el worker está recibiendo correctamente las variables de entorno.

---

## **5. Reinicia el worker**

```bash
docker-compose restart dlp_worker
```
y revisa los logs:
```bash
docker-compose logs -f dlp_worker
```

---

## **6. Si sigue sin mostrar nada**

- Comparte aquí cualquier mensaje de error que veas al ejecutar el worker manualmente.
- Si el worker imprime las variables correctamente pero no procesa mensajes, revisa que la cola SQS realmente tenga mensajes (puedes usar la interfaz de LocalStack o prints en el backend justo después de enviar el mensaje).

---

¿Puedes probar estos pasos y compartir aquí lo que ves al ejecutar el worker manualmente o en los logs? Así te ayudo a encontrar el cuello de botella exacto.
