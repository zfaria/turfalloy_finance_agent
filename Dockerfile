FROM python:3.11-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependências + wkhtmltopdf (FUNCIONA no bullseye)
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    xvfb \
    libfontconfig \
    libxrender1 \
    libxext6 \
    libjpeg62-turbo \
    libpng16-16 \
    fonts-dejavu-core \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p reports

ENV PYTHONUNBUFFERED=1

CMD ["python", "bot/main.py"]