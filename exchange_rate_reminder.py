#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import platform
import requests
import time
import subprocess
import os
import shutil
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from threshold_calculator import DynamicThresholdCalculator

# ============================================================================
# Configuration
# ============================================================================

class Config:
    """Centralized configuration"""
    # API settings
    USE_FRANKFURTER_FIRST = True
    API_TIMEOUT = 10
    
    # Monitoring settings
    CHECK_INTERVAL_MINUTES = 45  # 45 minutes = ~4320 requests/month
    
    # Notification settings
    NOTIFICATION_TIMEOUT = 10
    # macOS sound name for terminal-notifier and fallback afplay
    # Common sounds: Basso, Blow, Bottle, Frog, Funk, Glass, Hero,
    # Morse, Ping, Pop, Purr, Sosumi, Submarine, Tink
    MACOS_SOUND_NAME = "Glass"
    # If terminal-notifier doesn't play a sound, also play via afplay
    MACOS_FORCE_SOUND_WITH_AFLAY = True
    
    @property
    def CHECK_INTERVAL_SECONDS(self):
        return self.CHECK_INTERVAL_MINUTES * 60


config = Config()

# ============================================================================
# Platform Detection and Dependencies
# ============================================================================

# Detect OS once at startup
OS_NAME = platform.system()

# Try to import plyer for Windows notifications
try:
    from plyer import notification
    HAS_PLYER = True
except ImportError:
    HAS_PLYER = False
    if OS_NAME == "Windows":
        print("⚠️  Warning: plyer not installed. Windows notifications disabled.")
        print("   Install with: pip install plyer")

# Load environment variables
load_dotenv()
API_KEY = os.getenv('EXCHANGE_RATE_API_KEY')

# Initialize threshold calculator
calculator = DynamicThresholdCalculator()

# Load dynamic thresholds or use defaults
def load_thresholds():
    """Load dynamic thresholds from file or use static defaults"""
    status = calculator.get_threshold_status()
    
    if status["exists"]:
        thresholds = calculator.load_thresholds()
        print(f"✅ Loaded dynamic thresholds (updated: {status['last_updated']})")
        print(f"   Method: {status['percentile']}th percentile, {status['lookback_days']} days lookback")
        return thresholds
    else:
        print("⚠️  No dynamic thresholds found. Using static defaults.")
        print("   💡 Run 'python update_thresholds.py' to enable dynamic thresholds")
        # Static fallback thresholds
        return {
            "AUD/CNY": {"min": 4.50, "max": 4.90},
            "CHF/AUD": {"min": 1.50, "max": 1.90},
            "USD/AUD": {"min": 1.40, "max": 1.60},
            "AUD/HKD": {"min": 4.85, "max": 5.25},
            "HKD/JPY": {"min": 18.62, "max": 19.85},
        }

# Load thresholds at startup
RULES = load_thresholds()

# Pre-calculate base currencies (avoid recomputing every check)
BASE_CURRENCIES = set(pair.split('/')[0] for pair in RULES.keys())

# ============================================================================
# Platform-Specific Notification Functions
# ============================================================================

def _notify_macos(title, message):
    """Send notification on macOS.
    Prefer terminal-notifier (if available) for better visibility/sound,
    and fall back to AppleScript otherwise.
    """
    abs_notifier = "/opt/homebrew/bin/terminal-notifier"
    notifier_path = abs_notifier if os.path.exists(abs_notifier) else shutil.which('terminal-notifier')
    if notifier_path:
        sound_name = getattr(config, 'MACOS_SOUND_NAME', 'Glass') or 'Glass'
        subprocess.run([
            notifier_path,
            '-title', title,
            '-message', message,
            '-sound', sound_name,
        ], check=True)
        # Optional: force sound using afplay in case notification sound is muted by system policy
        if getattr(config, 'MACOS_FORCE_SOUND_WITH_AFLAY', False):
            sound_path = f"/System/Library/Sounds/{sound_name}.aiff"
            if os.path.exists(sound_path):
                try:
                    subprocess.run(['/usr/bin/afplay', sound_path], check=False)
                except Exception:
                    pass
        return
    # Fallback to AppleScript (use explicit path and JSON to safely escape)
    apple_script = f'display notification {json.dumps(message)} with title {json.dumps(title)}'
    subprocess.run(['/usr/bin/osascript', '-e', apple_script], check=True)


