# Checkpoint DLP Project

This project is a system designed to detect and handle Data Loss Prevention (DLP) in text data. It uses a microservices architecture with a Django backend, a MySQL database, a LocalStack SQS queue, and a dedicated asynchronous Python worker for DLP processing.

## Architecture

The application is composed of the following services, orchestrated by Docker Compose:

-   **`db`**: A MySQL database container to store application data.
-   **`queue`**: A LocalStack container simulating AWS SQS for messaging. This queue decouples the main application from the DLP processing task.
-   **`backend`**: A Django REST Framework application that provides an API to submit text for DLP analysis. When a request is received, it sends a message to the SQS queue.
-   **`dlp_worker`**: An asynchronous Python worker that listens for messages on the SQS queue. It consumes messages, performs DLP analysis on the text, and can take further action based on the results.

## Project Structure

```
.
├── backend/
│   ├── backend/          # Django project directory
│   ├── dlp_api/          # Django app for the API
│   ├── Dockerfile        # Dockerfile for the backend service
│   ├── manage.py         # Django's command-line utility
│   └── requirements.txt  # Python dependencies for the backend
├── dlp_worker/
│   ├── Dockerfile        # Dockerfile for the DLP worker service
│   ├── requirements.txt  # Python dependencies for the worker
│   └── worker.py         # The asynchronous DLP worker script
├── docker-compose.yml    # Docker Compose file for all services
└── README.md             # This file
```

## Getting Started

### Prerequisites

-   Docker
-   Docker Compose

### Installation and Running

1.  **Build the Docker containers:**
    ```bash
    docker-compose build
    ```

2.  **Start all services:**
    ```bash
    docker-compose up
    ```

This command will start the database, queue, backend, and DLP worker. The Django backend will be available at `http://localhost:8000`.

## How It Works

1.  The `backend` application exposes an API endpoint to receive text data.
2.  When a request with text is received, the `backend` creates a message and sends it to the `dlp-queue` in LocalStack. The message has a specific format, for example:
    ```json
    {
      "task": "process_text",
      "args": ["Some text to be scanned for sensitive data..."],
      "kwargs": {}
    }
    ```
3.  The `dlp_worker` is constantly polling the queue for new messages.
4.  When a message is received, the worker's `Manager` class invokes the appropriate task (`process_text` in this case) and passes the arguments.
5.  The task function (`process_text_for_dlp`) executes the DLP scanning logic on the text.

## Next Steps

The following are the next logical steps in the development of this project:

1.  **Implement the API Endpoint**: Create the view and serializer in the `dlp_api` Django app to handle incoming requests and send messages to the SQS queue.
2.  **Configure Django Settings**: Adjust the `settings.py` file to connect to the MySQL database and configure the LocalStack SQS queue connection.
3.  **Flesh out the DLP Logic**: Enhance the `process_text_for_dlp` function in `dlp_worker/worker.py` with actual DLP detection rules and logic.
4.  **Database Models**: Define the necessary Django models in `dlp_api/models.py` to store the results of the DLP scans or any other relevant data.
5.  **Run Migrations**: Create and apply database migrations to set up the necessary tables.
