FROM python:3.12-slim

# Install Qt6/PySide6 system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libxcb1 \
    libx11-xcb1 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xkb1 \
    libxkbcommon-x11-0 \
    libxcb-cursor0 \
    libxcb-shape0 \
    libxcb-sync1 \
    libxcb-util1 \
    libdbus-1-3 \
    libfontconfig1 \
    libxrender1 \
    libxi6 \
    libxext6 \
    libx11-6 \
    libegl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/configs

CMD ["python", "main.py"]
