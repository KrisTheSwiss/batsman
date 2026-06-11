# Use the official Playwright Python image (pre-loaded with every required browser and OS library)
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

# Set our working directory inside the container
WORKDIR /app

# Copy your requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your actual Python script into the container
COPY . .

# The command Railway will run on the cron schedule
CMD ["python", "script.py"]
