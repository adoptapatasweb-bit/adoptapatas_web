FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    unixodbc-dev \
    gcc \
    apt-transport-https \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=10000

CMD ["gunicorn", "backpatas.app:app", "--bind", "0.0.0.0:10000"]