FROM python:3.11-slim

# WeasyPrint needs Pango/Cairo/GDK-Pixbuf for PDF rendering; PyMuPDF ships
# its own wheels and needs nothing extra here.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libcairo2 \
    shared-mime-info \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -e ".[dev]" && chmod +x docker-entrypoint.sh

RUN mkdir -p /app/brief_output
ENV MEDIAPULSE_BRIEF_STORAGE_DIR=/app/brief_output

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "mediapulse.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
