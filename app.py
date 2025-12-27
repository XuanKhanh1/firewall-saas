from flask import Flask, request, Response
import requests
from urllib.parse import unquote

app = Flask(__name__)

# Backend web thật (web-victim)
BACKEND_URL = "http://web-victim:5000"

# Danh sách pattern tấn công (SQLi, XSS, CMD...)
BAD_KEYWORDS = [
    "SELECT ",
    "UNION ",
    "DROP ",
    "INSERT ",
    "DELETE ",
    "UPDATE ",
    "--",
    "' OR '1'='1",
    "<SCRIPT>",
    "ALERT(",
    "ONERROR=",
    "XP_CMD",
    "EXEC "
]

# =========================
# FIREWALL CORE
# =========================
@app.before_request
def firewall():
    # Lấy toàn bộ request
    raw_content = request.url + str(request.form)

    # Decode URL (xử lý %20, %27, ...)
    decoded_content = unquote(raw_content).upper()

    # Kiểm tra pattern độc hại
    for bad in BAD_KEYWORDS:
        if bad in decoded_content:
            return Response(
                f"🚫 BLOCKED BY FIREWALL (Detected: {bad})",
                status=403
            )

# =========================
# PROXY REQUEST
# =========================
@app.route('/', defaults={'path': ''}, methods=["GET", "POST"])
@app.route('/<path:path>', methods=["GET", "POST"])
def proxy(path):
    if request.method == "GET":
        resp = requests.get(f"{BACKEND_URL}/{path}", params=request.args)
    else:
        resp = requests.post(f"{BACKEND_URL}/{path}", data=request.form)

    return Response(
        resp.content,
        status=resp.status_code,
        headers=dict(resp.headers)
    )

# =========================
# STATIC FILE PROXY
# =========================
@app.route('/static/<path:filename>')
def proxy_static(filename):
    resp = requests.get(f"{BACKEND_URL}/static/{filename}")
    return Response(resp.content, mimetype=resp.headers.get('Content-Type'))

# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
