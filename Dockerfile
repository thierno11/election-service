FROM python:3.12-slim
WORKDIR /app
COPY . .

EXPOSE 8000
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn","app.main:app","--host", "0.0.0.0","--port", "8000" ]