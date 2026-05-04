import json
import boto3
import os
import requests
import pandas as pd
import time
from datetime import datetime, timedelta

def lambda_handler(event, context):
    print("Starting Russell 1000 daily analysis...")
    start_time = time.time()
    
    try:
        # Initialize clients
        ssm = boto3.client('ssm')
        s3 = boto3.client('s3')
        
        # Get API credentials
        polygon_api_key = ssm.get_parameter(
            Name='/screener/polygon/api_key',
            WithDecryption=True
        )['Parameter']['Value']
        
        alpaca_api_key = ssm.get_parameter(
            Name='/screener/alpaca/api_key',
            WithDecryption=True
        )['Parameter']['Value']
        
        alpaca_secret_key = ssm.get_parameter(
            Name='/screener/alpaca/secret_key',
            WithDecryption=True
        )['Parameter']['Value']
        
        alpaca_base_url = ssm.get_parameter(
            Name='/screener/alpaca/base_url'
        )['Parameter']['Value']
        
        alpaca_headers = {
            'APCA-API-KEY-ID': alpaca_api_key,
            'APCA-API-SECRET-KEY': alpaca_secret_key
        }
        
        today = datetime.now().date()
        print(f"Analysis date: {today}")
        
        # Get COMPLETE Russell 1000 symbols from CSV files
        russell_symbols = get_complete_russell_1000_symbols()
        print(f"Analyzing {len(russell_symbols)} Russell 1000 stocks")

        current_data = get_current_market_data(polygon_api_key, russell_symbols)
        print(f"Current data for {len(current_data)} stocks")

        drawdown_results = calculate_180_day_drawdowns_optimized(polygon_api_key, current_data, today)
        print(f"Calculated drawdowns for {len(drawdown_results)} stocks")

        ranked_results = rank_drawdown_results(drawdown_results, today)
        top_candidates = ranked_results[:10]

        portfolio_data = collect_portfolio_data(alpaca_headers, alpaca_base_url, today)
        print(f"Portfolio: {len(portfolio_data)} positions")
        bucket_name = os.environ.get('S3_BUCKET_NAME')
        files_saved = 0
        
        if ranked_results:
            append_to_csv(s3, bucket_name, 'russell_1000_drawdown_results.csv', ranked_results)
            files_saved += 1
        if top_candidates:
            save_to_csv(s3, bucket_name, 'daily_top_candidates.csv', top_candidates)
            files_saved += 1
        if portfolio_data:
            append_to_csv(s3, bucket_name, 'portfolio_snapshots.csv', portfolio_data)
            files_saved += 1
        
        execution_time = time.time() - start_time
        
        summary = {
            'date': today.isoformat(),
            'stocks_analyzed': len(drawdown_results),
            'portfolio_positions': len(portfolio_data),
            'worst_drawdown': min([r['drawdown_pct'] for r in ranked_results]) if ranked_results else 0,
            'best_candidate': top_candidates[0]['symbol'] if top_candidates else None,
            'execution_time_seconds': round(execution_time, 2),
            'csv_files_updated': files_saved,
            'data_source': 'Polygon 180-Day Complete CSV Russell 1000',
            'status': 'success'
        }
        
        print(f"Processing completed in {execution_time:.1f}s")
        print(f"Summary: {summary}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(summary, default=str)
        }
        
    except Exception as e:
        import traceback
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e), 'status': 'failed'})
        }