def _notify_linux(title, message):
    """Send notification on Linux using notify-send"""
    subprocess.run(['notify-send', title, message], check=True)


def _notify_windows(title, message):
    """Send notification on Windows using plyer"""
    if not HAS_PLYER:
        raise RuntimeError("plyer not installed")
    notification.notify(
        title=title,
        message=message,
        app_name='Exchange Rate Monitor',
        timeout=config.NOTIFICATION_TIMEOUT
    )


# Map OS names to notification functions
NOTIFIERS = {
    "Darwin": _notify_macos,
    "Linux": _notify_linux,
    "Windows": _notify_windows,
}


# Lightweight info notification wrapper and reminder state
MONTHLY_REMINDER_SHOWN = False  # show monthly reminder at most once per run
NEXT_WEEKLY_REMINDER_AT = None  # schedule weekly follow-ups until updated

def notify_info(title, message):
    """Send an informational notification using platform notifier with console fallback."""
    notifier = NOTIFIERS.get(OS_NAME)
    if notifier:
        try:
            notifier(title, message)
            print(f"ℹ️  Reminder shown: {title}")
            return
        except Exception as e:
            print(f"⚠️  Reminder notification failed: {e}")
    print(f"\n{'='*60}\n{title}\n{message}\n{'='*60}\n")

def thresholds_outdated_this_month() -> bool:
    """Return True if thresholds are missing or last_updated is before the current month."""
    try:
        status = calculator.get_threshold_status()
        if not status.get("exists"):
            return True
        last = datetime.fromisoformat(status.get("last_updated"))
        now = datetime.now()
        return (last.year, last.month) != (now.year, now.month)
    except Exception:
        # If anything goes wrong, be conservative and remind
        return True


def send_notification(pair, rate, rule):
    """Send cross-platform notification based on exchange rate thresholds"""
    # Determine notification content
    if rate <= rule["min"]:
        title = f"📉 Low Rate Alert: {pair} = {rate:.4f}"
        message = f"{pair} has fallen below your minimum threshold ({rule['min']})"
    elif rate >= rule["max"]:
        title = f"📈 High Rate Alert: {pair} = {rate:.4f}"
        message = f"{pair} has exceeded your maximum threshold ({rule['max']})"
    else:
        return  # Don't send notification if within threshold
    
    # Try platform-specific notification
    notifier = NOTIFIERS.get(OS_NAME)
    if notifier:
        try:
            notifier(title, message)
            print(f"✅ Notification sent: {title}")
            return
        except FileNotFoundError:
            if OS_NAME == "Linux":
                print("⚠️  notify-send not found. Install: sudo apt-get install libnotify-bin")
        except Exception as e:
            print(f"⚠️  {OS_NAME} notification failed: {e}")
    
    # Fallback: Console output
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{message}")
    print(f"{'='*60}\n")

# ============================================================================
# API Fetching Functions
# ============================================================================

def _fetch_api(url, parser_func, api_name):
    """Unified API fetching wrapper with error handling"""
    try:
        response = requests.get(url, timeout=config.API_TIMEOUT)
        if response.status_code == 200:
            return parser_func(response.json())
        else:
            print(f"⚠️  {api_name} returned status {response.status_code}")
            return None
    except requests.Timeout:
        print(f"⏱️  {api_name} timeout")
        return None
    except requests.RequestException as e:
        print(f"🌐 {api_name} network error: {e}")
        return None
    except Exception as e:
        print(f"❌ {api_name} error: {e}")
        return None


def fetch_rates_frankfurter(base):
    """Fetch rates from Frankfurter API (Primary, no key needed)"""
    return _fetch_api(
        url=f"https://api.frankfurter.app/latest?from={base}",
        parser_func=lambda data: data.get("rates", {}),
        api_name=f"Frankfurter API ({base})"
    )


