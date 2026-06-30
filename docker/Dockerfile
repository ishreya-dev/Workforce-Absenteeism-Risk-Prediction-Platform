FROM python:3.11-slim

WORKDIR /app

COPY docker/api-requirements.txt .
RUN pip install --no-cache-dir -r api-requirements.txt

COPY src/api/ ./src/api/
COPY src/model/ ./src/model/
COPY src/preprocessing/ ./src/preprocessing/
COPY models/ ./models/

EXPOSE 8000

WORKDIR /app/src

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]