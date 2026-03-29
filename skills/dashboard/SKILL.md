---
name: dashboard
description: Open the Atelier Dashboard in your browser. Starts the brain HTTP server if needed and launches the telemetry visualization page.
---

# Dashboard Skill

Open the Atelier Dashboard -- a telemetry visualization page showing pipeline
cost, quality trends, agent fitness, and degradation alerts.

## Procedure

1. Check if the brain HTTP server is already running:

```bash
curl -s http://localhost:8788/api/health
```

2. If the health check fails (server not running), start the brain HTTP server
   in the background:

```bash
node ${CLAUDE_PLUGIN_ROOT}/brain/server.mjs http &
```

3. Wait 2 seconds for the server to start, then verify it is healthy:

```bash
sleep 2
curl -s http://localhost:8788/api/health
```

4. Open the dashboard in the default browser. Use the appropriate command for
   the current OS:

   - **macOS:** `open http://localhost:8788/ui/dashboard.html`
   - **Linux:** `xdg-open http://localhost:8788/ui/dashboard.html`
   - **Windows WSL:** `cmd.exe /c start http://localhost:8788/ui/dashboard.html`

5. Print confirmation:

```
Dashboard opened at http://localhost:8788/ui/dashboard.html
```

## Notes

- The dashboard auto-refreshes every 30 seconds.
- If no telemetry data exists yet, the dashboard shows a graceful empty state.
- The dashboard requires the brain to have telemetry data (thoughts with
  `thought_type='insight'` and `source_phase='telemetry'`). Run at least one
  pipeline with telemetry capture enabled to populate data.
