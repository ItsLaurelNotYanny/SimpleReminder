#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Threshold Update Script
Run this manually or automatically (first day of each month) to update thresholds
"""

from threshold_calculator import DynamicThresholdCalculator

# Configuration
CURRENCY_PAIRS = [
    "AUD/CNY",
    "CHF/AUD",
    "USD/AUD",
    "AUD/HKD",
    "HKD/JPY"
]

PERCENTILE = 10  # 10th/90th percentile (captures ~20% of opportunities)
LOOKBACK_DAYS = 365  # One year of historical data


def main():
    """Update all thresholds"""
    print("🚀 Dynamic Threshold Update Tool")
    print()
    
    calculator = DynamicThresholdCalculator()
    
    # Update all thresholds
    thresholds = calculator.update_all_thresholds(
        currency_pairs=CURRENCY_PAIRS,
        percentile=PERCENTILE,
        lookback_days=LOOKBACK_DAYS
    )
    
    print()
    print("📊 Summary:")
    print()
    
    for pair, data in thresholds.items():
        print(f"  {pair:12} → {data['min']:.4f} - {data['max']:.4f}")
    
    print()
    print("💾 Thresholds saved to: data/thresholds.json")
    print("✅ You can now run the monitor with these dynamic thresholds!")
    print()


if __name__ == "__main__":
    main()

