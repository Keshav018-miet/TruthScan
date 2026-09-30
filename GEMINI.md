# TruthScan Antigravity Workspace Rules

## Always-Active Server & Live Tunnel Policy
Whenever a session starts, resumes, or whenever the background tasks are detected as stopped/restarted:
1. Always verify that the Flask server (`python app.py` in `D:\mjhg\truthscan`) is running in the background. If not, launch it as a background daemon task.
2. Always verify that the Cloudflare tunnel (`.\cloudflared_new.exe tunnel --url http://127.0.0.1:5000` in `D:\mjhg\truthscan`) is running in the background. If not, launch it as a background daemon task.
3. Automatically retrieve the latest active `trycloudflare.com` URL from the tunnel log and provide it to the user whenever the server is restarted or whenever the user asks for the link.
4. Auto-commit and push any new feature code to GitHub repository `Keshav018-miet/TruthScan.git` on the `main` branch.
