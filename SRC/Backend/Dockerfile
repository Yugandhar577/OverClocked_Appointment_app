FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app

COPY SRC/Backend/requirements.txt /app/SRC/Backend/requirements.txt
RUN pip install --no-cache-dir -r /app/SRC/Backend/requirements.txt

COPY . /app

CMD ["uvicorn", "SRC.Backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
