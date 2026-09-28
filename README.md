# vm-status-app

A tiny live status page for my Oracle Cloud VM — shows CPU, memory, disk, and uptime.

Deployed automatically on every push to `main` via GitHub Actions: the workflow copies the app to the VM, installs dependencies in a virtualenv, and restarts it behind nginx as a systemd service.

**Stack:** Python (Flask + gunicorn), nginx, systemd, GitHub Actions.