def fetch_rates_exchangerate_api(base):
    """Fetch rates from ExchangeRate-API.com (Backup, requires key)"""
    if not API_KEY:
        return None
    
    def parse_exchangerate(data):
        if data.get("result") == "success":
            return data.get("conversion_rates", {})
        error_type = data.get("error-type", "Unknown error")
        print(f"⚠️  ExchangeRate-API error for {base}: {error_type}")
        return None
    
    return _fetch_api(
        url=f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/{base}",
        parser_func=parse_exchangerate,
        api_name=f"ExchangeRate-API ({base})"
    )

# ============================================================================
# Main Monitoring Logic
# ============================================================================

def check_rates():
    """Check exchange rates for monitored currency pairs"""
    rates_cache = {}
    
    # Fetch rates for all base currencies
    for base in BASE_CURRENCIES:
        rates = None
        
        # Try primary API first
        if config.USE_FRANKFURTER_FIRST:
            rates = fetch_rates_frankfurter(base)
            
            # If primary fails, try backup API
            if rates is None and API_KEY:
                print(f"🔄 Switching to backup API for {base}...")
                rates = fetch_rates_exchangerate_api(base)
        else:
            # Use ExchangeRate-API as primary
            rates = fetch_rates_exchangerate_api(base)
            
            # If primary fails, try Frankfurter as backup
            if rates is None:
                print(f"🔄 Switching to Frankfurter API for {base}...")
                rates = fetch_rates_frankfurter(base)
        
        if rates:
            rates_cache[base] = rates
    
    # Check if we got any data at all
    if not rates_cache:
        print("❌ Unable to fetch any exchange rates. Check your internet connection.")
        return
    
    # Check each currency pair against thresholds
    for pair, rule in RULES.items():
        from_currency, to_currency = pair.split('/')
        
        if from_currency in rates_cache and to_currency in rates_cache[from_currency]:
            rate = rates_cache[from_currency][to_currency]
            
            # Send notification if threshold crossed
            send_notification(pair, rate, rule)
            
            # Log to console
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"{timestamp} - {pair}: {rate:.4f} (Alert range: {rule['min']} - {rule['max']})")
        else:
            print(f"⚠️  No data available for {pair}")

def main():
    """Main monitoring loop"""
    # Calculate API usage
    checks_per_day = (24 * 60) // config.CHECK_INTERVAL_MINUTES
    api_calls_per_day = checks_per_day * len(BASE_CURRENCIES)
    api_calls_per_month = api_calls_per_day * 30
    
    # Print startup info
    print("=" * 70)
    print(f"🚀 Exchange Rate Monitor Started")
    print(f"🖥️  Platform: {OS_NAME}")
    print(f"📊 Watching {len(RULES)} currency pairs")
    print("=" * 70)
    
    # API configuration
    if config.USE_FRANKFURTER_FIRST:
        print(f"🔑 Primary API: Frankfurter.app (Free, ~5,000 requests/month)")
        if API_KEY:
            print(f"🔐 Backup API: ExchangeRate-API.com (1,500 requests/month)")
        else:
            print(f"💡 Backup API: Not configured (optional)")
    else:
        print(f"🔑 Primary API: ExchangeRate-API.com (1,500 requests/month)")
        print(f"🔐 Backup API: Frankfurter.app (~5,000 requests/month)")
    
    # Monitoring schedule
    print(f"⏰ Check interval: {config.CHECK_INTERVAL_MINUTES} minutes")
    print(f"📈 Daily checks: ~{checks_per_day} times ({api_calls_per_day} API calls/day)")
    print(f"📊 Monthly usage: ~{api_calls_per_month} API calls/month")
    print("=" * 70)
    print()
    
    # Gentle monthly reminder (once per run on the 1st), plus weekly follow-ups if still outdated
    global MONTHLY_REMINDER_SHOWN, NEXT_WEEKLY_REMINDER_AT
    now = datetime.now()
    if now.day == 1 and not MONTHLY_REMINDER_SHOWN and thresholds_outdated_this_month():
        notify_info(
            "Time to update thresholds",
            "It's the 1st of the month.\nRun: python update_thresholds.py"
        )
        MONTHLY_REMINDER_SHOWN = True
        # schedule first weekly follow-up in 7 days
        NEXT_WEEKLY_REMINDER_AT = now + timedelta(days=7)
    
    # Main monitoring loop
    try:
        while True:
            check_rates()
            # Weekly follow-up if still outdated (only once per 7 days)
            if thresholds_outdated_this_month() and NEXT_WEEKLY_REMINDER_AT is not None:
                if datetime.now() >= NEXT_WEEKLY_REMINDER_AT:
                    notify_info(
                        "Reminder: update thresholds",
                        "Thresholds not updated this month yet.\nRun: python update_thresholds.py"
                    )
                    NEXT_WEEKLY_REMINDER_AT = datetime.now() + timedelta(days=7)
            print(f"\n⏳ Next check in {config.CHECK_INTERVAL_MINUTES} minutes...\n")
            time.sleep(config.CHECK_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\n✅ Exchange Rate Monitor Stopped")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Monitor stopped. Please check logs and restart.")

