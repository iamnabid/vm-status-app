import platform
import socket
import time
from datetime import timedelta

import psutil
from flask import Flask

app = Flask(__name__)
START_TIME = time.time()

PAGE = """<!doctype html>
<html>
<head>
  <title>{hostname} — status</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 2rem; }}
    h1 {{ font-size: 1.4rem; margin-bottom: 1.5rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; max-width: 900px; }}
    .card {{ background: #1e293b; border-radius: 10px; padding: 1rem 1.25rem; }}
    .label {{ font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }}
    .value {{ font-size: 1.6rem; font-weight: 600; margin-top: 0.25rem; }}
    .bar {{ background: #334155; border-radius: 6px; height: 8px; margin-top: 0.6rem; overflow: hidden; }}
    .bar-fill {{ background: #38bdf8; height: 100%; }}
    footer {{ margin-top: 2rem; color: #64748b; font-size: 0.8rem; }}
  </style>
</head>
<body>
  <h1>{hostname} — live status</h1>
  <div class="grid">
    <div class="card">
      <div class="label">CPU load</div>
      <div class="value">{cpu:.0f}%</div>
      <div class="bar"><div class="bar-fill" style="width:{cpu:.0f}%"></div></div>
    </div>
    <div class="card">
      <div class="label">Memory</div>
      <div class="value">{mem_used:.1f} / {mem_total:.1f} GB</div>
      <div class="bar"><div class="bar-fill" style="width:{mem_pct:.0f}%"></div></div>
    </div>
    <div class="card">
      <div class="label">Disk</div>
      <div class="value">{disk_used:.1f} / {disk_total:.1f} GB</div>
      <div class="bar"><div class="bar-fill" style="width:{disk_pct:.0f}%"></div></div>
    </div>
    <div class="card">
      <div class="label">System uptime</div>
      <div class="value">{uptime}</div>
    </div>
    <div class="card">
      <div class="label">App uptime</div>
      <div class="value">{app_uptime}</div>
    </div>
    <div class="card">
      <div class="label">OS</div>
      <div class="value" style="font-size:1.1rem">{os_info}</div>
    </div>
  </div>
  <footer>Deployed automatically via GitHub Actions on every push to main.</footer>
</body>
</html>
"""


def fmt_delta(seconds: float) -> str:
    return str(timedelta(seconds=int(seconds)))


@app.route("/")
def status():
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    boot_time = psutil.boot_time()

    return PAGE.format(
        hostname=socket.gethostname(),
        cpu=psutil.cpu_percent(interval=0.3),
        mem_used=mem.used / (1024 ** 3),
        mem_total=mem.total / (1024 ** 3),
        mem_pct=mem.percent,
        disk_used=disk.used / (1024 ** 3),
        disk_total=disk.total / (1024 ** 3),
        disk_pct=disk.percent,
        uptime=fmt_delta(time.time() - boot_time),
        app_uptime=fmt_delta(time.time() - START_TIME),
        os_info=f"{platform.system()} {platform.release()}",
    )


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
