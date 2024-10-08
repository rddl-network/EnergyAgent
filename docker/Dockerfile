FROM python:3.12.5-slim-bookworm

# Install only necessary packages for building Python extensions and git for fetching Python packages
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    git \
    curl \
    net-tools \
    wireless-tools \
    systemd-sysv \
    wpasupplicant

# Clean up the Docker image by removing cache and unnecessary files
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy only necessary files for installing Python dependencies
COPY poetry.lock pyproject.toml ./

RUN pip install --upgrade setuptools
RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry lock
RUN poetry install --no-root

COPY app  /app

EXPOSE 2138

#CMD ["tail", "-f", "/dev/null"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "2138", "--timeout-keep-alive", "240"]