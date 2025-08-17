FROM python:3.11-slim
ENV HTTPS_PROXY=http://10.36.129.6:8080
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD [ "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080" ]
