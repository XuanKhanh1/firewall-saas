from flask import Flask, request, Response, render_template_string, redirect, url_for
import requests

app = Flask(__name__)
TARGET_SERVER = 'http://web-victim:5000'
FIREWALL_ENABLED = True 

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Firewall SaaS Dashboard</title>
    <style>
        body { font-family: sans-serif; text-align: center; padding: 50px; background-color: #f4f4f9; }
        .box { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); display: inline-block; }
        .status { font-weight: bold; font-size: 24px; color: {{ 'green' if status else 'red' }}; }
        .btn { padding: 15px 30px; font-size: 18px; cursor: pointer; border: none; border-radius: 5px; color: white; margin-top: 20px; }
        .btn-on { background-color: #28a745; }
        .btn-off { background-color: #dc3545; }
        a { text-decoration: none; color: #007bff; }
    </style>
</head>
<body>
    <h1>🛡️ Hệ thống Cloud Firewall SaaS</h1>
    <div class="box">
        <p>Trạng thái bảo vệ:</p>
        <div class="status">{{ 'ACTIVE (ĐANG BẬT)' if status else 'DISABLED (ĐANG TẮT)' }}</div>
        <form action="/toggle" method="post">
            <button type="submit" class="btn {{ 'btn-off' if status else 'btn-on' }}">
                {{ 'TẮT SYSTEM' if status else 'KÍCH HOẠT SYSTEM' }}
            </button>
        </form>
        <hr>
        <p>👉 <a href="/" target="_blank">Vào Web Khách Hàng (Demo)</a></p>
    </div>
</body>
</html>
"""

@app.route('/dashboard')
def dashboard():
    return render_template_string(DASHBOARD_HTML, status=FIREWALL_ENABLED)

@app.route('/toggle', methods=['POST'])
def toggle():
    global FIREWALL_ENABLED
    FIREWALL_ENABLED = not FIREWALL_ENABLED
    return redirect(url_for('dashboard'))

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    if path.startswith('dashboard') or path.startswith('toggle') or path.startswith('static'):
        return dashboard()

    if FIREWALL_ENABLED:
        BAD_KEYWORDS = ["SELECT", "UNION", "DROP", "<SCRIPT>", "ALERT(", "OR 1=1"]
        full_url = str(request.url).upper()
        if any(bad in full_url for bad in BAD_KEYWORDS):
             return Response(f"<h1 style='color:red; text-align:center;'>🚫 FIREWALL BLOCKED!<br>Malicious content detected.</h1>", status=403)
        
        if request.method == 'POST':
            data_str = str(request.form.to_dict()).upper()
            if any(bad in data_str for bad in BAD_KEYWORDS):
                return Response(f"<h1 style='color:red; text-align:center;'>🚫 FIREWALL BLOCKED!<br>Malicious POST data detected.</h1>", status=403)

    try:
        if request.method == 'GET':
            resp = requests.get(f"{TARGET_SERVER}/{path}", params=request.args)
        else:
            resp = requests.request(
                method=request.method,
                url=f"{TARGET_SERVER}/{path}",
                data=request.form,
                cookies=request.cookies,
                allow_redirects=False)
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
        return Response(resp.content, resp.status_code, headers)
    except Exception as e:
        return Response(f"Backend Error: {e}", status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)