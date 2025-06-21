#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import platform
import requests
import time
import subprocess
from datetime import datetime

# Currency pairs with thresholds
RULES = {
    "AUD/CNY": {"min": 4.50, "max": 4.90},
    "CHF/AUD": {"min": 1.50, "max": 1.85},
    "USD/AUD": {"min": 1.40, "max": 1.60},
    "AUD/HKD": {"min": 4.85, "max": 5.25},
}

def send_notification(pair, rate, rule):
    """Send notification based on exchange rate thresholds"""
    os_name = platform.system()
    
    # Determine notification content
    if rate <= rule["min"]:
        title = f"📉 Low Rate Alert: {pair} = {rate}"
        message = f"{pair} has fallen below your minimum threshold ({rule['min']})"
    elif rate >= rule["max"]:
        title = f"📈 High Rate Alert: {pair} = {rate}"
        message = f"{pair} has exceeded your maximum threshold ({rule['max']})"
    else:
        return  # Don't send notification if within threshold
    
    # Send notification based on OS
    if os_name == "Linux":
        subprocess.run(['notify-send', title, message])
    elif os_name == "Darwin":
        apple_script = f'display notification "{message}" with title "{title}"'
        subprocess.run(['osascript', '-e', apple_script])
    else:
        print(f"\n{title}\n{message}\n")

def check_rates():
    """Check exchange rates for monitored currency pairs"""
    # Get exchange rates for all base currencies
    # Web-based functionality (Line 47) requires internet connectivity 
    rates_cache = {}
    for base in set(pair.split('/')[0] for pair in RULES.keys()):
        try:
            response = requests.get(f"https://open.er-api.com/v6/latest/{base}")
            data = response.json()
            if data["result"] == "success":
                rates_cache[base] = data["rates"]
        except Exception as e:
            print(f"Error fetching rates for {base}: {e}")
    
    # Check each currency pair against thresholds
    for pair, rule in RULES.items():
        from_currency, to_currency = pair.split('/')
        
        if from_currency in rates_cache and to_currency in rates_cache[from_currency]:
            rate = rates_cache[from_currency][to_currency]
            
            # Send notification if threshold crossed
            send_notification(pair, rate, rule)
            
            # Log to console
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"{timestamp} - {pair}: {rate} (Alert range: {rule['min']} - {rule['max']})")

def main():
    """Main function"""
    print(f"🚀 Exchange Rate Monitor Started - Watching {len(RULES)} currency pairs")
    
    try:
        while True:
            check_rates()
            time.sleep(3600)  # Check every hour
    except KeyboardInterrupt:
        print("\n✅ Exchange Rate Monitor Stopped")

if __name__ == "__main__":
    main() 