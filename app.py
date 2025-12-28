from flask import Flask, request, Response
import requests
from urllib.parse import unquote
import os

app = Flask(__name__)

# Backend web thật (web-victim)
# Mặc định lấy từ biến môi trường Render, nếu không có thì dùng localhost
BACKEND_URL = os.environ.get("BACKEND_URL", "http://web-victim:5000")

# Danh sách pattern tấn công (SQLi, XSS, CMD...)
BAD_KEYWORDS = [
    "SELECT ", "UNION ", "DROP ", "INSERT ", "DELETE ", "UPDATE ",
    "--", "' OR '1'='1", "<SCRIPT>", "ALERT(", "ONERROR=", "XP_CMD", "EXEC "
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
# PROXY REQUEST (Đã sửa lỗi 502)
# =========================
@app.route('/', defaults={'path': ''}, methods=["GET", "POST"])
@app.route('/<path:path>', methods=["GET", "POST"])
def proxy(path):
    # Tạo URL đích
    target_url = f"{BACKEND_URL}/{path}"

    try:
        if request.method == "GET":
            resp = requests.get(target_url, params=request.args)
        else:
            resp = requests.post(target_url, data=request.form)

        # --- ĐOẠN SỬA ĐỂ FIX LỖI 502 ---
        # Không copy toàn bộ headers của server đích nữa vì sẽ bị lệch Content-Length
        # Chỉ tạo Response mới với nội dung và status code
        response = Response(resp.content, resp.status_code)
        
        # Chỉ giữ lại Content-Type để hiển thị đúng ảnh/css/html
        if 'Content-Type' in resp.headers:
            response.headers['Content-Type'] = resp.headers['Content-Type']
            
        return response
        # -------------------------------

    except Exception as e:
        return Response(f"Proxy Error: {str(e)}", status=500)

# =========================
# STATIC FILE PROXY (Dự phòng)
# =========================
@app.route('/static/<path:filename>')
def proxy_static(filename):
    try:
        resp = requests.get(f"{BACKEND_URL}/static/{filename}")
        return Response(resp.content, mimetype=resp.headers.get('Content-Type'))
    except:
        return Response("Static file not found", status=404)

# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)