import json
import boto3
import pandas as pd
import os
import requests
from datetime import datetime
from io import StringIO


def lambda_handler(event, context):
    print("Russell 1000 Telegram bot webhook received")

    try:
        body = json.loads(event.get('body', '{}'))

        if 'message' not in body:
            print("No message in webhook body")
            return {'statusCode': 200}

        message = body['message']
        chat_id = message['chat']['id']
        text = message.get('text', '').strip()
        user_name = message.get('from', {}).get('first_name', 'User')

        print(f"Message from {user_name} (chat {chat_id}): {text}")

        ssm = boto3.client('ssm')
        s3 = boto3.client('s3')
        lambda_client = boto3.client('lambda')

        bot_token = ssm.get_parameter(
            Name='/screener/telegram/bot_token',
            WithDecryption=True
        )['Parameter']['Value']

        try:
            authorized_chat_id = ssm.get_parameter(
                Name='/screener/telegram/chat_id'
            )['Parameter']['Value']

            if str(chat_id) != str(authorized_chat_id):
                send_telegram_message(bot_token, chat_id, "🚫 Unauthorized access. Contact admin.")
                return {'statusCode': 200}
        except Exception:
            # Parameter not set — allow any user
            pass

        bucket_name = os.environ.get('S3_BUCKET_NAME')

        if text.startswith('/'):
            command = text.split()[0].lower()

            if command in ('/start', '/help'):
                response = get_help_message(user_name)
            elif command in ('/dashboard', '/daily'):
                response = get_daily_dashboard(s3, bucket_name)
            elif command == '/screen':
                response = get_screening_results(s3, bucket_name)
            elif command == '/portfolio':
                response = get_portfolio_summary(s3, bucket_name)
            elif command == '/monitor':
                response = check_profit_targets(s3, bucket_name)
            elif command == '/account':
                response = get_account_summary()
            elif command == '/trigger':
                response = trigger_data_collection(lambda_client)
            elif command == '/stats':
                response = get_system_stats(s3, bucket_name)
            elif command == '/download':
                response = get_download_links(s3, bucket_name)
            else:
                response = f"❓ Unknown command '{command}'. Type /help for available commands."
        else:
            response = "Please use commands starting with /. Type /help for available commands."

        send_telegram_message(bot_token, chat_id, response)

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Success'})
        }

    except Exception as e:
        import traceback
        print(f"Error in Telegram bot: {str(e)}")
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def get_daily_dashboard(s3_client, bucket_name):
    try:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
        dashboard = f"📊 **DAILY DASHBOARD** ({current_time})\n"
        dashboard += "=" * 40 + "\n\n"

        account_info = get_account_summary_data()
        if account_info:
            dashboard += "💰 **ACCOUNT STATUS**\n"
            dashboard += f"*Equity:* ${account_info['equity']:,.2f}\n"
            dashboard += f"*Cash:* ${account_info['cash']:,.2f}\n"
            dashboard += f"*Buying Power:* ${account_info['buying_power']:,.2f}\n"
            dashboard += f"*Status:* {account_info['status']}\n\n"
        else:
            dashboard += "💰 **ACCOUNT STATUS**\n❌ Unable to fetch account data\n\n"

        portfolio_summary = get_portfolio_summary_data(s3_client, bucket_name)
        if portfolio_summary and not portfolio_summary['positions'].empty:
            dashboard += "💼 **PORTFOLIO OVERVIEW**\n"
            dashboard += f"*Positions:* {portfolio_summary['position_count']}\n"
            dashboard += f"*Total Value:* ${portfolio_summary['total_value']:,.2f}\n"
            dashboard += f"*Unrealized P&L:* ${portfolio_summary['total_unrealized']:+,.2f}\n"
            dashboard += f"*Avg Return:* {portfolio_summary['avg_return']:+.1f}%\n\n"

            sorted_positions = portfolio_summary['positions'].sort_values('unrealized_return_pct', ascending=False)
            top_5 = sorted_positions.head(5)

            dashboard += "🏆 **TOP 5 BEST POSITIONS**\n"
            for _, pos in top_5.iterrows():
                emoji = "🟢" if pos['unrealized_return_pct'] > 0 else "🔴"
                dashboard += f"{emoji} *{pos['symbol']}*: {pos['unrealized_return_pct']:+.1f}% (${pos['market_value']:,.0f})\n"
            dashboard += "\n"

            if len(sorted_positions) >= 5:
                top_5_avg = top_5['unrealized_return_pct'].mean()
                dashboard += "🎯 **PROFIT TARGET STATUS**\n"
                dashboard += f"*Top 5 Avg Return:* {top_5_avg:.1f}%\n"
                dashboard += "*Target:* 100.0%\n"
                if top_5_avg >= 100.0:
                    dashboard += "🚨 **TAKE PROFIT SIGNAL!** 🚨\n"
                    dashboard += f"*Profit to realize:* ${top_5['unrealized_pl'].sum():+,.0f}\n\n"
                else:
                    dashboard += f"⏳ *Need {100.0 - top_5_avg:.1f}% more*\n\n"
            else:
                dashboard += "🎯 **PROFIT TARGET STATUS**\n*Need 5+ positions for target analysis*\n\n"

            dashboard += "📋 **ALL POSITIONS** (sorted best to worst)\n"
            for _, pos in sorted_positions.iterrows():
                emoji = "🟢" if pos['unrealized_return_pct'] > 0 else "🔴"
                dashboard += (
                    f"{emoji} *{pos['symbol']}*: {pos['unrealized_return_pct']:+.1f}% "
                    f"(${pos['avg_entry_price']:.2f}→${pos['current_price']:.2f}) ${pos['unrealized_pl']:+.0f}\n"
                )
            dashboard += "\n"

        else:
            dashboard += "💼 **PORTFOLIO OVERVIEW**\n*No current positions*\n\n"

        screening_data = get_screening_results_data(s3_client, bucket_name)
        if screening_data is not None and not screening_data.empty:
            latest_date = screening_data['date'].max()
            latest_candidates = screening_data[screening_data['date'] == latest_date].head(10)

            dashboard += f"📉 **TOP 10 BUY CANDIDATES** ({latest_date})\n"
            dashboard += "*Worst Russell 1000 drawdowns:*\n"

            for _, row in latest_candidates.iterrows():
                rank = int(row.get('rank', 0)) if row.get('rank', 0) else "•"
                current = row.get('current_price', 0)
                peak = row.get('peak_price', 0)
                days = int(row.get('days_since_peak', 0))
                dashboard += f"*{rank}. {row['symbol']}*: {row['drawdown_pct']:.1f}%"
                if current > 0 and peak > 0:
                    dashboard += f" (${peak:.2f}→${current:.2f}, {days}d)\n"
                else:
                    dashboard += f" ({days} days from peak)\n"
        else:
            dashboard += "📉 **TOP 10 BUY CANDIDATES**\n*No screening data available*\n"

        dashboard += "\n💡 *Use individual commands (/portfolio, /screen, etc.) for more details*"
        return dashboard

    except Exception as e:
        return f"❌ Error generating dashboard: {str(e)}"


