FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Set default port for Cloud Run
ENV PORT 8080
EXPOSE 8080

# Run the application with uvicorn using shell-form CMD for variable expansion
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
