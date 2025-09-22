# 1. Base image
FROM python:3.12-slim

# 2. Set working directory inside the container
WORKDIR /app

# 3. Copy only requirements first
COPY requirements.txt .

# 4. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your app (ignored files in .dockerignore)
COPY . .

# 6. Expose a port (optional, for web apps)
EXPOSE 8000

# 7. Define the command to run your app
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]