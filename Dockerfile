# Base = gosom/google-maps-scraper (Playwright Chromium + scraper binary ready).
# Uske upar Python/Streamlit chadate hain — ek hi container me app + free GMaps scraper.
FROM gosom/google-maps-scraper:v1.15.0
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt
ENV PATH="/opt/venv/bin:$PATH"

COPY lf_core ./lf_core
COPY static ./static
# NOTE: COPY <dir> ./ dir ka SIRF contents copy karta hai (Docker docs), isliye
# .streamlit ko file-level COPY kiya — warna config.toml /app/ pe gir jaata tha
# aur Render pe theme+staticServing kabhi load nahi hote the (dark theme bug).
COPY app.py entrypoint.sh ./
COPY .streamlit/config.toml .streamlit/config.toml
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh && mkdir -p data /gmapsdata

EXPOSE 8501
ENTRYPOINT ["./entrypoint.sh"]
