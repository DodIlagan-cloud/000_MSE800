# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Fast, clean Python behavior
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DODSCARS_DB=/data/dodscars.sqlite  
# default DB path inside the container

WORKDIR /app

# If you use Pillow for text2png, list it in requirements.txt (e.g., "Pillow==10.*")
#COPY requirements.txt ./
#RUN pip install --no-cache-dir -r requirements.txt || true

# Bring in the app
COPY . /app

# Make a place for the SQLite file and artifacts
RUN mkdir -p /data /app/.artifacts

# Default command runs the main CLI
# (change to your real entry script)
CMD ["python", "login_main_menu.py"]
