# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-10-30

### Added
- **macOS Notifications Enhancement**: Prioritize `terminal-notifier` for native notifications with fallback to `osascript`
- **Audible Alerts**: Added `afplay` sound fallback to ensure audible notifications even when notifier sound is muted
- **Threshold Update Reminders**: Monthly reminder on the 1st of each month to update dynamic thresholds
- **Weekly Follow-up Reminders**: If threshold update is missed, weekly reminders until updated
- **macOS Autostart Management**: Command-line flags for launchd integration
  - `--install-autostart`: Install and enable autostart on login
  - `--remove-autostart`: Remove autostart configuration
  - `--autostart-status`: Check current autostart status
- **Documentation**: Added macOS notification screenshot (`docs/images/macos-notifications.png`)
- **Technical Documentation**: Created detailed implementation guide (`docs/DYNAMIC_THRESHOLDS_IMPLEMENTATION.md`)

### Changed
- **English-only Codebase**: Translated all Chinese text in documentation and comments to English
- **README.md**: Updated feature descriptions and usage examples
- **Notification Reliability**: Improved cross-platform notification handling with better fallbacks

### Improved
- **User Experience**: More reliable and audible notifications on macOS
- **Maintenance**: Automated reminder system reduces manual tracking overhead
- **Documentation**: Clearer setup instructions with visual examples

## [0.1.0] - 2025-10-29

### Added
- **Dynamic Threshold System**: Automated threshold calculation based on historical data
- **Percentile Method**: Uses 10th/90th percentile from 365 days of exchange rate history
- **Threshold Calculator** (`threshold_calculator.py`): Core engine for percentile calculations
- **Threshold Update Script** (`update_thresholds.py`): Standalone script for monthly threshold updates
- **Smart Notifications**: Only alerts for exceptional rates (top/bottom 20% opportunities)
- **Auto-adaptive Thresholds**: Self-adjusting based on market trends
- **Data Persistence**: JSON-based threshold storage with metadata
- **Quick Start Guide** (`QUICKSTART.md`): Step-by-step setup instructions
- **Comprehensive Documentation**: 
  - How percentile method works
  - Why 10% is recommended
  - Example calculations and comparison tables
  - Monthly workflow recommendations

### Features
- **5 Currency Pairs Monitored**:
  - AUD/CNY (Australian Dollar to Chinese Yuan)
  - CHF/AUD (Swiss Franc to Australian Dollar)
  - USD/AUD (US Dollar to Australian Dollar)
  - AUD/HKD (Australian Dollar to Hong Kong Dollar)
  - HKD/JPY (Hong Kong Dollar to Japanese Yen)

- **Cross-Platform Support**:
  - macOS: Native notifications via osascript
  - Linux: notify-send
  - Windows: plyer library

- **Dual API Support**:
  - Primary: Frankfurter API (free, ~5,000 requests/month)
  - Backup: ExchangeRate-API (optional, 1,500 requests/month)

- **Intelligent Checking**:
  - Check interval: 45 minutes (~128 API calls/day, ~3,840/month)
  - Automatic failover between APIs
  - Graceful degradation on errors

### Technical Details
- **Data-Driven**: Analyzes 365 days of historical data
- **Low Maintenance**: 5-minute monthly update process
- **Configurable**: Adjustable percentile levels (5%, 10%, 15%, 20%)
- **Fallback Strategy**: Uses static defaults if dynamic thresholds unavailable

---

## Version History Summary

- **v0.2.0** - Enhanced notifications, autostart support, English-only version
- **v0.1.0** - Initial release with dynamic threshold system

## Links

- [Technical Implementation Details](docs/DYNAMIC_THRESHOLDS_IMPLEMENTATION.md)
- [Quick Start Guide](QUICKSTART.md)
- [Platform Support Details](PLATFORM_SUPPORT.md)

