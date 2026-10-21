# Binance Pump Alerts (Windows)

Desktop app that monitors all Binance USDT-M perpetual futures and shows a Windows notification
with the coin ticker when:

- 24h quote volume >= **30 million USDT** (editable), AND
- price growth >= **4%** within **5 minutes** (editable).

Uses only PUBLIC Binance Futures endpoints. No API key is needed.

## Get the installer (.exe)

The installer is built automatically by GitHub (free):

1. Create a new GitHub repository and upload the contents of this folder (the `.github` folder must be included).
2. Open the **Actions** tab. The "Build Windows installer" workflow starts by itself (or run it manually: Run workflow).
3. When it finishes (about 3-5 minutes), open the run and download the artifact **BinancePumpAlerts-Setup**.
   Inside is `BinancePumpAlerts-Setup.exe`.

Or build locally on Windows: install Python 3.10+ and Inno Setup 6, then run `build.bat`.
The installer is created at `installer_output\BinancePumpAlerts-Setup.exe`.

## Use

1. Install and start the app. Adjust the settings, click **Save settings**, then **Start monitoring**.
2. Alerts appear as Windows notifications. Click **Test notification** to check they work.
   If you do not see them, make sure Windows "Do not disturb" / Focus assist is off.
3. Settings are re-read on every check, so saved changes apply immediately.
4. Keep the window open (it can be minimized). Tick "Start monitoring automatically when the app opens"
   and choose "Start with Windows" in the installer to run it all the time.

Settings are stored in `%APPDATA%\BinancePumpAlerts\settings.json`.

## Sound and alerts log

- The app plays its own two-tone beep on every alert ("Play a sound on every alert" checkbox),
  because Windows often mutes the sound of toast notifications. Use **Test notification** to check it.
  If you hear nothing, check the Windows volume mixer and the selected output device.
- Every alert is also written to `%APPDATA%\BinancePumpAlerts\alerts.log` (button **Alerts log**),
  including the time, coin, growth and price. If a toast could not be shown, the reason is written there too.
  Use it to compare with other alert sources: if the coin is in the log but you did not see a toast,
  Windows hid it (check Focus assist / Do not disturb and Settings > System > Notifications).

## Settings

| Setting | Default | Meaning |
|---|---|---|
| Minimum 24h volume (million USDT) | 30 | Volume filter |
| Volume list refresh interval (s) | 60 | How often the list of qualifying coins is refreshed |
| Minimum price growth (%) | 4 | Pump threshold |
| Time window (minutes) | 5 | Window used to measure growth |
| Price check interval (s) | 15 | How often prices are polled |
| Alert cooldown per coin (min) | 15 | No repeated alerts for the same coin within this time |

## Notes

- The installer is not code-signed, so Windows SmartScreen may show "Windows protected your PC".
  Click **More info -> Run anyway**.
- If the log shows HTTP 451/403 errors, Binance is blocked on your network; use another network or a VPN.

## Run from source (optional)

```
pip install -r requirements.txt
python run.py
python -m unittest discover -s tests -v
```

## Open the coin in Vataga.terminal (v1.3.0)

The buttons **Open in Vataga** (in the popup, the toast and the Recent alerts list) sends the alerted coin to Vataga.terminal through its local HTTP API
(`POST http://localhost:5005/api/open/BinancePumpAlerts/binance/F/BTCUSDT`).

One-time setup in Vataga.terminal:
1. Settings > General > turn on **Application integration**.
2. Right-click the title of the window with the order book > **Link to window** > **Screener**.
3. Keep the terminal running. In this app press **Test Vataga**: BTCUSDT should open in the linked window.

Market `F` = futures (default), `S` = spot. Every alert offers both **Open in Vataga** and **Open on Binance**.
The app registers a per-user link type `binancepumpalerts://` (no admin rights) so the toast button can trigger the request.

## Popup window (v1.4.0)

Every alert also opens an always-on-top popup in the bottom-right corner (works even when Windows hides
toasts because of Focus assist / full-screen apps). It has buttons **Open in Vataga** and **Open on Binance**,
stays until you close it (optional auto-close in seconds in the settings). All alerts are also kept in the **Recent alerts** list in the main window (also after restart, from alerts.log): select one and press Open in Vataga / Open on Binance, or double-click. Both the popup and the toast can be switched off in the app.
If toasts do not appear: Settings > System > Notifications > turn off Focus assist / Do not disturb;
missed toasts are also kept in the notification center (clock icon).

## What's new in 1.7.0 (no WebSocket: low traffic)

- **Mirror mode.** "Alert on": *Growth (+)* (default), *Drop (-), mirror mode* (e.g. minus 4% in 5 minutes) or
  *Growth and drop*. One threshold ("Minimum price move") is used for both directions. Drop alerts are red and
  say "Price fell"; cooldown is kept separately for growth and drop of the same coin.
- **Trade volume spike filter.** When a coin passes the price condition, the app loads its 1-minute candles and
  compares the volume of the last window (e.g. 5 min) with the usual volume of same-size windows over the previous
  N minutes (default 60). "Min volume spike" = 0 turns the filter off (default); 2 means "at least twice the usual".
  The ratio is shown in the alert ("Trade volume: x3.4 of the usual"). A coin that fails only the volume check is not
  put on cooldown and can still alert on a later check. Works for both growth and drops.
- **Connection warning.** If no market data arrives for the number of seconds set in "Warn if no market data"
  (default 60), a red "Connection lost" popup + sound appears once; a green "Connection restored" when data is back.
- Traffic: prices are polled over REST (default every 15 s) and the symbol list is refreshed only every 10 minutes.