def get_complete_russell_1000_symbols():
    
    symbols = [
        'A', 'AAON', 'AAL', 'AAPL', 'ABT', 'ABBV', 'ABNB', 'ACN', 'ACGL', 'ADC', 'ADP', 
        'ADBE', 'ADI', 'ADM', 'ADSK', 'ADT', 'AEE', 'AEP', 'AES', 'AFG', 'AFL', 'AIG', 
        'AIZ', 'AJG', 'AKAM', 'AL', 'ALB', 'ALGM', 'ALGN', 'ALK', 'ALL', 'ALLE', 'ALNY', 
        'ALSN', 'AM', 'AMAT', 'AMCR', 'AMD', 'AME', 'AMG', 'AMGN', 'AMKR', 'AMP', 'AMT', 
        'AMTM', 'AMZN', 'AN', 'ANET', 'AON', 'AOS', 'APA', 'APD', 'APH', 'APO', 'APP', 
        'APTV', 'APLS', 'ARE', 'ARW', 'ASH', 'ATI', 'ATO', 'ATR', 'AVGO', 'AVB', 'AVTR', 
        'AVY', 'AWI', 'AWK', 'AXP', 'AXON', 'AXTA', 'AZO', 'AUR', 'AXS',
        'BA', 'BAC', 'BAM', 'BALL', 'BAX', 'BBY', 'BC', 'BDX', 'BEN', 'BF.B', 'BG', 
        'BHF', 'BIIB', 'BIO', 'BIRK', 'BK', 'BKNG', 'BKR', 'BLK', 'BLDR', 'BILL', 'BMY', 
        'BOKF', 'BPOP', 'BR', 'BRO', 'BROS', 'BRX', 'BRBR', 'BRKR', 'BSX', 'BX', 'BXP', 
        'BYD',
        'C', 'CAG', 'CAH', 'CAI', 'CAR', 'CACC', 'CARR', 'CAT', 'CAVA', 'CB', 'CBOE', 
        'CBSH', 'CCI', 'CCL', 'CDNS', 'CDW', 'CE', 'CEG', 'CBRE', 'CFG', 'CFLT', 'CFR', 
        'CHD', 'CHE', 'CHH', 'CHDN', 'CHRD', 'CHTR', 'CHRW', 'CI', 'CINF', 'CL', 'CLF', 
        'CLX', 'CMS', 'CME', 'CMG', 'CMI', 'CMCSA', 'CNC', 'CNP', 'CNX', 'CNXC', 'COF', 
        'COIN', 'COLB', 'COLM', 'COO', 'COP', 'COR', 'CORT', 'COST', 'COTY', 'CPB', 'CPAY', 
        'CPNG', 'CPRT', 'CPT', 'CTAS', 'CTSH', 'CTRA', 'CTVA', 'CUBE', 'CUZ', 'CVNA', 
        'CVS', 'CVX', 'CWEN', 'CXT', 'CZR',
        'D', 'DAL', 'DAR', 'DASH', 'DAY', 'DBX', 'DD', 'DDOG', 'DE', 'DECK', 'DELL', 
        'DG', 'DGX', 'DHI', 'DHR', 'DIS', 'DJT', 'DLB', 'DLR', 'DLTR', 'DOC', 'DOV', 
        'DOW', 'DPZ', 'DRI', 'DTE', 'DUK', 'DVA', 'DVN', 'DXC', 'DXCM',
        'EA', 'EBAY', 'ECG', 'ECL', 'ED', 'EFX', 'EG', 'EIX', 'EL', 'ELF', 'ELV', 'EME', 
        'EMN', 'EMR', 'ENPH', 'EOG', 'EPAM', 'EPR', 'EQR', 'EQT', 'EQIX', 'ERIE', 'ES', 
        'ESAB', 'ESI', 'ESS', 'ETN', 'ETR', 'ETSY', 'EVRG', 'EW', 'EXC', 'EXE', 'EXLS', 
        'EXP', 'EXPD', 'EXPE', 'EXR',
        'F', 'FAF', 'FANG', 'FAST', 'FBIN', 'FCN', 'FCX', 'FDS', 'FDX', 'FE', 'FERG', 
        'FHB', 'FI', 'FICO', 'FIS', 'FITB', 'FIVE', 'FLO', 'FLS', 'FLUT', 'FLS', 'FND', 
        'FNB', 'FOX', 'FR', 'FRHC', 'FRT', 'FRPT', 'FSLR', 'FTI', 'FTNT', 'FTV', 'FOUR',
        'G', 'GAP', 'GDDY', 'GD', 'GE', 'GEHC', 'GEN', 'GEV', 'GILD', 'GIS', 'GL', 'GLOB', 
        'GLW', 'GMED', 'GM', 'GNRC', 'GOOG', 'GPC', 'GPK', 'GPN', 'GRMN', 'GS', 'GTES', 
        'GTLB', 'GTM', 'GWW', 'GXO',
        'HAL', 'HALO', 'HAS', 'HBAN', 'HCA', 'HD', 'HEI', 'HES', 'HHH', 'HIG', 'HII', 
        'HIW', 'HL', 'HLT', 'HLNE', 'HOG', 'HOLX', 'HON', 'HOOD', 'HPE', 'HPQ', 'HR', 
        'HRB', 'HRL', 'HST', 'HSIC', 'HSY', 'HUBB', 'HUM', 'HWM', 'HXL',
        'IAC', 'IBM', 'IBKR', 'ICE', 'IDA', 'IDXX', 'IEX', 'IFF', 'INGM', 'INGR', 'INCY', 
        'INFA', 'INSM', 'INSP', 'INTC', 'INTU', 'INVH', 'IP', 'IPG', 'IPGP', 'IQV', 'IR', 
        'IRM', 'ISRG', 'IT', 'ITW', 'IVZ',
        'J', 'JAZZ', 'JBL', 'JBHT', 'JCI', 'JHG', 'JKHY', 'JNJ', 'JPM',
        'K', 'KBR', 'KD', 'KEY', 'KEYS', 'KEX', 'KHC', 'KIM', 'KLAC', 'KMB', 'KMI', 'KMPR', 
        'KMX', 'KNX', 'KO', 'KKR', 'KR', 'KRC', 'KVUE',
        'L', 'LAD', 'LAZ', 'LBRDA', 'LBTYA', 'LCID', 'LDOS', 'LEA', 'LEN', 'LH', 'LHX', 
        'LII', 'LIN', 'LINE', 'LKQ', 'LLY', 'LLYVA', 'LMT', 'LNC', 'LNG', 'LNT', 'LNW', 
        'LOAR', 'LOPE', 'LOW', 'LPX', 'LRCX', 'LSCC', 'LSTR', 'LULU', 'LUV', 'LVS', 'LW', 
        'LYB', 'LYFT', 'LYV',
        'MA', 'MAA', 'MAR', 'MAS', 'MASI', 'MAT', 'MCD', 'MCK', 'MCO', 'MCHP', 'MDT', 
        'MDU', 'MET', 'META', 'MGM', 'MHK', 'MIDD', 'MKC', 'MKTX', 'MLM', 'MMC', 'MMM', 
        'MNST', 'MO', 'MOH', 'MOS', 'MPC', 'MPWR', 'MRK', 'MRP', 'MRNA', 'MRVL', 'MS', 
        'MSA', 'MSCI', 'MSFT', 'MSI', 'MSM', 'MSTR', 'MTB', 'MTCH', 'MTD', 'MTG', 'MTN', 
        'MTDR', 'MU', 'MUSA',
        'NCLH', 'NCNO', 'NDAQ', 'NDSN', 'NEE', 'NEM', 'NET', 'NEU', 'NFLX', 'NFG', 'NI', 
        'NIQ', 'NKE', 'NNN', 'NOC', 'NOV', 'NOW', 'NRG', 'NSA', 'NSC', 'NTAP', 'NTRS', 
        'NU', 'NUE', 'NVDA', 'NVR', 'NVST', 'NWS', 'NXPI', 'NXST',
        'O', 'ODFL', 'OGE', 'OKE', 'OLED', 'OLLI', 'OLN', 'OMC', 'OMF', 'ON', 'ONTO', 
        'ORCL', 'ORLY', 'OSK', 'OTIS', 'OXY', 'OZK',
        'PANW', 'PATH', 'PAYX', 'PB', 'PCAR', 'PCG', 'PCTY', 'PEG', 'PEN', 'PEP', 'PFE', 
        'PFG', 'PG', 'PGR', 'PH', 'PHM', 'PKG', 'PLD', 'PLNT', 'PLTR', 'PM', 'PNC', 'PNFP', 
        'PNR', 'PNW', 'PODD', 'POOL', 'POST', 'PPG', 'PPL', 'PPC', 'PRI', 'PRMB', 'PRU', 
        'PSA', 'PSN', 'PSO', 'PSX', 'PTC', 'PWR', 'PVH', 'PYPL',
        'QCOM', 'QRVO',
        'R', 'RAL', 'RARE', 'RBC', 'RBLX', 'RDDT', 'REG', 'REGN', 'REYN', 'RF', 'RGEN', 
        'RH', 'RHI', 'RITM', 'RJF', 'RKT', 'RL', 'RLI', 'RMD', 'RNG', 'ROK', 'ROL', 
        'ROP', 'ROST', 'RRC', 'RRX', 'RSG', 'RTX', 'RVTY', 'RYN',
        'S', 'SAIA', 'SAM', 'SARO', 'SBAC', 'SBUX', 'SCCO', 'SCHW', 'SAIC', 'SITE', 'SEB', 
        'SEE', 'SFD', 'SFM', 'SHC', 'SHW', 'SIRI', 'SJM', 'SLB', 'SLM', 'SNA', 'SNDR', 
        'SNOW', 'SNPS', 'SO', 'SOFI', 'SOLV', 'SON', 'SPGI', 'SPG', 'SPR', 'SRE', 'SSNSD', 
        'SSB', 'ST', 'STAG', 'STLD', 'STT', 'STX', 'STZ', 'SWK', 'SW', 'SWKS', 'SYF', 
        'SYK', 'SYY',
        'T', 'TAP', 'TDC', 'TDG', 'TDY', 'TEAM', 'TECH', 'TEL', 'TER', 'TFC', 'TFX', 'TGT', 
        'THC', 'THG', 'THO', 'TIGO', 'TJX', 'TKO', 'TKR', 'TMO', 'TMUS', 'TNL', 'TPL', 
        'TPR', 'TRGP', 'TRMB', 'TROW', 'TRV', 'TREX', 'TSN', 'TSCO', 'TSLA', 'TT', 'TTC', 
        'TTD', 'TTEK', 'TTWO', 'TXN', 'TXT', 'TYL',
        'UBER', 'UDR', 'UGI', 'UHS', 'UI', 'UNH', 'UNP', 'UPS', 'URI', 'USB', 'UAL', 
        'UWMC',
        'V', 'VALE', 'VFC', 'VICI', 'VKTX', 'VLTO', 'VLO', 'VMC', 'VMI', 'VNO', 'VNT', 
        'VOYA', 'VRT', 'VRSK', 'VRSN', 'VRTX', 'VST', 'VTRS', 'VTR', 'VVV', 'VZ',
        'WAB', 'WAL', 'WAT', 'WBD', 'WDC', 'WEC', 'WELL', 'WEX', 'WFC', 'WH', 'WHR', 
        'WLK', 'WM', 'WMB', 'WMT', 'WRB', 'WSC', 'WSM', 'WST', 'WTM', 'WTFC', 'WTW', 
        'WU', 'WWD', 'WY', 'WYNN',
        'XEL', 'XOM', 'XYL', 'XYZ',
        'YETI', 'YUM',
        'ZBH', 'ZBRA', 'ZION', 'ZS', 'ZTS'
    ]
    
    unique_symbols = set(symbols)
    print(f"Total unique symbols: {len(unique_symbols)}")
    return unique_symbols

