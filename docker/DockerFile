FROM python:3.12.3-slim-bookworm

# Install only necessary packages for building Python extensions and git for fetching Python packages
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    git \
    curl

# Clean up the Docker image by removing cache and unnecessary files
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy only necessary files for installing Python dependencies
COPY poetry.lock pyproject.toml ./

RUN pip install --upgrade setuptools
RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-root --only main

# Copy the rest of the application
COPY . .

EXPOSE 8000

CMD ["python", "-m", "main"]