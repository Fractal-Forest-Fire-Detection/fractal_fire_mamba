# 📸 Screenshot Placement Guide

Place your UI screenshots here with the following exact filenames so they appear in the README:

| Filename | Description | Suggested Resolution |
|:---|:---|:---|
| `dashboard_overview.png` | Full dashboard view (all panels visible) | 1920×1080 |
| `tactical_map.png` | Map view with fire spread vectors & node markers | 960×720 |
| `telemetry_panel.png` | Per-node sensor readings and battery health | 960×720 |
| `fractal_analysis.png` | Hurst/Lyapunov plots and chaos metrics | 960×720 |
| `command_terminal.png` | Command terminal with system logs | 960×720 |

## How to capture

1. Start the server: `uvicorn server:app --reload`
2. Open `http://localhost:8000` in Chrome/Edge
3. Use browser DevTools → "Capture full size screenshot" for best results
4. Save images as PNG in this directory