def get_current_market_data(api_key, russell_symbols):
    """Get current market data for Russell 1000 stocks from snapshot"""
    
    try:
        response = requests.get(
            "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers",
            params={'apikey': api_key},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == 'OK' and 'tickers' in data:
                tickers = data['tickers']
                
                russell_data = {}
                for item in tickers:
                    try:
                        symbol = item['ticker']
                        
                        if symbol in russell_symbols:
                            day_data = item.get('day', {})
                            
                            if day_data and day_data.get('c', 0) > 0:
                                russell_data[symbol] = {
                                    'current_price': float(day_data['c']),
                                    'current_high': float(day_data.get('h', day_data['c'])),
                                    'current_volume': int(day_data.get('v', 0))
                                }
                    except (KeyError, ValueError, TypeError):
                        continue
                
                return russell_data
        
        return {}
            
    except Exception as e:
        print(f"Error fetching current data: {str(e)}")
        return {}

def calculate_180_day_drawdowns_optimized(api_key, current_data, today):
    """Calculate 180-day drawdowns with optimized processing"""
    
    drawdown_results = []
    
    start_date = today - timedelta(days=250)  # Buffer for weekends/holidays
    end_date = today - timedelta(days=1)  # Yesterday
    
    print(f"Processing {len(current_data)} stocks for 180-day drawdowns ({start_date} to {end_date})")
    
    processed_count = 0
    success_count = 0
    total_stocks = len(current_data)
    
    for symbol, current_info in current_data.items():
        try:
            if processed_count % 50 == 0:
                progress = (processed_count / total_stocks) * 100
                print(f"Progress: {processed_count}/{total_stocks} ({progress:.1f}%) - {success_count} successful")
            
            response = requests.get(
                f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start_date.isoformat()}/{end_date.isoformat()}",
                params={
                    'adjusted': 'true',
                    'sort': 'asc',
                    'limit': 250,
                    'apikey': api_key
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'OK' and 'results' in data:
                    bars = data['results']
                    
                    if len(bars) >= 30:
                        result = calculate_stock_drawdown(symbol, bars, current_info, today)
                        if result:
                            drawdown_results.append(result)
                            success_count += 1
                            
                            if success_count <= 10:
                                print(f"{symbol}: {result['drawdown_pct']:.1f}% ({result['days_since_peak']} days)")
                            
            elif response.status_code == 429:
                print("Rate limited, waiting 60s...")
                time.sleep(60)
                continue
            
            processed_count += 1
            
            # Rate limiting
            if processed_count % 10 == 0:
                time.sleep(0.5)
            
        except Exception as e:
            if processed_count < 10:
                print(f"Error processing {symbol}: {str(e)}")
            processed_count += 1
            continue

    print(f"Calculated {len(drawdown_results)} drawdowns from {total_stocks} stocks")
    return drawdown_results

def calculate_stock_drawdown(symbol, historical_bars, current_info, date):
    """Calculate drawdown metrics for a single stock"""
    
    try:
        current_price = current_info['current_price']
        
        historical_highs = [float(bar['h']) for bar in historical_bars]
        historical_highs.append(current_info['current_high'])
        
        peak_price = max(historical_highs)
        peak_index = historical_highs.index(peak_price)
        days_since_peak = len(historical_highs) - 1 - peak_index
        
        drawdown_pct = ((current_price - peak_price) / peak_price) * 100
        
        return {
            'date': date.isoformat(),
            'symbol': symbol,
            'current_price': round(current_price, 2),
            'peak_price': round(peak_price, 2),
            'drawdown_pct': round(drawdown_pct, 2),
            'days_since_peak': days_since_peak,
            'volume': current_info['current_volume']
        }
        
    except Exception as e:
        return None

def rank_drawdown_results(drawdown_results, date):
    """Rank stocks by drawdown (worst first)"""
    sorted_results = sorted(drawdown_results, key=lambda x: x['drawdown_pct'])
    
    for rank, result in enumerate(sorted_results, 1):
        result['rank'] = rank
    
    return sorted_results

def collect_portfolio_data(headers, base_url, date):
    """Get portfolio data from Alpaca"""
    
    portfolio_data = []
    try:
        response = requests.get(f"{base_url}/v2/positions", headers=headers, timeout=10)
        
        if response.status_code == 200:
            positions = response.json()
            
            for position in positions:
                try:
                    entry_price = float(position['avg_entry_price'])
                    current_price = float(position['current_price']) if position['current_price'] else entry_price
                    unrealized_return_pct = ((current_price - entry_price) / entry_price) * 100
                    
                    portfolio_data.append({
                        'date': date.isoformat(),
                        'symbol': position['symbol'],
                        'quantity': float(position['qty']),
                        'avg_entry_price': round(entry_price, 2),
                        'current_price': round(current_price, 2),
                        'unrealized_return_pct': round(unrealized_return_pct, 2),
                        'market_value': round(float(position['market_value']), 2),
                        'unrealized_pl': round(float(position['unrealized_pl']), 2)
                    })
                except Exception:
                    continue

    except Exception as e:
        print(f"Portfolio error: {str(e)}")
    
    return portfolio_data

def append_to_csv(s3_client, bucket_name, filename, data):
    """Append data to S3 CSV"""
    try:
        try:
            obj = s3_client.get_object(Bucket=bucket_name, Key=filename)
            existing_df = pd.read_csv(obj['Body'])
        except s3_client.exceptions.NoSuchKey:
            existing_df = pd.DataFrame()
        
        new_df = pd.DataFrame(data)
        
        if not existing_df.empty:
            today_str = data[0]['date'] if data else ''
            existing_df = existing_df[existing_df['date'] != today_str]
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined_df = new_df
        
        csv_content = combined_df.to_csv(index=False)
        s3_client.put_object(Bucket=bucket_name, Key=filename, Body=csv_content, ContentType='text/csv')
        print(f"Saved {len(new_df)} rows to {filename}")
        
    except Exception as e:
        print(f"Error with {filename}: {str(e)}")
        raise

def save_to_csv(s3_client, bucket_name, filename, data):
    """Save data to S3 CSV"""
    try:
        df = pd.DataFrame(data)
        csv_content = df.to_csv(index=False)
        s3_client.put_object(Bucket=bucket_name, Key=filename, Body=csv_content, ContentType='text/csv')
        print(f"Saved {len(data)} rows to {filename}")
    except Exception as e:
        print(f"Error saving {filename}: {str(e)}")
        raise