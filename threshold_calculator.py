#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dynamic Threshold Calculator
Uses percentile method to calculate thresholds based on historical data
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path


class DynamicThresholdCalculator:
    """Calculate dynamic thresholds using percentile method"""
    
    def __init__(self, cache_dir="data"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.thresholds_file = self.cache_dir / "thresholds.json"
    
    def fetch_historical_data(self, base, target, days=365):
        """
        Fetch historical exchange rate data from Frankfurter API
        
        Args:
            base: Base currency (e.g., 'AUD')
            target: Target currency (e.g., 'CNY')
            days: Number of days to look back (default: 365)
        
        Returns:
            List of exchange rates
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        url = f"https://api.frankfurter.app/{start_date.strftime('%Y-%m-%d')}..{end_date.strftime('%Y-%m-%d')}"
        params = {"from": base, "to": target}
        
        print(f"   📥 Fetching {days} days of historical data...")
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        # Extract rates from all dates
        rates = []
        for date in sorted(data["rates"].keys()):
            if target in data["rates"][date]:
                rates.append(data["rates"][date][target])
        
        return rates
    
    def calculate_percentile_threshold(self, rates, percentile):
        """
        Calculate threshold at given percentile
        
        Args:
            rates: List of exchange rates
            percentile: Percentile value (e.g., 10 for 10th percentile)
        
        Returns:
            Threshold value at the percentile
        """
        rates_sorted = sorted(rates)
        n = len(rates_sorted)
        index = int(n * percentile / 100)
        
        # Ensure index is within bounds
        index = max(0, min(index, n - 1))
        
        return rates_sorted[index]
    
    def calculate_thresholds(self, pair, percentile=10, lookback_days=365):
        """
        Calculate min/max thresholds for a currency pair
        
        Args:
            pair: Currency pair string (e.g., 'AUD/CNY')
            percentile: Percentile to use (default: 10)
            lookback_days: Days of historical data (default: 365)
        
        Returns:
            Dictionary with threshold information
        """
        base, target = pair.split('/')
        
        # Fetch historical data
        rates = self.fetch_historical_data(base, target, lookback_days)
        
        if not rates:
            raise ValueError(f"No historical data available for {pair}")
        
        # Calculate percentile thresholds
        lower_threshold = self.calculate_percentile_threshold(rates, percentile)
        upper_threshold = self.calculate_percentile_threshold(rates, 100 - percentile)
        
        # Calculate additional stats
        mean_rate = sum(rates) / len(rates)
        min_rate = min(rates)
        max_rate = max(rates)
        
        return {
            "min": round(lower_threshold, 4),
            "max": round(upper_threshold, 4),
            "mean": round(mean_rate, 4),
            "historical_min": round(min_rate, 4),
            "historical_max": round(max_rate, 4),
            "data_points": len(rates),
            "percentile": percentile,
            "lookback_days": lookback_days,
            "last_updated": datetime.now().isoformat()
        }
    
    def update_all_thresholds(self, currency_pairs, percentile=10, lookback_days=365):
        """
        Update thresholds for all currency pairs
        
        Args:
            currency_pairs: List of currency pair strings
            percentile: Percentile to use (default: 10)
            lookback_days: Days of historical data (default: 365)
        
        Returns:
            Dictionary of all thresholds
        """
        thresholds = {}
        
        print("=" * 70)
        print("🔄 Updating Dynamic Thresholds")
        print(f"📊 Method: {percentile}th Percentile")
        print(f"📅 Lookback: {lookback_days} days")
        print("=" * 70)
        print()
        
        for pair in currency_pairs:
            print(f"📈 Processing {pair}...")
            try:
                thresholds[pair] = self.calculate_thresholds(pair, percentile, lookback_days)
                
                print(f"   ✅ Thresholds: {thresholds[pair]['min']} - {thresholds[pair]['max']}")
                print(f"   📊 Based on {thresholds[pair]['data_points']} data points")
                print(f"   💡 Historical range: {thresholds[pair]['historical_min']} - {thresholds[pair]['historical_max']}")
                print()
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                print()
        
        # Save to file
        self.save_thresholds(thresholds)
        
        print("=" * 70)
        print(f"✅ Thresholds updated and saved to {self.thresholds_file}")
        print("=" * 70)
        
        return thresholds
    
    def save_thresholds(self, thresholds):
        """Save thresholds to JSON file"""
        with open(self.thresholds_file, 'w') as f:
            json.dump(thresholds, f, indent=2)
    
    def load_thresholds(self):
        """Load cached thresholds from file"""
        if self.thresholds_file.exists():
            with open(self.thresholds_file, 'r') as f:
                return json.load(f)
        return {}
    
    def should_update(self, day_of_month=1):
        """
        Check if thresholds should be updated
        
        Args:
            day_of_month: Day of month to update (default: 1)
        
        Returns:
            Boolean indicating if update is needed
        """
        # If no thresholds file exists, need to update
        if not self.thresholds_file.exists():
            return True
        
        thresholds = self.load_thresholds()
        
        # If file is empty, need to update
        if not thresholds:
            return True
        
        # Check the last update date
        first_pair = list(thresholds.keys())[0]
        last_updated = datetime.fromisoformat(thresholds[first_pair]["last_updated"])
        
        now = datetime.now()
        
        # Update if it's the specified day of month and hasn't been updated this month
        if now.day == day_of_month and (last_updated.month != now.month or last_updated.year != now.year):
            return True
        
        return False
    
    def get_threshold_status(self):
        """Get status information about current thresholds"""
        if not self.thresholds_file.exists():
            return {
                "exists": False,
                "message": "No thresholds configured. Run update_thresholds.py to initialize."
            }
        
        thresholds = self.load_thresholds()
        
        if not thresholds:
            return {
                "exists": False,
                "message": "Threshold file is empty. Run update_thresholds.py."
            }
        
        first_pair = list(thresholds.keys())[0]
        last_updated = datetime.fromisoformat(thresholds[first_pair]["last_updated"])
        
        return {
            "exists": True,
            "count": len(thresholds),
            "last_updated": last_updated.strftime('%Y-%m-%d %H:%M:%S'),
            "percentile": thresholds[first_pair]["percentile"],
            "lookback_days": thresholds[first_pair]["lookback_days"]
        }


if __name__ == "__main__":
    # Test the calculator
    calculator = DynamicThresholdCalculator()
    
    test_pairs = ["AUD/CNY", "USD/AUD"]
    
    print("🧪 Testing Threshold Calculator\n")
    
    result = calculator.update_all_thresholds(test_pairs, percentile=10, lookback_days=365)
    
    print("\n📋 Results:")
    for pair, data in result.items():
        print(f"{pair}: {data['min']} - {data['max']}")

