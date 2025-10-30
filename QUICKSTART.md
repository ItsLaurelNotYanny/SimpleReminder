# 🚀 Quick Start Guide - Dynamic Thresholds

## First Time Setup

### 1. Install Dependencies
```bash
cd SimpleReminder
./setup.sh
```

### 2. Generate Dynamic Thresholds
```bash
source venv/bin/activate
python update_thresholds.py
```

You'll see output like:
```
✅ Thresholds: 4.5435 - 4.7081
📊 Based on 255 data points
💡 Historical range: 4.4104 - 4.7641
```

### 3. Run the Monitor
```bash
./venv/bin/python exchange_rate_reminder.py

# Optional: enable macOS autostart
./venv/bin/python exchange_rate_reminder.py --install-autostart
```

## Monthly Maintenance

On the 1st of each month:

```bash
cd SimpleReminder
source venv/bin/activate
python update_thresholds.py
```

Then restart the monitor if it's running in background.

Notes:
- If you forget to update on the 1st, the monitor will send a weekly reminder until thresholds are updated this month.
- On macOS, notifications use `terminal-notifier` when available and also play a system sound via `afplay` to ensure you can hear the alert.

## Understanding Your Notifications

**Dynamic thresholds capture the best 20% of opportunities:**

- **Low rate alert** = Rate is in the lowest 10% of the past year  
- **High rate alert** = Rate is in the highest 10% of the past year

Example:
```
📉 Low Rate Alert: AUD/CNY = 4.52
AUD/CNY has fallen below your minimum threshold (4.5435)
```

This means: Over the past 365 days, the rate was only this low or lower on about 10% of days. **Good time to exchange!**

## Customization

### Change Percentile (Notification Frequency)

Edit `update_thresholds.py`:

```python
PERCENTILE = 10  # Change to 5 (fewer) or 15 (more) notifications
```

Then run `python update_thresholds.py` again.

### Add/Remove Currency Pairs

Edit `update_thresholds.py`:

```python
CURRENCY_PAIRS = [
    "AUD/CNY",
    "EUR/USD",  # Add new pair
    # "HKD/JPY",  # Comment out to remove
]
```

Then run `python update_thresholds.py` to regenerate.

---

**Need help?** See the full [README.md](README.md)
