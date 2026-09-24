#!/bin/sh
set -e

# Google OAuth keys env-vars se Streamlit secrets.toml banao (Render/Docker ke liye)
if [ -n "${GOOGLE_CLIENT_ID}" ] && [ -n "${GOOGLE_CLIENT_SECRET}" ]; then
  if [ -n "${LF_OAUTH_REDIRECT_URI}" ]; then
    REDIRECT="${LF_OAUTH_REDIRECT_URI}"
  elif [ -n "${RENDER_EXTERNAL_URL}" ]; then
    REDIRECT="${RENDER_EXTERNAL_URL}/oauth2callback"
  else
    REDIRECT="http://localhost:8501/oauth2callback"
  fi
  COOKIE="${LF_COOKIE_SECRET:-lf-dev-cookie-secret-0123456789abcdef}"
  mkdir -p .streamlit
  cat > .streamlit/secrets.toml <<EOF
[auth]
redirect_uri = "${REDIRECT}"
cookie_secret = "${COOKIE}"

[auth.google]
client_id = "${GOOGLE_CLIENT_ID}"
client_secret = "${GOOGLE_CLIENT_SECRET}"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
EOF
fi

exec streamlit run app.py --server.port="${PORT:-8501}" --server.address=0.0.0.0