def get_account_summary_data():
    try:
        ssm = boto3.client('ssm')

        api_key = ssm.get_parameter(Name='/screener/alpaca/api_key', WithDecryption=True)['Parameter']['Value']
        secret_key = ssm.get_parameter(Name='/screener/alpaca/secret_key', WithDecryption=True)['Parameter']['Value']
        base_url = ssm.get_parameter(Name='/screener/alpaca/base_url')['Parameter']['Value']

        headers = {
            'APCA-API-KEY-ID': api_key,
            'APCA-API-SECRET-KEY': secret_key
        }

        response = requests.get(f"{base_url}/v2/account", headers=headers, timeout=10)

        if response.status_code == 200:
            account = response.json()
            return {
                'equity': float(account['equity']),
                'cash': float(account['cash']),
                'buying_power': float(account['buying_power']),
                'status': account['status']
            }
        return None
    except Exception:
        return None


def get_portfolio_summary_data(s3_client, bucket_name):
    try:
        obj = s3_client.get_object(Bucket=bucket_name, Key='portfolio_snapshots.csv')
        portfolio_df = pd.read_csv(obj['Body'])

        if portfolio_df.empty:
            return None

        latest_date = portfolio_df['date'].max()
        current_positions = portfolio_df[portfolio_df['date'] == latest_date]

        if current_positions.empty:
            return None

        return {
            'positions': current_positions,
            'total_value': current_positions['market_value'].sum(),
            'total_unrealized': current_positions['unrealized_pl'].sum(),
            'position_count': len(current_positions),
            'avg_return': current_positions['unrealized_return_pct'].mean()
        }
    except Exception as e:
        print(f"Portfolio summary error: {e}")
        return None


