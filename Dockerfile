FROM python:3.12-slim

WORKDIR /app

# Geospatial wheels (shapely / pyproj) may need native libs on slim images
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgeos-c1v5 \
        libproj25 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x docker-entrypoint.sh

ENV PYTHONUNBUFFERED=1 \
    HEALTH_HOST=0.0.0.0 \
    HEALTH_PORT=5000

EXPOSE 5000

ENTRYPOINT ["./docker-entrypoint.sh"]
