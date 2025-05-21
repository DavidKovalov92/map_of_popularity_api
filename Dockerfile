# filepath: /home/david/Desktop/fastapi_course/popularity_map/Dockerfile
FROM python:3.13.3-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y curl gcc libpq-dev && apt-get clean

COPY src/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/

WORKDIR /app/map_of_popularity_of_locations  # Set the correct working directory

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]