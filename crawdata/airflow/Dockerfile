FROM apache/airflow:2.10.5-python3.10

USER root

# Cài đặt system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Tạo và cấp quyền cho thư mục Playwright
RUN mkdir -p /ms-playwright && \
    chown -R airflow:root /ms-playwright && \
    chmod -R 777 /ms-playwright

# Chuyển sang user airflow để cài đặt Python packages
USER airflow

# Cài đặt Python packages
COPY --chown=airflow:root requirements.txt /opt/airflow/
RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt && \
    pip install --no-cache-dir psycopg2-binary==2.9.9

# Cài đặt Playwright dưới quyền airflow
RUN pip install playwright && \
    playwright install chromium

# Chuyển sang user root để cài đặt Playwright dependencies
USER root

# Cài đặt Playwright dependencies
RUN playwright install-deps

# Chuyển lại về user airflow
USER airflow