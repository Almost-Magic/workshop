# The Workshop — User Manual

## What Is The Workshop?

The Workshop is the homepage of the Almost Magic Tech Lab. Open it in your browser and you will see every AMTL app laid out as a grid of cards. Each card shows whether the app is running, stopped, or not yet built.

**URL**: http://amtl/workshop/ (or just http://amtl/)

## The Dashboard

### App Cards

Each card shows:
- **App name** — in large heading text
- **Status badge** — LIVE (green), DOWN (red), or COMING SOON (grey)
- **Description** — what the app does
- **Port number** — which port it runs on

Click any LIVE card to open that app in a new browser tab.

### Health Strip

The bar below the header shows three counts:
- **Green** — how many apps are currently running
- **Red** — how many apps are down
- **Grey** — how many apps are not yet built

If any app goes down, the strip background turns red so you notice immediately.

The strip refreshes automatically every 30 seconds. You do not need to reload the page.

### ELAINE Widget

Top-right corner. Shows a green dot when ELAINE is running, red when she is down. Click it to open ELAINE's API documentation.

### Theme Toggle

The moon/sun button in the top-right toggles between dark mode (AMTL Midnight) and light mode. Your choice is saved and persists across sessions.

## Quick Actions

### Start All
Click **Start All** to trigger the startup script that launches every AMTL app. The button shows "Starting..." while it runs, then "Triggered!" when done. The dashboard will refresh after a few seconds to show updated status.

### View Logs
Click **View Logs** to open a panel showing all built apps as buttons. Click any app name to see its recent terminal output (the last 50 lines from its tmux session). Useful for checking if an app crashed or seeing recent activity.

## Troubleshooting

**All cards show DOWN**: The apps may not be running. Click **Start All** to launch them, or ask your administrator to run `bash /home/mani/amtl/start-all.sh`.

**Dashboard does not load**: Check that the Workshop is running on port 5001. Run `curl http://localhost:5001/health` from the server.

**Cards do not update**: The health check runs every 30 seconds. Wait a moment, or reload the page. If an app takes more than 8 seconds to respond to its health check, it will show as DOWN.