def get_screening_results_data(s3_client, bucket_name):
    try:
        obj = s3_client.get_object(Bucket=bucket_name, Key='daily_top_candidates.csv')
        return pd.read_csv(obj['Body'])
    except Exception:
        pass

    try:
        obj = s3_client.get_object(Bucket=bucket_name, Key='russell_1000_drawdown_results.csv')
        full_df = pd.read_csv(obj['Body'])
        latest_date = full_df['date'].max()
        candidates_df = full_df[full_df['date'] == latest_date].head(10).copy()
        candidates_df['rank'] = range(1, len(candidates_df) + 1)
        return candidates_df
    except Exception as e:
        print(f"Screening data error: {e}")
        return pd.DataFrame()


def get_help_message(user_name):
    return f"""🤖 **Hi {user_name}! Russell 1000 Screener Bot**

📊 **Available Commands:**

*🎯 Quick Access:*
/dashboard - Complete daily overview (account + portfolio + top stocks)
/daily - Same as /dashboard

*📈 Market Analysis:*
/screen - Top 10 worst drawdown stocks (buy candidates)
/stats - System performance & data statistics

*💼 Portfolio Management:*
/portfolio - Your current positions
/monitor - Check profit-taking opportunities (100% target)
/account - Alpaca account summary

*⚙️ System Control:*
/trigger - Manually run data collection
/download - Get CSV download links

*ℹ️ Info:*
/help - Show this menu

**📋 Strategy:** Contrarian value investing - buy Russell 1000 stocks with worst 180-day drawdowns, sell when top 5 average ≥100% gains.

**⏰ Data:** Updated daily at 6 AM ET using Polygon.io feed.
**💰 Trading:** Alpaca Markets integration for portfolio tracking.

*Happy investing! 📈✨*"""


def get_screening_results(s3_client, bucket_name):
    try:
        candidates_df = get_screening_results_data(s3_client, bucket_name)

        if candidates_df is None or candidates_df.empty:
            return "📊 No screening data available yet. Try /trigger to collect data or check back after 6 AM ET."

        latest_date = candidates_df['date'].max()
        latest_candidates = candidates_df[candidates_df['date'] == latest_date]

        if latest_candidates.empty:
            return "📊 No candidates found for latest date."

        message = f"📉 **TOP 10 WORST DRAWDOWNS** ({latest_date})\n\n"
        message += "_Contrarian value opportunities from Russell 1000:_\n\n"

        for _, row in latest_candidates.head(10).iterrows():
            rank = int(row.get('rank', 0))
            symbol = row['symbol']
            drawdown = row['drawdown_pct']
            current = row.get('current_price', 0)
            peak = row.get('peak_price', 0)
            days = int(row.get('days_since_peak', 0))

            message += f"*{rank}. {symbol}*: {drawdown:.1f}%\n"
            if current > 0 and peak > 0:
                message += f"   ${peak:.2f} → ${current:.2f} ({days} days ago)\n\n"
            else:
                message += f"   {drawdown:.1f}% from peak ({days} days ago)\n\n"

        message += "_💡 These are the most beaten-down Russell 1000 stocks - potential contrarian plays._"
        return message

    except Exception as e:
        return f"❌ Error getting screening results: {str(e)}"


def get_portfolio_summary(s3_client, bucket_name):
    try:
        summary = get_portfolio_summary_data(s3_client, bucket_name)

        if not summary or summary['positions'].empty:
            return "💼 **PORTFOLIO SUMMARY**\n\nNo current positions."

        positions = summary['positions']
        latest_date = positions['date'].max()

        message = f"💼 **PORTFOLIO SUMMARY** ({latest_date})\n\n"
        message += f"*Positions:* {summary['position_count']}\n"
        message += f"*Total Value:* ${summary['total_value']:,.2f}\n"
        message += f"*Unrealized P&L:* ${summary['total_unrealized']:+,.2f}\n"
        message += f"*Average Return:* {summary['avg_return']:+.1f}%\n\n"
        message += "*Current Positions:*\n"

        for _, pos in positions.sort_values('unrealized_return_pct', ascending=False).iterrows():
            emoji = "🟢" if pos['unrealized_return_pct'] > 0 else "🔴"
            message += f"{emoji} *{pos['symbol']}*: {pos['unrealized_return_pct']:+.1f}% (${pos['market_value']:,.0f}, ${pos['unrealized_pl']:+.0f})\n"

        return message

    except Exception as e:
        return f"❌ Error getting portfolio summary: {str(e)}"


