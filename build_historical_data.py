#!/usr/bin/env python3
"""
Russell 1000 Historical Data Builder
====================================

This script builds a complete historical dataset of Russell 1000 stocks using
your Alpaca paper trading account (IEX data feed). It will:

1. Fetch 180+ days of daily closing prices for all 991 Russell 1000 stocks
2. Calculate drawdown metrics for each stock
3. Save clean CSV files ready for S3 upload
4. Handle rate limits and errors gracefully
5. Show progress and data quality metrics

Usage:
    python build_historical_data.py

Requirements:
    pip install requests pandas python-dotenv
"""

import requests
import pandas as pd
import time
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json

from russell_1000_symbols import get_russell_1000_symbols as _get_russell_symbols

class RussellDataBuilder:
    def __init__(self):
        """Initialize the data builder with Alpaca credentials"""
        
        # Load environment variables
        load_dotenv()
        
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        
        if not self.api_key or not self.secret_key:
            raise ValueError("Please set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env file")
        
        self.headers = {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.secret_key
        }
        
        self.base_url = "https://data.alpaca.markets"
        self.data_dir = "data"
        
        # Create data directory
        os.makedirs(self.data_dir, exist_ok=True)
        
        print("Russell 1000 Historical Data Builder")
        print("=" * 50)
        print(f"Data directory: {os.path.abspath(self.data_dir)}")
    
    def get_russell_1000_symbols(self):
        """Return complete Russell 1000 symbols list"""
        symbols = _get_russell_symbols()
        print(f"Complete Russell 1000 list: {len(symbols)} unique stocks")
        return symbols
    
    def fetch_historical_data(self, symbols, days=200):
        """Fetch historical data for all symbols (IEX feed compatible)"""
        
        end_date = datetime.now().date() - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=days)
        
        print(f"Fetching data from {start_date} to {end_date}")
        print(f"Processing {len(symbols)} symbols using IEX feed...")
        print(f"Estimated runtime: {len(symbols) * 0.1 / 60:.1f} minutes")
        
        all_data = []
        failed_symbols = []
        
        for i, symbol in enumerate(symbols):
            # Progress indicator every 50 symbols
            if i > 0 and i % 50 == 0:
                elapsed = i * 0.1 / 60
                remaining = (len(symbols) - i) * 0.1 / 60
                print(f"   Progress: {i}/{len(symbols)} ({i/len(symbols)*100:.1f}%) - "
                      f"Elapsed: {elapsed:.1f}m, Remaining: {remaining:.1f}m")
            
            try:
                # Fetch daily bars for this symbol using IEX feed
                response = requests.get(
                    f"{self.base_url}/v2/stocks/{symbol}/bars",
                    headers=self.headers,
                    params={
                        'timeframe': '1Day',
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat(),
                        'adjustment': 'all',
                        'feed': 'iex',  # Use IEX feed for paper trading compatibility
                        'limit': 1000
                    },
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    bars = data.get('bars', [])
                    
                    if len(bars) >= 30:  # Minimum data requirement
                        # Process each bar
                        for bar in bars:
                            all_data.append({
                                'date': bar['t'][:10],  # Extract date part
                                'symbol': symbol,
                                'open': float(bar['o']),
                                'high': float(bar['h']),
                                'low': float(bar['l']),
                                'close': float(bar['c']),
                                'volume': int(bar['v'])
                            })
                    else:
                        if i < 10:
                            print(f"   {symbol}: Insufficient data ({len(bars)} bars)")
                        failed_symbols.append(symbol)

                elif response.status_code == 403:
                    if i < 10:
                        print(f"   {symbol}: 403 Forbidden")
                    failed_symbols.append(symbol)

                else:
                    if i < 10:
                        print(f"   {symbol}: API error {response.status_code}")
                    failed_symbols.append(symbol)

            except Exception as e:
                if i < 10:
                    print(f"   {symbol}: Error - {str(e)}")
                failed_symbols.append(symbol)
            
            # Rate limiting (conservative with IEX)
            time.sleep(0.1)  # 100ms between requests
        
        print(f"\nData collection complete.")
        print(f"   Successful: {len(symbols) - len(failed_symbols)} symbols")
        print(f"   Failed: {len(failed_symbols)} symbols")
        print(f"   Total data points: {len(all_data):,}")
        
        if failed_symbols and len(failed_symbols) <= 20:
            print(f"   Failed symbols: {', '.join(failed_symbols)}")
        elif len(failed_symbols) > 20:
            print(f"   Failed symbols (first 20): {', '.join(failed_symbols[:20])}...")
        
        return pd.DataFrame(all_data), failed_symbols
    
    def calculate_drawdowns(self, df):
        """Calculate 180-day drawdown metrics for each symbol"""
        
        print(f"Calculating drawdowns for {df['symbol'].nunique()} symbols...")
        
        results = []
        
        for symbol in df['symbol'].unique():
            symbol_data = df[df['symbol'] == symbol].copy()
            symbol_data = symbol_data.sort_values('date')
            
            if len(symbol_data) < 30:
                continue
            
            # Calculate rolling high (expanding window for peak detection)
            symbol_data['rolling_high'] = symbol_data['high'].expanding().max()
            
            # Calculate drawdown from peak
            symbol_data['drawdown_pct'] = (
                (symbol_data['close'] - symbol_data['rolling_high']) / 
                symbol_data['rolling_high'] * 100
            )
            
            # Get latest metrics
            latest = symbol_data.iloc[-1]
            
            # Find when the peak occurred
            peak_rows = symbol_data[symbol_data['rolling_high'] == latest['rolling_high']]
            peak_date = peak_rows['date'].iloc[0]  # First occurrence of this peak
            days_since_peak = (pd.to_datetime(latest['date']) - pd.to_datetime(peak_date)).days
            
            results.append({
                'symbol': symbol,
                'current_price': latest['close'],
                'peak_price': latest['rolling_high'],
                'drawdown_pct': latest['drawdown_pct'],
                'days_since_peak': days_since_peak,
                'data_points': len(symbol_data),
                'date_range_start': symbol_data['date'].min(),
                'date_range_end': symbol_data['date'].max(),
                'last_updated': datetime.now().isoformat()
            })
        
        return pd.DataFrame(results)
    
    def save_datasets(self, price_data, drawdown_data):
        """Save datasets to CSV files"""
        
        print("Saving datasets...")

        price_file = os.path.join(self.data_dir, 'russell_1000_daily_prices.csv')
        price_data.to_csv(price_file, index=False)
        print(f"   Raw price data: {price_file} ({len(price_data):,} rows)")

        drawdown_file = os.path.join(self.data_dir, 'russell_1000_drawdowns.csv')
        drawdown_data.to_csv(drawdown_file, index=False)
        print(f"   Drawdown analysis: {drawdown_file} ({len(drawdown_data)} rows)")

        top_candidates = drawdown_data.nsmallest(50, 'drawdown_pct')
        candidates_file = os.path.join(self.data_dir, 'top_drawdown_candidates.csv')
        top_candidates.to_csv(candidates_file, index=False)
        print(f"   Top candidates: {candidates_file} ({len(top_candidates)} rows)")
        
        # Save metadata
        metadata = {
            'created': datetime.now().isoformat(),
            'total_symbols': len(drawdown_data),
            'date_range': f"{drawdown_data['date_range_start'].min()} to {drawdown_data['date_range_end'].max()}",
            'avg_data_points': round(drawdown_data['data_points'].mean(), 1),
            'data_source': 'Alpaca IEX Feed'
        }
        
        metadata_file = os.path.join(self.data_dir, 'dataset_metadata.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"   Metadata: {metadata_file}")
        
        return price_file, drawdown_file, candidates_file
    
    def show_summary(self, drawdown_data):
        """Show summary statistics"""
        
        print("\nRUSSELL 1000 DATASET SUMMARY")
        print("=" * 60)

        print(f"Total stocks analyzed: {len(drawdown_data)}")
        print(f"Average data points per stock: {drawdown_data['data_points'].mean():.1f}")
        print(f"Date range: {drawdown_data['date_range_start'].min()} to {drawdown_data['date_range_end'].max()}")

        print("\nDrawdown Statistics:")
        print(f"   Worst drawdown: {drawdown_data['drawdown_pct'].min():.1f}%")
        print(f"   Average drawdown: {drawdown_data['drawdown_pct'].mean():.1f}%")
        print(f"   Best performing: {drawdown_data['drawdown_pct'].max():.1f}%")
        print(f"   Average days since peak: {drawdown_data['days_since_peak'].mean():.0f} days")

        print("\nTop 10 Worst Drawdowns:")
        top_10 = drawdown_data.nsmallest(10, 'drawdown_pct')
        for i, (_, row) in enumerate(top_10.iterrows(), 1):
            print(f"   {i:2d}. {row['symbol']:6s}: {row['drawdown_pct']:6.1f}% "
                  f"(${row['current_price']:6.2f} from ${row['peak_price']:6.2f}, "
                  f"{row['days_since_peak']} days ago)")

        print("\nBest Performers:")
        top_performers = drawdown_data.nlargest(5, 'drawdown_pct')
        for i, (_, row) in enumerate(top_performers.iterrows(), 1):
            print(f"   {i}. {row['symbol']:6s}: {row['drawdown_pct']:+6.1f}% "
                  f"(${row['current_price']:6.2f} from ${row['peak_price']:6.2f})")
    
    def run(self):
        """Run the complete data building process"""
        
        try:
            print(f"Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Get complete Russell 1000 symbol list
            symbols = self.get_russell_1000_symbols()
            
            # Fetch historical data
            price_data, failed_symbols = self.fetch_historical_data(symbols)
            
            if price_data.empty:
                print("No data collected. Check your API credentials and IEX access.")
                return
            
            # Calculate drawdowns
            drawdown_data = self.calculate_drawdowns(price_data)
            
            # Save datasets
            files = self.save_datasets(price_data, drawdown_data)
            
            # Show summary
            self.show_summary(drawdown_data)
            
            print(f"\nDataset built successfully.")
            print(f"Files saved in: {os.path.abspath(self.data_dir)}")
            print(f"Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            print("\nNext steps:")
            print(f"   1. Review the CSV files for data quality")
            print(f"   2. Upload to S3: aws s3 cp {self.data_dir}/ s3://your-bucket/data/ --recursive")
            print(f"   3. Deploy Lambda functions via SAM")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            raise

def main():
    """Main entry point"""
    
    # Check for .env file
    if not os.path.exists('.env'):
        print("Please create a .env file with your Alpaca credentials:")
        print("   ALPACA_API_KEY=your_paper_api_key_here")
        print("   ALPACA_SECRET_KEY=your_paper_secret_key_here")
        return
    
    # Run the data builder
    builder = RussellDataBuilder()
    builder.run()

if __name__ == "__main__":
    main()