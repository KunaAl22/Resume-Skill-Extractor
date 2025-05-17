## Running the Project with Docker

This project is containerized using Docker and can be run easily with Docker Compose. Below are the project-specific instructions and requirements for running the application in a Docker environment.

### Project-Specific Docker Requirements
- **Base Image:** Uses `python:3.12-slim` as the base image.
- **System Dependencies:** Installs `libxml2-dev`, `libxslt1-dev`, `python3-dev`, and `build-essential` for building and running the app.
- **Python Dependencies:** All Python dependencies are managed via `requirements.txt` and installed in a virtual environment during the build.
- **User:** The application runs as a non-root user (`appuser`) for improved security.

### Environment Variables
- **No required environment variables** are specified in the Dockerfile or docker-compose.yml. If you need to add any, uncomment and use the `env_file` section in the compose file.

### Build and Run Instructions
1. **Build and start the application:**
   ```sh
   docker compose up --build
   ```
   This will build the Docker image and start the container named `python-app`.

2. **Stopping the application:**
   ```sh
   docker compose down
   ```

### Special Configuration
- **No external services or persistent volumes** are required for this project.
- **No additional configuration** is needed unless you add environment variables or external dependencies in the future.

### Ports
- The application exposes **port 8000** inside the container. This is mapped to **port 8000** on your host machine (`localhost:8000`).

---

*If you add environment variables or external services in the future, update the `docker-compose.yml` and this section accordingly.*