if __name__ == "__main__":
    # ----------------------------------------------------------------------
    # Optional: manage macOS autostart via launchd
    # ----------------------------------------------------------------------
    parser = argparse.ArgumentParser(description="Exchange Rate Monitor")
    parser.add_argument("--install-autostart", action="store_true", help="Install and load launchd to auto-start on login (macOS)")
    parser.add_argument("--remove-autostart", action="store_true", help="Unload and remove launchd auto-start (macOS)")
    parser.add_argument("--autostart-status", action="store_true", help="Print auto-start status (macOS)")
    args = parser.parse_args()

    def _plist_path() -> Path:
        return Path.home() / "Library" / "LaunchAgents" / "com.simplereminder.exchangerate.plist"

    def _ensure_plist():
        project_dir = Path(__file__).resolve().parent
        python_bin = Path(os.environ.get("VIRTUAL_ENV", project_dir / "venv")).joinpath("bin", "python")
        if not python_bin.exists():
            # Fallback to current interpreter
            python_bin = Path(os.sys.executable)
        script_path = Path(__file__).resolve()
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.simplereminder.exchangerate</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_bin}</string>
        <string>{script_path}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{project_dir}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{project_dir}/exchange_rate.out.log</string>
    <key>StandardErrorPath</key>
    <string>{project_dir}/exchange_rate.err.log</string>
</dict>
</plist>
"""
        plist_path = _plist_path()
        plist_path.parent.mkdir(parents=True, exist_ok=True)
        plist_path.write_text(plist_content)
        return plist_path

    def _launchctl(*cmd):
        try:
            subprocess.run(["launchctl", *cmd], check=True)
            return True
        except Exception:
            return False

    if OS_NAME == "Darwin":
        if args.install_autostart:
            plist_path = _ensure_plist()
            _launchctl("unload", str(plist_path))  # unload if already loaded
            ok = _launchctl("load", str(plist_path))
            print("✅ Autostart installed and loaded" if ok else "⚠️ Failed to load launchd service")
            exit(0)
        if args.remove_autostart:
            plist_path = _plist_path()
            _launchctl("unload", str(plist_path))
            if plist_path.exists():
                try:
                    plist_path.unlink()
                    print("✅ Autostart removed")
                except Exception as e:
                    print(f"⚠️ Failed to remove plist: {e}")
            else:
                print("ℹ️ Autostart not installed")
            exit(0)
        if args.autostart_status:
            plist_path = _plist_path()
            exists = plist_path.exists()
            print(f"Plist: {plist_path} -> {'present' if exists else 'missing'}")
            if exists:
                # best-effort check
                _launchctl("print", f"gui/{os.getuid()}/com.simplereminder.exchangerate")
            exit(0)

    # Run the normal monitor
    main()