import platform
import socket
import time
from datetime import timedelta

import psutil
from flask import Flask, send_from_directory

app = Flask(__name__)
START_TIME = time.time()

SEGMENTS = 24

ROOT_VARS_CSS = """\
      --bg: #0d1b1e;
      --panel: #142b2e;
      --line: #24393c;
      --brass: #c7a25a;
      --brass-dim: #8c7440;
      --ink: #ede6d6;
      --dim: #7c9496;
      --warn: #b0503a;"""

STATUS_PAGE = """<!doctype html>
<html>
<head>
  <title>{hostname} status</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <style>
    :root {{
__ROOT_VARS__
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
    .back {{
      max-width: 520px;
      width: 100%;
      margin-bottom: 0.9rem;
      font-size: 0.8rem;
    }}
    .back a {{ color: var(--dim); text-decoration: none; }}
    .back a:hover {{ color: var(--ink); }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="back"><a href="/">Nabid Sheikh</a></div>
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
""".replace("__ROOT_VARS__", ROOT_VARS_CSS)

PORTFOLIO_DESCRIPTION = (
    "Environmental engineering student at CZU Prague — remote sensing, "
    "hydrology, and the cloud infrastructure behind the research."
)

PORTFOLIO_PAGE = """<!doctype html>
<html>
<head>
  <title>Nabid Sheikh</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="__PORTFOLIO_DESCRIPTION__">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:wght@500;600&display=swap" rel="stylesheet">
  <link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://nabidsheikh.systems/">
  <meta property="og:title" content="Nabid Sheikh">
  <meta property="og:description" content="__PORTFOLIO_DESCRIPTION__">
  <meta property="og:image" content="https://nabidsheikh.systems/static/og-image.png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Nabid Sheikh">
  <meta name="twitter:description" content="__PORTFOLIO_DESCRIPTION__">
  <meta name="twitter:image" content="https://nabidsheikh.systems/static/og-image.png">
  <style>
    :root {
__ROOT_VARS__
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      font-family: 'IBM Plex Sans', sans-serif;
      background: var(--bg);
      background-image:
        repeating-linear-gradient(135deg, rgba(199,162,90,0.015) 0px, rgba(199,162,90,0.015) 1px, transparent 1px, transparent 8px);
      color: var(--ink);
      margin: 0;
      line-height: 1.55;
    }
    a { color: inherit; }
    .shell {
      max-width: 680px;
      margin: 0 auto;
      padding: 2.5rem 1.5rem 4rem;
    }
    nav {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 1.1rem;
      font-size: 0.82rem;
      color: var(--dim);
      padding-bottom: 2.2rem;
      margin-bottom: 2.4rem;
      border-bottom: 1px solid var(--line);
    }
    nav a { text-decoration: none; color: var(--dim); }
    nav a:hover { color: var(--brass); }
    nav .brand {
      margin-right: auto;
      line-height: 0;
    }
    nav .brand svg { display: block; transition: transform 0.25s ease; }
    nav .brand:hover svg { transform: rotate(10deg); }

    h1 {
      font-family: 'IBM Plex Serif', serif;
      font-weight: 600;
      font-size: 2.1rem;
      margin: 0 0 0.3rem;
    }
    .role {
      color: var(--brass);
      font-size: 1rem;
      margin-bottom: 1.1rem;
    }
    .lede {
      font-size: 1.05rem;
      color: var(--ink);
      max-width: 46ch;
      margin-bottom: 0.9rem;
    }
    .now {
      font-size: 0.88rem;
      color: var(--dim);
      max-width: 52ch;
      margin-bottom: 2.2rem;
    }
    .now strong { color: var(--ink); font-weight: 500; }

    .cv-button {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      background: var(--brass);
      color: var(--bg);
      font-weight: 600;
      font-size: 0.85rem;
      text-decoration: none;
      padding: 0.55rem 1.1rem;
      border-radius: 3px;
      margin-top: 1.4rem;
      transition: background 0.15s ease;
    }
    .cv-button:hover { background: var(--ink); }
    .cv-button svg { width: 14px; height: 14px; }

    .pipeline {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }
    .pipeline-step {
      background: var(--bg);
      border: 1px solid var(--line);
      border-radius: 3px;
      padding: 0.7rem 0.9rem;
      font-family: 'IBM Plex Mono', monospace;
      font-size: 0.85rem;
      color: var(--ink);
    }
    .step-label { color: var(--brass); margin-right: 0.6rem; }
    .pipeline-arrow {
      text-align: center;
      color: var(--dim);
      font-size: 0.9rem;
      line-height: 1;
    }
    .pipeline-note {
      margin-top: 1rem;
      font-size: 0.8rem;
      color: var(--dim);
    }

    .elev {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 4px;
      padding: 1.4rem 1.5rem;
      margin-bottom: 3.2rem;
    }
    .elev-caption {
      font-size: 0.8rem;
      color: var(--dim);
      margin-bottom: 1rem;
    }
    .elev-row {
      display: grid;
      grid-template-columns: 7.5rem 1fr;
      gap: 0.3rem 1.1rem;
      padding: 0.65rem 0;
      border-bottom: 1px solid var(--line);
      align-items: center;
    }
    .elev-row:last-child { border-bottom: none; padding-bottom: 0; }
    .elev-row:first-child { padding-top: 0; }
    .elev-label {
      font-family: 'IBM Plex Mono', monospace;
      font-size: 0.82rem;
      color: var(--dim);
    }
    .elev-bar {
      height: 9px;
      border-radius: 1px;
      background: transparent;
      border: 1px solid var(--line);
      margin-bottom: 0.35rem;
    }
    .elev-bar.sig { background: var(--warn); border-color: var(--warn); }
    .elev-note { font-size: 0.85rem; color: var(--ink); }

    section { margin-bottom: 3.2rem; }
    h2 {
      font-size: 1.05rem;
      font-weight: 600;
      margin: 0 0 1.1rem;
      padding-bottom: 0.7rem;
      border-bottom: 1px solid var(--line);
    }
    p { margin: 0 0 1rem; max-width: 62ch; }
    p:last-child { margin-bottom: 0; }

    .meta-list {
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
      font-size: 0.88rem;
      color: var(--dim);
      margin-bottom: 1.2rem;
    }
    .meta-list strong { color: var(--ink); font-weight: 500; }

    .finding {
      display: flex;
      gap: 0.7rem;
      padding: 0.7rem 0;
      border-bottom: 1px solid var(--line);
      font-size: 0.92rem;
    }
    .finding:last-child { border-bottom: none; }
    .finding .mark {
      flex: none;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--brass);
      margin-top: 0.55rem;
    }
    .status-line {
      margin-top: 1.2rem;
      font-size: 0.82rem;
      color: var(--brass-dim);
      font-family: 'IBM Plex Mono', monospace;
    }

    .timeline-row {
      display: grid;
      grid-template-columns: 6rem 1fr;
      gap: 0.2rem 1.1rem;
      padding: 0.8rem 0;
      border-bottom: 1px solid var(--line);
    }
    .timeline-row:last-child { border-bottom: none; }
    .timeline-date {
      font-family: 'IBM Plex Mono', monospace;
      font-size: 0.8rem;
      color: var(--dim);
    }
    .timeline-place {
      font-weight: 500;
      margin-bottom: 0.15rem;
    }
    .timeline-detail {
      font-size: 0.88rem;
      color: var(--dim);
    }

    .skill-row {
      display: grid;
      grid-template-columns: 8.5rem 1fr;
      gap: 0.3rem 1.1rem;
      padding: 0.6rem 0;
      border-bottom: 1px solid var(--line);
      font-size: 0.9rem;
    }
    .skill-row:last-child { border-bottom: none; }
    .skill-label { color: var(--brass); }
    .skill-value { color: var(--dim); }
    .skill-group-label {
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--brass-dim);
      margin: 1.3rem 0 0.4rem;
    }
    .skill-group-label:first-of-type { margin-top: 0; }

    .contact-links {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      font-family: 'IBM Plex Mono', monospace;
      font-size: 0.9rem;
    }
    .contact-links a { text-decoration: none; border-bottom: 1px solid var(--line); padding-bottom: 2px; }
    .contact-links a:hover { border-color: var(--brass); color: var(--brass); }

    footer {
      color: var(--brass-dim);
      font-size: 0.75rem;
      padding-top: 1rem;
      border-top: 1px solid var(--line);
    }
  </style>
</head>
<body>
  <div class="shell">
    <nav>
      <a href="/" class="brand" aria-label="Nabid Sheikh, home">
        <svg width="24" height="24" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="0.5" y="0.5" width="31" height="31" rx="7" fill="var(--panel)" stroke="var(--line)"/>
          <ellipse cx="16" cy="16" rx="11" ry="5.2" transform="rotate(-28 16 16)" stroke="var(--brass-dim)" stroke-width="1.1"/>
          <circle cx="16" cy="16" r="3.2" fill="var(--brass)"/>
          <circle cx="25.1" cy="11.4" r="1.5" fill="var(--brass)"/>
        </svg>
      </a>
      <a href="#about">About</a>
      <a href="#systems">Systems</a>
      <a href="#skills">Skills</a>
      <a href="#thesis">Thesis</a>
      <a href="#field">Field work</a>
      <a href="#contact">Contact</a>
      <a href="/status">Live status</a>
    </nav>

    <h1>Nabid Sheikh</h1>
    <div class="role">Environmental engineering student, CZU Prague</div>
    <p class="lede">I dig into how systems behave. Right now that's 24 years of Czech mountain snow cover data pulled from satellites, and the infrastructure running this site.</p>
    <p class="now">Currently: writing my bachelor thesis on Czech mountain snow cover trends, running the cloud infrastructure (Oracle, Azure) behind it and this site, and picking up field methods in snow hydrology along the way.</p>

    <section id="about">
      <h2>About</h2>
      <p>I'm an environmental engineering student at the Czech University of Life Sciences Prague (CZU), currently in my second year. I moved from Dhaka, Bangladesh to Prague in 2024 for the programme, which has covered environmental chemistry, hydrology, GIS, air pollution, ecotoxicology, soil science, and landscape ecology.</p>
      <p>My focus sits at the intersection of remote sensing, hydrology, and GIS: using satellite data to answer questions about how mountain environments are changing. I'm drawn to research with a clear environmental application, not research for its own sake.</p>
      <p>I speak Bangla natively, work comfortably in English, and am building up my Czech.</p>
    </section>

    <section id="systems">
      <h2>Systems &amp; infrastructure</h2>
      <div class="meta-list">
        <div><strong>This site, end to end</strong></div>
        <div>Oracle Cloud ARM VM &mdash; provisioned, deployed, and monitored by me</div>
      </div>
      <p>Push to main and GitHub Actions ships straight to the server: SSH deploy, dependency install in a fresh virtualenv, systemd restart, nginx reverse proxy, TLS from Let&rsquo;s Encrypt. The same VM reports its own live vitals on the status page linked below.</p>

      <div class="elev">
        <div class="elev-caption">How this site runs</div>
        <div class="pipeline">
          <div class="pipeline-step"><span class="step-label">01</span>git push to main</div>
          <div class="pipeline-arrow">&darr;</div>
          <div class="pipeline-step"><span class="step-label">02</span>GitHub Actions checks out the code</div>
          <div class="pipeline-arrow">&darr;</div>
          <div class="pipeline-step"><span class="step-label">03</span>Deploys over SSH to an Oracle Cloud ARM VM, installs dependencies in a fresh virtualenv</div>
          <div class="pipeline-arrow">&darr;</div>
          <div class="pipeline-step"><span class="step-label">04</span>systemd restarts the app; nginx reverse-proxies it and terminates TLS</div>
          <div class="pipeline-arrow">&darr;</div>
          <div class="pipeline-step"><span class="step-label">05</span>Let&rsquo;s Encrypt certificate, auto-renewed by certbot</div>
        </div>
      </div>

      <div class="finding"><span class="mark"></span><span>Every push to main redeploys automatically &mdash; no manual server steps.</span></div>
      <div class="finding"><span class="mark"></span><span>TLS is issued and renewed by Let&rsquo;s Encrypt/certbot; nginx terminates it and reverse-proxies to gunicorn.</span></div>
      <div class="finding"><span class="mark"></span><span>My own SSH and RDP access to the VM goes over Tailscale &mdash; GitHub&rsquo;s runners deploy straight over the public IP.</span></div>

      <div class="status-line">Built with Flask, gunicorn, nginx, systemd, and GitHub Actions.</div>

      <div class="contact-links">
        <a href="/status">See the live dashboard</a>
        <a href="https://github.com/iamnabid/vm-status-app">Source on GitHub</a>
      </div>
    </section>

    <section id="skills">
      <h2>Skills</h2>
      <p>What's actually in rotation, grouped by where it gets used.</p>

      <div class="skill-group-label">Research &amp; analysis</div>
      <div class="skill-row"><div class="skill-label">Remote sensing</div><div class="skill-value">Google Earth Engine, MODIS (MOD10A1 / MOD10A2), Sentinel-2, UAV data collection</div></div>
      <div class="skill-row"><div class="skill-label">GIS</div><div class="skill-value">ArcGIS Pro, QGIS, DEM-based elevation analysis</div></div>
      <div class="skill-row"><div class="skill-label">Programming</div><div class="skill-value">Python (pandas, matplotlib), R, JavaScript (Earth Engine scripting)</div></div>
      <div class="skill-row"><div class="skill-label">Statistics</div><div class="skill-value">Mann-Kendall trend test, Sen's slope estimator, correlation analysis</div></div>
      <div class="skill-row"><div class="skill-label">Field methods</div><div class="skill-value">Snow pit excavation, snow water equivalent measurement, avalanche safety certified</div></div>

      <div class="skill-group-label">Infrastructure</div>
      <div class="skill-row"><div class="skill-label">Systems</div><div class="skill-value">Linux administration, cloud VMs (Oracle, Azure), CI/CD (GitHub Actions), SSH/Tailscale networking</div></div>
    </section>

    <section id="thesis">
      <h2>Bachelor thesis</h2>
      <div class="meta-list">
        <div><strong>Long-term trends in snow cover duration in Czech mountain ranges and their implications for water resources</strong></div>
        <div>Czech University of Life Sciences Prague, Faculty of Environmental Sciences</div>
        <div>Supervised by doc. Ing. Jan Kom&aacute;rek, Ph.D.</div>
        <div>Submission due March 2027</div>
      </div>
      <p>The thesis tracks snow cover duration across three Czech mountain ranges (Krkono&scaron;e, &Scaron;umava, and Hrub&yacute; Jesen&iacute;k), using 24 years of MODIS satellite data (2000&ndash;2024), split into three elevation bands to test whether temperature or precipitation drives snowpack change at different heights.</p>

      <div class="elev">
        <div class="elev-caption">Where the decline is showing up, by elevation</div>
        <div class="elev-row">
          <div class="elev-label">Above 1,200 m</div>
          <div>
            <div class="elev-bar"></div>
            <div class="elev-note">No significant trend detected</div>
          </div>
        </div>
        <div class="elev-row">
          <div class="elev-label">800&ndash;1,200 m</div>
          <div>
            <div class="elev-bar sig"></div>
            <div class="elev-note">Significant decline (p &lt; 0.05)</div>
          </div>
        </div>
        <div class="elev-row">
          <div class="elev-label">Below 800 m</div>
          <div>
            <div class="elev-bar sig"></div>
            <div class="elev-note">Significant decline (p &lt; 0.05)</div>
          </div>
        </div>
      </div>

      <div class="finding"><span class="mark"></span><span>Snow cover duration is declining below 1,200&nbsp;m across all three ranges, statistically significant in 11 of 18 elevation&ndash;forest categories tested.</span></div>
      <div class="finding"><span class="mark"></span><span>Above 1,200&nbsp;m, no significant trend has turned up yet.</span></div>
      <div class="finding"><span class="mark"></span><span>Temperature tracks the decline more closely than precipitation at every elevation tested, including above 1,200&nbsp;m.</span></div>
      <div class="finding"><span class="mark"></span><span>Cloud cover itself shows no trend over the same period, which rules out satellite cloud obscuration as the cause of the declining signal.</span></div>

      <div class="status-line">In progress. Built with Google Earth Engine, Python (pandas, pyMannKendall), and ArcGIS Pro.</div>
    </section>

    <section id="field">
      <h2>Field work</h2>
      <div class="timeline-row">
        <div class="timeline-date">Mar 2025</div>
        <div>
          <div class="timeline-place">Polar Winter School &mdash; Agricultural University of Iceland, Borgarnes</div>
          <div class="timeline-detail">Snow microstructure, impurity deposition in snow, UAV-based snow cover mapping, arctic snow hydrology.</div>
        </div>
      </div>
      <div class="timeline-row">
        <div class="timeline-date">Jan 2026</div>
        <div>
          <div class="timeline-place">Snow Hydrology Field Course &mdash; Krkono&scaron;e Mountains, Czechia</div>
          <div class="timeline-detail">Snow pit stratigraphy, snow water equivalent measurement, avalanche risk assessment and safety certification.</div>
        </div>
      </div>
    </section>

    <section id="contact">
      <h2>Get in touch</h2>
      <p>Open to research assistant roles, field campaigns, thesis-related collaboration, and infrastructure or DevOps work.</p>
      <div class="contact-links">
        <a href="mailto:nabidsheikh06@gmail.com">nabidsheikh06@gmail.com</a>
        <a href="https://linkedin.com/in/nabidsheikh-431164184">linkedin.com/in/nabidsheikh-431164184</a>
      </div>

      <a class="cv-button" href="/cv" download>
        <svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 1v9m0 0L4.5 6.5M8 10l3.5-3.5M2 12.5v1a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-1" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
        Download CV (PDF)
      </a>
    </section>

    <footer>Rebuilt and redeployed automatically on every push to main.</footer>
  </div>
</body>
</html>
""".replace("__ROOT_VARS__", ROOT_VARS_CSS).replace(
    "__PORTFOLIO_DESCRIPTION__", PORTFOLIO_DESCRIPTION
)


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
def portfolio():
    return PORTFOLIO_PAGE


@app.route("/status")
def status():
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    boot_time = psutil.boot_time()
    cpu = psutil.cpu_percent(interval=0.3)

    return STATUS_PAGE.format(
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


@app.route("/cv")
def cv():
    return send_from_directory(
        app.static_folder, "cv.pdf",
        as_attachment=True, download_name="Nabid_Sheikh_CV.pdf",
    )


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        app.static_folder, "favicon.ico", mimetype="image/vnd.microsoft.icon"
    )


@app.route("/robots.txt")
def robots():
    return send_from_directory(app.static_folder, "robots.txt", mimetype="text/plain")


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
