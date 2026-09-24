FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY lf_core ./lf_core
COPY app.py .streamlit entrypoint.sh ./
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh && mkdir -p data
EXPOSE 8501
ENTRYPOINT ["./entrypoint.sh"]