def check_profit_targets(s3_client, bucket_name):
    try:
        obj = s3_client.get_object(Bucket=bucket_name, Key='portfolio_snapshots.csv')
        portfolio_df = pd.read_csv(obj['Body'])

        if portfolio_df.empty:
            return "🎯 **PROFIT TARGET CHECK**\n\nNo portfolio data available."

        latest_date = portfolio_df['date'].max()
        current_positions = portfolio_df[portfolio_df['date'] == latest_date]

        if len(current_positions) == 0:
            return "🎯 **PROFIT TARGET CHECK**\n\nNo current positions to monitor."

        if len(current_positions) < 5:
            avg_return = current_positions['unrealized_return_pct'].mean()
            message = f"🎯 **PROFIT TARGET CHECK** ({latest_date})\n\n"
            message += f"*Current Positions:* {len(current_positions)} (need 5+ for top-5 analysis)\n"
            message += f"*Average Return:* {avg_return:.1f}%\n\n"
            message += "📊 *All Positions:*\n"
            for _, pos in current_positions.sort_values('unrealized_return_pct', ascending=False).iterrows():
                emoji = "🟢" if pos['unrealized_return_pct'] > 0 else "🔴"
                message += f"{emoji} *{pos['symbol']}*: {pos['unrealized_return_pct']:+.1f}%\n"
            return message

        sorted_positions = current_positions.sort_values('unrealized_return_pct', ascending=False)
        top_5 = sorted_positions.head(5)
        avg_return = top_5['unrealized_return_pct'].mean()

        message = f"🎯 **PROFIT TARGET CHECK** ({latest_date})\n\n"
        message += f"*Top 5 Average Return:* {avg_return:.1f}%\n"
        message += "*Target:* 100.0%\n\n"

        if avg_return >= 100.0:
            message += "🚨 **TAKE PROFIT SIGNAL!** 🚨\n\n"
            message += "*🎊 Exit these winners:*\n"
            for _, pos in top_5.iterrows():
                message += f"• *{pos['symbol']}*: {pos['unrealized_return_pct']:.1f}% (${pos['market_value']:,.0f})\n"
            message += f"\n💰 *Total profit to realize:* ${top_5['unrealized_pl'].sum():+,.0f}"
        else:
            message += f"⏳ Hold positions. Need {100.0 - avg_return:.1f}% more on average.\n\n"
            message += "📊 *Current Top 5:*\n"
            for _, pos in top_5.iterrows():
                emoji = "🟢" if pos['unrealized_return_pct'] > 0 else "🔴"
                message += f"{emoji} *{pos['symbol']}*: {pos['unrealized_return_pct']:+.1f}%\n"

        return message

    except Exception as e:
        return f"❌ Error checking profit targets: {str(e)}"


def get_account_summary():
    try:
        ssm = boto3.client('ssm')

        api_key = ssm.get_parameter(Name='/screener/alpaca/api_key', WithDecryption=True)['Parameter']['Value']
        secret_key = ssm.get_parameter(Name='/screener/alpaca/secret_key', WithDecryption=True)['Parameter']['Value']
        base_url = ssm.get_parameter(Name='/screener/alpaca/base_url')['Parameter']['Value']

        headers = {
            'APCA-API-KEY-ID': api_key,
            'APCA-API-SECRET-KEY': secret_key
        }

        response = requests.get(f"{base_url}/v2/account", headers=headers, timeout=10)

        if response.status_code == 200:
            account = response.json()

            message = f"💰 **ALPACA ACCOUNT** ({account['status']})\n\n"
            message += f"*Total Equity:* ${float(account['equity']):,.2f}\n"
            message += f"*Cash:* ${float(account['cash']):,.2f}\n"
            message += f"*Buying Power:* ${float(account['buying_power']):,.2f}\n"

            if account.get('pattern_day_trader'):
                message += "*Day Trading:* Pattern Day Trader\n"
            if account.get('daytrade_count', 0) > 0:
                message += f"*Day Trades Used:* {account['daytrade_count']}/3\n"

            return message
        else:
            return f"❌ Alpaca API error: {response.status_code}"

    except Exception as e:
        return f"❌ Error getting account summary: {str(e)}"


