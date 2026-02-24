#!/usr/bin/env python3
"""
IBKR Daily Positions Script
Fetches open positions from Interactive Brokers using Flex Web Service
Posts to Discord
"""

import os
import sys
import requests
import csv
import io
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

IBKR_FLEX_TOKEN = os.getenv('IBKR_FLEX_TOKEN', '')
IBKR_QUERY_ID = os.getenv('IBKR_QUERY_ID', '')
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK', '')
OPENCLAW_SESSION = os.getenv('OPENCLAW_SESSION', 'main')

FLEX_BASE_URL = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService"


def get_positions():
    request_url = f"{FLEX_BASE_URL}/SendRequest"
    params = {'t': IBKR_FLEX_TOKEN, 'q': IBKR_QUERY_ID, 'v': 3}
    response = requests.get(request_url, params=params, timeout=30)
    
    if response.status_code != 200:
        return None
    
    response_text = response.text
    
    if '<ReferenceCode>' in response_text:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response_text)
        ref_code_elem = root.find('.//ReferenceCode')
        
        if ref_code_elem is None or not ref_code_elem.text:
            return None
        
        reference_code = ref_code_elem.text
        statement_url = f"{FLEX_BASE_URL}/GetStatement"
        params = {'t': IBKR_FLEX_TOKEN, 'q': reference_code, 'v': 3}
        response = requests.get(statement_url, params=params, timeout=30)
        
        if response.status_code != 200:
            return None
        
        return parse_csv(response.text)
    
    return parse_csv(response_text)


def parse_csv(csv_string):
    try:
        reader = csv.DictReader(io.StringIO(csv_string))
        positions = []
        
        for row in reader:
            if row.get('Symbol') in [None, ''] or row.get('Symbol') == 'Symbol':
                continue
            
            symbol = row.get('Symbol', '')
            if not symbol:
                continue
            
            try:
                quantity = float(row.get('Quantity', 0))
                if quantity == 0:
                    continue
            except:
                quantity = 0
            
            try:
                position_value = float(row.get('PositionValue', 0))
            except:
                position_value = 0
            
            try:
                pnl = float(row.get('FifoPnlUnrealized', 0))
            except:
                pnl = 0
            
            positions.append({
                'symbol': symbol,
                'description': row.get('Description', ''),
                'quantity': quantity,
                'position_value': position_value,
                'pnl': pnl,
            })
        
        return positions
        
    except Exception as e:
        print(f"Error parsing CSV: {e}")
        return []


def format_message(positions):
    message = "📊 **IBKR Daily Positions Update**\n"
    message += f"_{datetime.now().strftime('%Y-%m-%d %H:%M %Z')}_\n\n"
    
    if not positions:
        message += "No open positions found."
        return message
    
    total_value = sum(p.get('position_value', 0) for p in positions)
    total_pnl = sum(p.get('pnl', 0) for p in positions)
    
    message += f"**Total Position Value:** ${total_value:,.2f}\n"
    emoji = "🟢" if total_pnl >= 0 else "🔴"
    message += f"{emoji} **Total Unrealized P&L:** ${total_pnl:,.2f}\n\n"
    
    message += "**Open Positions:**\n"
    
    positions.sort(key=lambda x: x.get('position_value', 0), reverse=True)
    
    for pos in positions:
        symbol = pos.get('symbol', 'Unknown')
        description = pos.get('description', '')
        quantity = pos.get('quantity', 0)
        position_value = pos.get('position_value', 0)
        pnl = pos.get('pnl', 0)
        
        emoji = "🟢" if pnl >= 0 else "🔴"
        
        message += f"\n{emoji} **{symbol}**\n"
        if description:
            message += f"   {description}\n"
        message += f"   Shares: {quantity} | Value: ${position_value:,.2f} | P&L: ${pnl:,.2f}\n"
        
        # Add ticker mention for research trigger
        message += f"   🔍 Research: @{symbol}\n"
    
    message += "\n\n_Replying with @ticker will research that stock_"
    
    return message


def send_discord(message):
    if not DISCORD_WEBHOOK:
        print("No Discord webhook configured")
        return
    
    payload = {"content": message}
    resp = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
    if resp.status_code == 204:
        print("Sent to Discord successfully")
    else:
        print(f"Failed: {resp.status_code}")


def trigger_openclaw(positions):
    """Trigger OpenClaw agent to research positions"""
    if not positions:
        return
    
    # Get top 5 tickers by value
    top_tickers = sorted(positions, key=lambda x: x.get('position_value', 0), reverse=True)[:5]
    tickers = [p['symbol'] for p in top_tickers]
    
    # Send to OpenClaw session
    gateway_url = os.getenv('OPENCLAW_GATEWAY_URL', 'http://127.0.0.1:18789')
    gateway_token = os.getenv('OPENCLAW_GATEWAY_TOKEN', '')
    
    if not gateway_token:
        print("No OpenClaw gateway token configured")
        return
    
    # Format tickers for research request
    ticker_list = ", ".join(tickers)
    research_request = f"Research these stocks for latest news: {ticker_list}. Post findings to #portfolio."
    
    try:
        resp = requests.post(
            f"{gateway_url}/api/sessions/{OPENCLAW_SESSION}/messages",
            headers={"Authorization": f"Bearer {gateway_token}"},
            json={"content": research_request},
            timeout=10
        )
        if resp.status_code in [200, 201, 202]:
            print(f"Triggered OpenClaw agent for: {ticker_list}")
        else:
            print(f"OpenClaw trigger failed: {resp.status_code}")
    except Exception as e:
        print(f"OpenClaw trigger error: {e}")


def main():
    print("IBKR Daily Positions")
    print("=" * 40)
    
    if not IBKR_FLEX_TOKEN or not IBKR_QUERY_ID:
        print("ERROR: Missing credentials")
        sys.exit(1)
    
    print("Fetching positions...")
    positions = get_positions()
    
    if positions is None:
        print("Failed to get positions")
        send_discord("⚠️ Failed to fetch IBKR positions")
        return
    
    print(f"Found {len(positions)} positions")
    
    # Trigger OpenClaw research
    trigger_openclaw(positions)
    
    message = format_message(positions)
    send_discord(message)
    print("Done!")


if __name__ == "__main__":
    main()
