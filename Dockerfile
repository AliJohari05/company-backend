# 1. Base Image
FROM python:3.11-slim

# 2. Prevent Python from writing .pyc files & buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Set work directory inside container
WORKDIR /app

# 4. Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copy project code
COPY . /app/

# 6. Expose port 8000
EXPOSE 8000

# 7. Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]