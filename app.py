import platform
import socket
import time
from datetime import timedelta

import psutil
from flask import Flask

app = Flask(__name__)
START_TIME = time.time()

SEGMENTS = 24

PAGE = """<!doctype html>
<html>
<head>
  <title>{hostname} status</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0d1b1e;
      --panel: #142b2e;
      --line: #24393c;
      --brass: #c7a25a;
      --brass-dim: #8c7440;
      --ink: #ede6d6;
      --dim: #7c9496;
      --warn: #b0503a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: 'IBM Plex Sans', sans-serif;
      background: var(--bg);
      background-image:
        repeating-linear-gradient(135deg, rgba(199,162,90,0.015) 0px, rgba(199,162,90,0.015) 1px, transparent 1px, transparent 8px);
      color: var(--ink);
      margin: 0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 1.5rem;
    }}
    .panel {{
      width: 100%;
      max-width: 520px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 4px;
      padding: 1.75rem;
    }}
    .head {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      padding-bottom: 1.25rem;
      border-bottom: 1px solid var(--line);
    }}
    .host {{
      font-size: 1.15rem;
      font-weight: 600;
      letter-spacing: 0.01em;
    }}
    .status {{
      display: flex;
      align-items: center;
      gap: 0.45rem;
      font-size: 0.8rem;
      color: var(--dim);
    }}
    .dot {{
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--brass);
      box-shadow: 0 0 0 0 rgba(199,162,90,0.5);
      animation: pulse 2.6s ease-in-out infinite;
    }}
    @media (prefers-reduced-motion: reduce) {{
      .dot {{ animation: none; }}
    }}
    @keyframes pulse {{
      0%, 100% {{ box-shadow: 0 0 0 0 rgba(199,162,90,0.45); }}
      50% {{ box-shadow: 0 0 0 4px rgba(199,162,90,0); }}
    }}
    .meters {{
      padding-top: 1.4rem;
      display: flex;
      flex-direction: column;
      gap: 1.1rem;
    }}
    .meter-row {{
      display: grid;
      grid-template-columns: 4.6rem 1fr auto;
      align-items: center;
      gap: 0.9rem;
    }}
    .meter-label {{
      font-size: 0.85rem;
      color: var(--dim);
    }}
    .segs {{
      display: flex;
      gap: 2px;
    }}
    .seg {{
      flex: 1;
      height: 12px;
      background: var(--line);
      border-radius: 1px;
    }}
    .seg.on {{ background: var(--brass); }}
    .seg.on.warn {{ background: var(--warn); }}
    .meter-value {{
      font-family: 'IBM Plex Mono', monospace;
      font-size: 0.95rem;
      min-width: 3.4rem;
      text-align: right;
    }}
    .detail {{
      padding-top: 1.1rem;
      margin-top: 1.1rem;
      border-top: 1px solid var(--line);
      font-family: 'IBM Plex Mono', monospace;
      font-size: 0.78rem;
      color: var(--dim);
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 0.4rem 1rem;
    }}
    footer {{
      max-width: 520px;
      width: 100%;
      text-align: left;
      color: var(--brass-dim);
      font-size: 0.75rem;
      margin-top: 0.9rem;
      padding-left: 0.1rem;
    }}
    .wrap {{
      display: flex;
      flex-direction: column;
      align-items: center;
      width: 100%;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="panel">
      <div class="head">
        <div class="host">{hostname}</div>
        <div class="status"><span class="dot"></span>online, up {uptime}</div>
      </div>
      <div class="meters">
        <div class="meter-row">
          <div class="meter-label">Cpu</div>
          <div class="segs">{cpu_segs}</div>
          <div class="meter-value">{cpu:.0f}%</div>
        </div>
        <div class="meter-row">
          <div class="meter-label">Memory</div>
          <div class="segs">{mem_segs}</div>
          <div class="meter-value">{mem_pct:.0f}%</div>
        </div>
        <div class="meter-row">
          <div class="meter-label">Disk</div>
          <div class="segs">{disk_segs}</div>
          <div class="meter-value">{disk_pct:.0f}%</div>
        </div>
      </div>
      <div class="detail">
        <span>{mem_used:.1f} / {mem_total:.1f} GB memory</span>
        <span>{disk_used:.1f} / {disk_total:.1f} GB disk</span>
        <span>{os_info}</span>
      </div>
    </div>
    <footer>Rebuilt and restarted automatically on every push to main, {app_uptime} ago.</footer>
  </div>
</body>
</html>
"""


def fmt_delta(seconds: float) -> str:
    td = timedelta(seconds=int(seconds))
    days, rem = td.days, td.seconds
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def render_segments(pct: float) -> str:
    filled = round((pct / 100) * SEGMENTS)
    warn = pct >= 85
    segs = []
    for i in range(SEGMENTS):
        cls = "seg"
        if i < filled:
            cls += " on warn" if warn else " on"
        segs.append(f'<div class="{cls}"></div>')
    return "".join(segs)


@app.route("/")
def status():
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    boot_time = psutil.boot_time()
    cpu = psutil.cpu_percent(interval=0.3)

    return PAGE.format(
        hostname=socket.gethostname(),
        cpu=cpu,
        cpu_segs=render_segments(cpu),
        mem_used=mem.used / (1024 ** 3),
        mem_total=mem.total / (1024 ** 3),
        mem_pct=mem.percent,
        mem_segs=render_segments(mem.percent),
        disk_used=disk.used / (1024 ** 3),
        disk_total=disk.total / (1024 ** 3),
        disk_pct=disk.percent,
        disk_segs=render_segments(disk.percent),
        uptime=fmt_delta(time.time() - boot_time),
        app_uptime=fmt_delta(time.time() - START_TIME),
        os_info=f"{platform.system()} {platform.release()}",
    )


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
