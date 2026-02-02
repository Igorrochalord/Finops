FROM python:3.12-slim

WORKDIR /app

# Instala dependências do SO (necessário para algumas libs)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# O código será montado via volume no docker-compose, 
# mas copiamos aqui para garantir build de produção se precisar.
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app/main.py"]