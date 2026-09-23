FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY lf_core ./lf_core
COPY app.py .streamlit ./
RUN mkdir -p data
EXPOSE 8501
# Render $PORT (default 10000) pe bind karo, local/docker-compose me 8501
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0"]
