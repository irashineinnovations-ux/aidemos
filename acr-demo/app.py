from datetime import datetime, timezone
import os
import platform
import socket

from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ACR Demo - Task v2.0</title>
    <style>
        :root {
            --primary: #0078d4;
            --primary-hover: #106ebe;
            --bg: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --card-border: rgba(255, 255, 255, 0.1);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-green: #10b981;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: radial-gradient(circle at 50% 0%, #1e293b 0%, #0f172a 100%);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }

        .container {
            max-width: 640px;
            width: 100%;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 32px;
            backdrop-filter: blur(12px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        }

        .badge-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent-green);
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 13px;
            font-weight: 600;
        }

        .badge-dot {
            width: 8px;
            height: 8px;
            background: var(--accent-green);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        .version-badge {
            background: rgba(0, 120, 212, 0.15);
            color: #38bdf8;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 13px;
            font-weight: 600;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.9); }
        }

        h1 {
            font-size: 26px;
            font-weight: 700;
            margin-bottom: 8px;
            background: linear-gradient(135deg, #ffffff 0%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .subtitle {
            color: var(--text-muted);
            font-size: 15px;
            margin-bottom: 24px;
            line-height: 1.5;
        }

        .greeting-box {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 24px;
            font-size: 16px;
            font-weight: 500;
            color: #e2e8f0;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .info-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 24px;
        }

        @media (max-width: 480px) {
            .info-grid {
                grid-template-columns: 1fr;
            }
        }

        .info-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 10px;
            padding: 12px 16px;
        }

        .info-label {
            font-size: 12px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }

        .info-value {
            font-size: 14px;
            font-weight: 600;
            color: #f1f5f9;
            word-break: break-all;
        }

        .actions {
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .btn {
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 18px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .btn:hover {
            background: var(--primary-hover);
            transform: translateY(-1px);
        }

        #health-status {
            font-size: 13px;
            color: var(--text-muted);
            margin-left: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="badge-bar">
            <span class="badge">
                <span class="badge-dot"></span> Online
            </span>
            <span class="version-badge">Task v2.0</span>
        </div>

        <h1>Azure Container Registry Demo</h1>
        <p class="subtitle">Cloud-native container deployment showcase</p>

        <div class="greeting-box">
            <span>🚀</span>
            <span>Hello from New ACR Demo for Task v2.0!</span>
        </div>

        <div class="info-grid">
            <div class="info-card">
                <div class="info-label">Host / Container ID</div>
                <div class="info-value">{{ hostname }}</div>
            </div>
            <div class="info-card">
                <div class="info-label">Environment Port</div>
                <div class="info-value">{{ port }}</div>
            </div>
            <div class="info-card">
                <div class="info-label">Platform / OS</div>
                <div class="info-value">{{ platform }}</div>
            </div>
            <div class="info-card">
                <div class="info-label">Python Version</div>
                <div class="info-value">{{ python_version }}</div>
            </div>
        </div>

        <div class="actions">
            <button class="btn" onclick="checkHealth()">Test Health Endpoint</button>
            <span id="health-status"></span>
        </div>
    </div>

    <script>
        async function checkHealth() {
            const statusEl = document.getElementById('health-status');
            statusEl.textContent = 'Checking...';
            statusEl.style.color = '#94a3b8';
            try {
                const res = await fetch('/api/health');
                const data = await res.json();
                statusEl.textContent = `Status: ${data.status.toUpperCase()} (HTTP 200)`;
                statusEl.style.color = '#10b981';
            } catch (err) {
                statusEl.textContent = 'Health check failed';
                statusEl.style.color = '#ef4444';
            }
        }
    </script>
</body>
</html>
"""


@app.route("/")
def hello():
    port = os.environ.get("PORT", "8000")
    return render_template_string(
        HTML_TEMPLATE,
        hostname=socket.gethostname(),
        port=port,
        platform=platform.system(),
        python_version=platform.python_version(),
    )


@app.route("/api/health")
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "version": "v2.0",
    })


if __name__ == "__main__":
    # Port 8000 is blocked by many browsers as an unsafe port.
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)

