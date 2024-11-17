import json
from websocket import create_connection
import pandas as pd
from datetime import datetime
import time

#the purpose of the file
#this file is to get the data from tradingview websocket
#and then parse the data to get the OHLC data
#this was edited by chat bot after i provided the initial code - results not reviewed


class TradingViewWebSocket:
    def __init__(self):
        self.socket = "wss://data.tradingview.com/socket.io/websocket"
        self.ws = None

    def connect(self):
        """Establish WebSocket connection"""
        self.ws = create_connection(self.socket)

    def create_message(self, func, args):
        """Create formatted message for TradingView WebSocket"""
        message = json.dumps({"m": func, "p": args})
        formatted = f"~m~{len(message)}~m~{message}"
        return formatted

    def send_message(self, func, args):
        """Send a message to the WebSocket"""
        message = self.create_message(func, args)
        self.ws.send(message)

    def parse_message(self, message):
        """Parse TradingView WebSocket message"""
        if "~m~" not in message:
            return None

        # Split the message into parts
        parts = message.split("~m~")
        # Filter out empty strings and length indicators
        data_parts = [p for p in parts if p and not p.isdigit()]

        if not data_parts:
            return None

        try:
            return json.loads(data_parts[0])
        except json.JSONDecodeError:
            return None

    def parse_ohlc_data(self, data):
        """Parse OHLC data from timescale_update message"""
        if not isinstance(data, dict) or 'p' not in data:
            return None

        try:
            candles = data['p'][1]['sds_1']['s']

            ohlc_data = []
            for candle in candles:
                if 'v' in candle:
                    timestamp, open_price, high, low, close = candle['v']
                    ohlc_data.append({
                        'timestamp': datetime.fromtimestamp(timestamp),
                        'open': open_price,
                        'high': high,
                        'low': low,
                        'close': close
                    })

            return pd.DataFrame(ohlc_data)
        except (KeyError, IndexError):
            return None

    def get_solana_data(self):
        """Get Solana price data"""
        # Initialize connection
        self.connect()

        # Send required messages
        self.send_message("chart_create_session", ["cs_PQsM0CA4qK0I", ""])
        self.send_message("resolve_symbol", [
            "cs_PQsM0CA4qK0I",
            "sds_sym_1",
            "={\"adjustment\":\"splits\",\"symbol\":\"CRYPTO:SOLUSD\"}"
        ])
        self.send_message("create_series", [
            "cs_PQsM0CA4qK0I",
            "sds_1",
            "s1",
            "sds_sym_1",
            "5",  # 5-minute interval
            10,# Number of candles i.e. data points
            ""
        ])

        while True:
            result = self.ws.recv()
            parsed_data = self.parse_message(result)

            if parsed_data and parsed_data.get('m') == 'timescale_update':
                df = self.parse_ohlc_data(parsed_data)
                if df is not None:
                    return df

            if parsed_data and parsed_data.get('m') == 'series_completed':
                break

        return None

# Usage example
if __name__ == "__main__":
    tv = TradingViewWebSocket()
    df = tv.get_solana_data()

    if df is not None:
        print("\nSOL/USD OHLC Data:")
        print(df)

        # Calculate some basic statistics
        print("\nBasic Statistics:")
        print(f"Average Price: ${df['close'].mean():.2f}")
        print(f"Highest Price: ${df['high'].max():.2f}")
        print(f"Lowest Price: ${df['low'].min():.2f}")
        print(f"Price Range: ${df['high'].max() - df['low'].min():.2f}")
