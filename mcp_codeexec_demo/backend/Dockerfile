FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app
# Create workspace directory for filesystem-based code execution
# Include skills directory for reusable agent code (blog post pattern)
RUN mkdir -p /app/workspace/servers && \
    mkdir -p /app/workspace/skills
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
