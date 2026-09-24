#!/bin/sh
set -e

# ---- Google Maps scraper: local sidecar, ya bahar ka (home IP) endpoint ----
# GMAPS_BASE_URL agar localhost/127.0.0.1 se alag hai (jaise home-PC tunnel),
# toh local scraper band rakho — scraping tumhare home IP se hogi.
GMAPS_URL="${GMAPS_BASE_URL:-http://127.0.0.1:8080}"
case "$GMAPS_URL" in
  *127.0.0.1*|*localhost*) _local_gmaps=1 ;;
  *) _local_gmaps=0 ;;
esac

if [ "${GMAPS_ENABLE:-1}" = "1" ] && [ "$_local_gmaps" = "1" ]; then
  mkdir -p /gmapsdata
  # -c 1 = ek saath sirf 1 job (RAM + IP-block dono safe)
  DISABLE_TELEMETRY=1 google-maps-scraper -web -data-folder /gmapsdata -c 1 \
    >/tmp/gmaps.log 2>&1 &
  n=0
  until python3 -c 'import urllib.request as u; u.urlopen("http://127.0.0.1:8080/api/v1/jobs", timeout=2)' 2>/dev/null; do
    n=$((n + 1))
    [ "$n" -ge 30 ] && break
    sleep 1
  done
fi

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
