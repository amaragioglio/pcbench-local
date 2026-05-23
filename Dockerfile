FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends iputils-ping pciutils procps \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY pcbench ./pcbench

ENTRYPOINT ["python", "main.py"]
CMD ["run", "--quick", "--skip-security"]