def trigger_data_collection(lambda_client):
    try:
        function_name = None

        functions = lambda_client.list_functions()['Functions']
        for func in functions:
            name = func['FunctionName']
            if 'DataCollector' in name or 'daily_collector' in name.lower():
                function_name = name
                break

        if not function_name:
            return "❌ Could not find data collection function. Check function naming."

        print(f"Triggering function: {function_name}")

        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='Event',
            Payload=json.dumps({})
        )

        if response['StatusCode'] == 202:
            return f"✅ **DATA COLLECTION TRIGGERED**\n\nFunction `{function_name}` started.\n\nCheck back in 2-3 minutes for updated data. 📊"
        else:
            return f"❌ Error triggering collection: Status {response['StatusCode']}"

    except Exception as e:
        return f"❌ Error triggering data collection: {str(e)}"


def get_system_stats(s3_client, bucket_name):
    try:
        message = f"📊 **SYSTEM STATISTICS** ({datetime.now().strftime('%Y-%m-%d %H:%M')} UTC)\n\n"

        files_to_check = [
            'russell_1000_drawdown_results.csv',
            'daily_top_candidates.csv',
            'portfolio_snapshots.csv'
        ]

        for file in files_to_check:
            try:
                obj = s3_client.get_object(Bucket=bucket_name, Key=file)
                df = pd.read_csv(obj['Body'])

                if not df.empty:
                    latest_date = df['date'].max() if 'date' in df.columns else 'Unknown'
                    message += f"✅ *{file.replace('.csv', '').replace('_', ' ').title()}*\n"
                    message += f"   📅 Latest: {latest_date}\n"
                    message += f"   📝 Records: {len(df):,}\n\n"
                else:
                    message += f"⚠️ *{file}*: Empty file\n\n"

            except s3_client.exceptions.NoSuchKey:
                message += f"❌ *{file}*: Not found\n\n"
            except Exception as e:
                message += f"❌ *{file}*: Error ({str(e)[:30]}...)\n\n"

        message += "*🔧 System Health:*\n"
        message += f"📦 S3 Bucket: `{bucket_name}`\n"
        message += f"⚡ Last Check: {datetime.now().strftime('%H:%M:%S')} UTC\n"

        return message

    except Exception as e:
        return f"❌ Error getting system stats: {str(e)}"


def get_download_links(s3_client, bucket_name):
    try:
        csv_files = [
            'russell_1000_drawdown_results.csv',
            'daily_top_candidates.csv',
            'portfolio_snapshots.csv'
        ]

        message = "📥 **CSV DOWNLOAD LINKS** (Valid for 1 hour)\n\n"

        for file in csv_files:
            try:
                s3_client.head_object(Bucket=bucket_name, Key=file)

                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': file},
                    ExpiresIn=3600
                )

                file_name = file.replace('.csv', '').replace('_', ' ').title()
                message += f"📄 [{file_name}]({url})\n"

            except s3_client.exceptions.NoSuchKey:
                file_name = file.replace('.csv', '').replace('_', ' ').title()
                message += f"❌ {file_name}: Not available\n"
            except Exception:
                message += f"❌ {file}: Error generating link\n"

        message += "\n💡 Right-click links → 'Save Link As' to download CSV files."
        return message

    except Exception as e:
        return f"❌ Error generating download links: {str(e)}"


def send_telegram_message(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    max_length = 4000

    if len(message) <= max_length:
        messages = [message]
    else:
        parts = message.split('\n\n')
        messages = []
        current = ""

        for part in parts:
            if len(current) + len(part) + 2 <= max_length:
                current += part + "\n\n"
            else:
                if current:
                    messages.append(current.strip())
                current = part + "\n\n"

        if current:
            messages.append(current.strip())

    for msg in messages:
        payload = {
            'chat_id': chat_id,
            'text': msg,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }

        try:
            response = requests.post(url, data=payload, timeout=10)
            if response.status_code == 200:
                print(f"Message sent to chat {chat_id}")
            else:
                print(f"Error sending message: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Exception sending Telegram message: {str(e)}")
