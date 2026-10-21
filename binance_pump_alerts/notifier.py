"""Alerts: Windows toast notification (winotify) + our own sound (winsound) + alerts.log.

The sound is played by the app itself instead of the toast, because Windows often mutes
toast sounds (Focus assist, per-app notification settings). Toasts are shown in a
background thread, so a slow PowerShell call never delays price checks.

On non-Windows systems (e.g. when testing) everything falls back to console output.
"""

from __future__ import annotations

import threading
import time
from decimal import Decimal

from . import vataga
from .settings import APP_NAME, alerts_log_path, load_settings

try:
    from winotify import Notification, audio
except ImportError:  # not on Windows / package missing
    Notification = None
    audio = None

try:
    import winsound
except ImportError:  # not on Windows
    winsound = None

_sound_lock = threading.Lock()

# Set by the GUI: called as listener(symbol, title, message, direction) from any thread; shows the popup window.
alert_listener = None


def _format_price(price: float) -> str:
    return format(Decimal(str(price)).normalize(), "f")


def _append_log(line: str) -> None:
    """Record an alert / problem in alerts.log (never raises)."""
    try:
        path = alerts_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {line}\n")
    except OSError:
        pass


def play_sound() -> None:
    """Play a short two-tone beep without blocking the caller."""
    if winsound is None:
        return

    def _play() -> None:
        if not _sound_lock.acquire(blocking=False):  # a sound is already playing
            return
        try:
            try:
                winsound.Beep(988, 160)
                winsound.Beep(1319, 240)
            except RuntimeError:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        finally:
            _sound_lock.release()

    threading.Thread(target=_play, name="alert-sound", daemon=True).start()


def _show_toast(title: str, message: str, symbol: str | None) -> None:
    try:
        if Notification is None:
            print(f"[notification] {title}: {message}")
            return
        toast = Notification(app_id=APP_NAME, title=title, msg=message, duration="long")
        toast.set_audio(audio.Silent, loop=False)  # sound is played by play_sound()
        if symbol:
            toast.add_actions(label="Open in Vataga", launch=vataga.link_for(symbol))
            toast.add_actions(label="Open on Binance", launch=f"https://www.binance.com/en/futures/{symbol}")
        toast.show()
    except Exception as exc:
        _append_log(f"TOAST FAILED for '{title}': {exc}")


def _notify(symbol: str, title: str, message: str, sound: bool, direction: int = 0) -> None:
    settings = load_settings()
    if sound:
        play_sound()
    if settings.toast_enabled:
        threading.Thread(target=_show_toast, args=(title, message, symbol), daemon=True).start()
    if settings.popup_enabled and alert_listener is not None:
        try:
            alert_listener(symbol, title, message, direction)
        except Exception as exc:
            _append_log(f"POPUP FAILED for '{title}': {exc}")


def show_alert(
    symbol: str,
    change_percent: float,
    price: float,
    window_minutes: int,
    sound: bool = True,
    volume_ratio: float | None = None,
) -> None:
    """Pump (change > 0) or dump (change < 0) alert with the coin ticker in the title."""
    price_text = _format_price(price)
    verb = "rose" if change_percent >= 0 else "fell"
    message = f"Price {verb} {abs(change_percent):.2f}% in {window_minutes} min. Current price: {price_text}"
    log_line = f"ALERT {symbol} {change_percent:+.2f}% in {window_minutes} min, price {price_text}"
    if volume_ratio is not None:
        message += f"\nTrade volume: x{volume_ratio:.1f} of the usual"
        log_line += f", volume x{volume_ratio:.1f}"
    _append_log(log_line)
    _notify(
        symbol=symbol,
        title=f"{symbol}  {change_percent:+.2f}%",
        message=message,
        sound=sound,
        direction=1 if change_percent >= 0 else -1,
    )


def show_warning(title: str, message: str, sound: bool = True) -> None:
    """Problem notice (e.g. connection lost). Shown without coin buttons."""
    _append_log(f"WARNING {title}: {message}")
    _notify(symbol="", title=title, message=message, sound=sound)


def show_test(sound: bool = True) -> None:
    _notify("BTCUSDT", "Test notification", "Notifications are working.", sound)
