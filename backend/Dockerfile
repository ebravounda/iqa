FROM python:3.11-slim

WORKDIR /app

COPY requirements-prod.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

ENV MONGO_URL=mongodb://host.docker.internal:27017
ENV DB_NAME=gymaccess
ENV JWT_SECRET=CambiaEstoPorUnaClaveLargaYSegura2024
ENV QR_SECRET=OtraClaveDiferenteParaQR2024
ENV CORS_ORIGINS=https://gym.ticketpro.es

EXPOSE 8001

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
