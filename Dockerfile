FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 启动命令 (和你平台填的启动命令保持一致)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]