#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import platform
import requests
import time
import subprocess
import os
from datetime import datetime
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
    """Send notification on macOS using osascript"""
    apple_script = f'display notification "{message}" with title "{title}"'
    subprocess.run(['osascript', '-e', apple_script], check=True)


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
    
    # Check if thresholds need updating
    if calculator.should_update():
        print("🔄 Note: It's time to update dynamic thresholds!")
        print("   Run: python update_thresholds.py")
        print()
    
    # Main monitoring loop
    try:
        while True:
            check_rates()
            print(f"\n⏳ Next check in {config.CHECK_INTERVAL_MINUTES} minutes...\n")
            time.sleep(config.CHECK_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\n✅ Exchange Rate Monitor Stopped")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Monitor stopped. Please check logs and restart.")

if __name__ == "__main__":
    main() 