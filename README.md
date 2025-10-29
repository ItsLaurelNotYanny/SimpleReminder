# SimpleReminder

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)](https://github.com)

A smart notification system that monitors exchange rates and alerts you when thresholds are crossed. Perfect for catching the best currency exchange opportunities!

## Features

- 📊 **Real-time Exchange Rate Monitoring** - Tracks 5 currency pairs
- 🔔 **Cross-Platform Notifications** - Native alerts on macOS, Linux, and Windows
- 🤖 **Dynamic Thresholds** - Auto-calculated based on historical data (10th percentile)
- 🔑 **Secure API Key Management** - Uses `.env` file for credentials
- ⚡ **Efficient Resource Usage** - Minimal CPU and network overhead
- 🎯 **Intelligent Alerts** - Only notifies for significant rate changes (~20% of opportunities)

## Monitored Currency Pairs

- AUD/CNY (Australian Dollar to Chinese Yuan)
- CHF/AUD (Swiss Franc to Australian Dollar)
- USD/AUD (US Dollar to Australian Dollar)
- AUD/HKD (Australian Dollar to Hong Kong Dollar)
- HKD/JPY (Hong Kong Dollar to Japanese Yen)

## Requirements

- Python 3.6+
- Internet connection
- **No API key required!** (uses free Frankfurter API)
- Optional: Backup API key from [ExchangeRate-API.com](https://www.exchangerate-api.com/) for redundancy

### Platform-Specific Requirements

| Platform | Notification Method | Additional Requirements |
|----------|-------------------|------------------------|
| **macOS** | Native (osascript) | ✅ Built-in, no extras needed |
| **Linux** | notify-send | Install `libnotify-bin` (usually pre-installed) |
| **Windows** | plyer library | Auto-installed with setup |

## Installation

### Quick Setup (Recommended) 🚀

```bash
cd SimpleReminder

# Run the setup script (handles everything automatically)
./setup.sh
```

The setup script will:
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Check for .env file (optional)

### Manual Setup

If you prefer to set up manually:

#### 1. Navigate to Directory

```bash
cd SimpleReminder
```

#### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
# Install all dependencies at once
pip install -r requirements.txt

# Or install manually
pip install requests python-dotenv
```

### 4. Configure Environment (Optional for Backup API)

**The script works out-of-the-box with no configuration!** It uses the free Frankfurter API.

For extra reliability, you can optionally configure a backup API:

1. Visit [https://www.exchangerate-api.com/](https://www.exchangerate-api.com/)
2. Sign up for a free account (1,500 requests/month)
3. Copy your API key
4. Create a `.env` file:

```bash
# Copy the template
cp env_template.txt .env

# Edit .env and add your API key
nano .env
```

Your `.env` file should look like:
```
EXCHANGE_RATE_API_KEY=your_actual_api_key_here
```

**Note:** If you skip this step, the script will still work perfectly using only Frankfurter API.

---

## 🤖 Dynamic Thresholds (Recommended)

Instead of manually setting thresholds, the system can automatically calculate them based on historical data.

### How It Works

1. **Analyzes past year** of exchange rate data
2. **Calculates 10th/90th percentile** thresholds
3. **Notifies only for exceptional rates** (bottom 10% or top 10%)
4. **Updates monthly** to adapt to market trends

### Benefits

✅ **Auto-adaptive** - Follows market trends automatically  
✅ **Data-driven** - Based on 365 days of real data, not guesswork  
✅ **Smart notifications** - Captures ~20% of best opportunities  
✅ **Low maintenance** - Update once per month  

### Setup Dynamic Thresholds

```bash
cd /Users/ellery/Development/SimpleReminder

# Activate virtual environment
source venv/bin/activate

# Generate dynamic thresholds (run once, then monthly)
python update_thresholds.py
```

**Output example:**
```
🔄 Updating Dynamic Thresholds
📊 Method: 10th Percentile
📅 Lookback: 365 days
======================================================================

📈 Processing AUD/CNY...
   📥 Fetching 365 days of historical data...
   ✅ Thresholds: 4.5234 - 4.8765
   📊 Based on 260 data points
   💡 Historical range: 4.4123 - 4.9876

📈 Processing CHF/AUD...
   ✅ Thresholds: 1.5123 - 1.8543
   ...

✅ Thresholds updated and saved to data/thresholds.json
```

### Update Schedule

**Automatic reminder**: The monitor will remind you on the 1st of each month to update thresholds.

**Manual update anytime**:
```bash
python update_thresholds.py
```

### Configuration

Edit `update_thresholds.py` to customize:

```python
PERCENTILE = 10        # 10th/90th percentile (20% opportunities)
LOOKBACK_DAYS = 365    # One year of data
```

**Percentile guide**:
- `5%` = ~18 notifications/year (very selective, best opportunities only)
- `10%` = ~36 notifications/year (balanced, recommended) ⭐
- `15%` = ~55 notifications/year (more frequent)
- `20%` = ~73 notifications/year (very frequent)

---

## Usage

### Run the Monitor

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the script
python exchange_rate_reminder.py

# Or run directly with venv Python (without activation)
./venv/bin/python exchange_rate_reminder.py
```

### What Happens

1. Loads **dynamic thresholds** (if available) or uses static defaults
2. Checks exchange rates every **45 minutes** (~4,000 API calls/month)
3. Uses **Frankfurter API** as primary source (5,000 requests/month)
4. Automatically switches to **backup API** if primary fails
5. Compares rates against thresholds (10th/90th percentile)
6. Sends cross-platform notifications when rates cross thresholds
7. Logs all rates to console with timestamps
8. Reminds you to update thresholds on the 1st of each month

### Example Notification

When AUD/CNY drops below 4.50:
```
📉 Low Rate Alert: AUD/CNY = 4.45
AUD/CNY has fallen below your minimum threshold (4.50)
```

## Customization

### Change Currency Pairs

Edit the currency pairs in `update_thresholds.py`:

```python
CURRENCY_PAIRS = [
    "AUD/CNY",
    "CHF/AUD",
    "USD/AUD",
    "AUD/HKD",
    "HKD/JPY",
    # Add your own pairs here
]
```

Then run `python update_thresholds.py` to generate thresholds.

### Manual Thresholds (Static)

If you prefer manual control, edit `exchange_rate_reminder.py`:

```python
# Static thresholds (in load_thresholds() function)
return {
    "AUD/CNY": {"min": 4.50, "max": 4.90},  # Your custom values
    "CHF/AUD": {"min": 1.50, "max": 1.90},
    # ... more pairs
}
```

**Note**: Manual thresholds are used as fallback when `data/thresholds.json` doesn't exist.

### Adjust Check Interval

Modify the `CHECK_INTERVAL_MINUTES` in the `Config` class:

```python
class Config:
    CHECK_INTERVAL_MINUTES = 45  # Current: 45 minutes
    # For 30 min: = 30
    # For 1 hour: = 60
    # For 2 hours: = 120
```

**Note:** With Frankfurter API (~5,000 requests/month), recommended intervals:
- **45 min** = ~128 API calls/day (~3,840/month) ✅ Optimal (current) ⭐
- **30 min** = ~240 API calls/day (~7,200/month) ⚠️ Exceeds limit
- **1 hour** = ~120 API calls/day (~3,600/month) ✅ Safe
- **2 hours** = ~60 API calls/day (~1,800/month) ✅ Conservative

## API Usage Calculation

### Primary API: Frankfurter (~5,000 requests/month)

- **Free Tier**: ~5,000 requests/month (no registration needed)
- **Each check**: 4-5 API calls (one per base currency)
- **Safe daily usage**: ~165 requests/day = 33 checks/day

| Interval | Daily Checks | Daily API Calls | Monthly Total | Status |
|----------|--------------|-----------------|---------------|--------|
| **45 min** ⭐ | 32 | 128 | ~3,840 | ✅ Optimal (current) |
| 1 hour   | 24           | 96-120          | ~2,880-3,600  | ✅ Safe |
| 2 hours  | 12           | 48-60           | ~1,440-1,800  | ✅ Conservative |
| 30 min   | 48           | 192-240         | ~5,760-7,200  | ❌ Exceeds limit |

### Backup API: ExchangeRate-API (1,500 requests/month, optional)
Only used when Frankfurter API fails. Same rate calculations apply.

## Run in Background (macOS)

### Using nohup with venv

```bash
# Make sure you're in the project directory
cd SimpleReminder

# Run in background using venv Python
nohup ./venv/bin/python exchange_rate_reminder.py > exchange_rate.log 2>&1 &

# Check if it's running
ps aux | grep exchange_rate

# View logs
tail -f exchange_rate.log

# Stop the background process (if needed)
pkill -f exchange_rate_reminder.py
```

### Using launchd (Auto-start on login)

1. Create `~/Library/LaunchAgents/com.user.exchangerate.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.exchangerate</string>
    <key>ProgramArguments</key>
    <array>
        <string>/FULL/PATH/TO/SimpleReminder/venv/bin/python</string>
        <string>/FULL/PATH/TO/SimpleReminder/exchange_rate_reminder.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/FULL/PATH/TO/SimpleReminder</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/FULL/PATH/TO/SimpleReminder/error.log</string>
    <key>StandardOutPath</key>
    <string>/FULL/PATH/TO/SimpleReminder/output.log</string>
</dict>
</plist>
```

**Note**: Replace `/FULL/PATH/TO/SimpleReminder` with your actual project path.

2. Load the service:
```bash
launchctl load ~/Library/LaunchAgents/com.user.exchangerate.plist
```

## Troubleshooting

### "No dynamic thresholds found" warning
- **This is normal on first run!** The script uses static defaults
- Run `python update_thresholds.py` to generate dynamic thresholds
- After generating, restart the monitor to use dynamic thresholds

### "Backup API key not configured" warnings
- **This is normal!** The script works fine without a backup API
- If you want to add redundancy, create a `.env` file with your ExchangeRate-API key
- The warning only appears when the primary (Frankfurter) API fails

### Update threshold reminder on 1st of month
- **This is a helpful reminder**, not an error
- Run `python update_thresholds.py` to update thresholds
- Skip it if you don't need to update this month

### No Notifications Appearing

**macOS:**
- Grant Terminal (or Python) notification permissions:
  - System Preferences → Notifications → Terminal → Allow notifications
  - Or: System Settings → Notifications → Terminal

**Linux:**
- Install notification daemon if missing:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install libnotify-bin
  
  # Fedora/RHEL
  sudo dnf install libnotify
  
  # Arch Linux
  sudo pacman -S libnotify
  ```

**Windows:**
- Ensure `plyer` is installed:
  ```bash
  pip install plyer
  ```
- Check Windows notification settings (allow app notifications)

### API Errors
- Check your API key is valid
- Verify you haven't exceeded the free tier limit (1,500/month)
- Check internet connection

### "Module not found: dotenv" or "Module not found: requests"
```bash
# Activate virtual environment first
source venv/bin/activate

# Then install dependencies
pip install -r requirements.txt
```

## Cross-Platform Support

### Notification Implementation

The system uses the most reliable notification method for each platform:

**macOS (Darwin)**
- ✅ Uses native `osascript` for AppleScript notifications
- ✅ Appears in Notification Center
- ✅ No external dependencies required

**Linux**
- ✅ Uses `notify-send` command
- ✅ Works with GNOME, KDE, XFCE, and other desktop environments
- ℹ️ Requires `libnotify-bin` (usually pre-installed)

**Windows**
- ✅ Uses `plyer` library for native Windows 10/11 toast notifications
- ✅ Automatic fallback to console output if unavailable
- ℹ️ Installed automatically during setup

**Graceful Degradation**
- If native notifications fail on any platform, the system falls back to console output
- Monitoring continues uninterrupted

---

## File Structure

```
SimpleReminder/
├── venv/                       # Virtual environment (do not commit!)
├── exchange_rate_reminder.py   # Main monitoring script (cross-platform)
├── threshold_calculator.py     # Dynamic threshold calculation engine
├── update_thresholds.py        # Monthly threshold update script
├── requirements.txt            # Python dependencies
├── setup.sh                    # Quick setup script
├── data/                       # Data directory
│   ├── thresholds.json        # Calculated thresholds (auto-generated)
│   └── README.md              # Data directory info
├── .env                        # Your API key (optional, do not commit!)
├── env_template.txt           # Template for .env file
├── .gitignore                 # Git ignore rules
├── QUICKSTART.md              # Quick start guide
├── CHANGES.md                 # Change log
└── README.md                  # This file
```

## Security Notes

- ⚠️ **Never commit your `.env` file to Git**
- ⚠️ **Never share your API key publicly**
- ✅ The `.gitignore` file prevents accidental commits
- ✅ Use `env_template.txt` as reference for others

## Upgrade Options

If you need more frequent checks, consider upgrading:

- **Pro Plan** ($10/month): 30,000 requests, hourly updates
- **Business Plan** ($30/month): 125,000 requests, 5-min updates

Visit [ExchangeRate-API.com pricing](https://www.exchangerate-api.com/) for details.

## License

Free to use and modify for personal projects.

## Workflow Recommendation

### Monthly Routine (1st of each month)

```bash
# 1. Update thresholds with latest historical data
python update_thresholds.py

# 2. Restart the monitor (if running)
pkill -f exchange_rate_reminder.py
./venv/bin/python exchange_rate_reminder.py
```

### Daily Use

Just let it run! The monitor will:
- ✅ Check rates every 2 hours
- ✅ Send notifications for exceptional rates
- ✅ Remind you to update on the 1st

---

## Advanced: Understanding the Percentile Method

### Why 10th Percentile?

The system uses the **10th and 90th percentiles** as thresholds:

- **10th percentile**: Rate was **lower** than this only 10% of the time in the past year
- **90th percentile**: Rate was **higher** than this only 10% of the time in the past year

### Example

Past year AUD/CNY rates: 4.40 to 4.95

- Lowest 10% of rates: 4.40 - 4.55 → **10th percentile = 4.55**
- Highest 10% of rates: 4.85 - 4.95 → **90th percentile = 4.85**

**Result**: You get notified when rates enter the **best 20% of opportunities** (top 10% + bottom 10%)

### Comparison with Static Thresholds

| Method | AUD/CNY Example | Notifications/Year |
|--------|----------------|-------------------|
| **Manual** | 4.50 - 4.90 | Unpredictable |
| **10% Percentile** | 4.55 - 4.85 | ~73 days (20%) |
| **5% Percentile** | 4.48 - 4.92 | ~37 days (10%) |

---

## Contributing

Found a bug or want to add features? Feel free to submit issues or pull requests!

---

**Happy Exchange Rate Monitoring! 💱**
