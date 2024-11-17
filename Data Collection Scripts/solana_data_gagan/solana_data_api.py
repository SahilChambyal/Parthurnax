import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import os
from typing import Optional

#the purpose of the file
#fetch historical data for Solana from CoinGecko API
#can only get limited free data
# need paid version to get more data - too expensive


def fetch_solana_historical_data(
    start_date: str = '2020-03-16',
    api_key: Optional[str] = None,
    save_progress: bool = True
) -> pd.DataFrame:
    """
    Fetches 1-minute historical data for Solana from a specified start date.

    Args:
        start_date (str): Start date in YYYY-MM-DD format. Defaults to Solana's launch date.
        api_key (str, optional): CoinGecko API key for higher rate limits
        save_progress (bool): Whether to save progress periodically

    Returns:
        pandas.DataFrame: Historical price data with timestamps
    """

    # CoinGecko API endpoint
    base_url = "https://api.coingecko.com/api/v3"

    # Initialize empty list to store all data
    all_data = []

    # Convert start_date to timestamp
    current_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.now()

    # Setup headers if API key is provided
    headers = {'X-Cg-Pro-Api-Key': api_key} if api_key else {}

    # Create progress file name
    progress_file = 'solana_progress.csv'

    # Load progress if exists
    if save_progress and os.path.exists(progress_file):
        progress_df = pd.read_csv(progress_file)
        progress_df['timestamp'] = pd.to_datetime(progress_df['timestamp'])
        all_data = progress_df.to_dict('records')
        if all_data:
            current_date = datetime.strptime(
                all_data[-1]['timestamp'].split()[0],
                '%Y-%m-%d'
            ) + timedelta(days=1)
            print(f"Resuming from {current_date.date()}")

    while current_date < end_date:
        from_timestamp = int(current_date.timestamp())
        to_timestamp = int((current_date + timedelta(days=1)).timestamp())

        url = f"{base_url}/coins/solana/market_chart/range"
        params = {
            'vs_currency': 'usd',
            'from': from_timestamp,
            'to': to_timestamp
        }

        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

            day_data = []
            for timestamp_ms, price in data['prices']:
                day_data.append({
                    'timestamp': datetime.fromtimestamp(timestamp_ms/1000),
                    'price': price
                })

            all_data.extend(day_data)
            print(f"Collected data for {current_date.date()}")

            # Save progress periodically
            if save_progress and len(day_data) > 0:
                temp_df = pd.DataFrame(all_data)
                temp_df.to_csv(progress_file, index=False)

            current_date += timedelta(days=1)

            # Adjust sleep time based on API key
            if api_key:
                time.sleep(0.3)  # Pro API has higher rate limits
            else:
                time.sleep(1.5)  # Free tier needs longer delays

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {current_date.date()}: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)
            continue

    df = pd.DataFrame(all_data)
    df = df.sort_values('timestamp')
    df = df.drop_duplicates(subset='timestamp')

    return df

def save_to_csv(df: pd.DataFrame, filename: str = 'solana_historical_data.csv') -> None:
    """
    Saves the DataFrame to a CSV file.

    Args:
        df (pandas.DataFrame): DataFrame containing the historical data
        filename (str): Name of the output file
    """
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

    # Print summary statistics
    print("\nDataset Summary:")
    print(f"Date Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Total Records: {len(df)}")
    print("\nPrice Statistics:")
    print(df['price'].describe())

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Fetch Solana historical price data')
    parser.add_argument('--start-date', type=str, default='2020-03-16',
                      help='Start date in YYYY-MM-DD format')
    parser.add_argument('--api-key', type=str, help='CoinGecko API key (optional)')
    parser.add_argument('--output', type=str, default='solana_historical_data.csv',
                      help='Output filename')
    parser.add_argument('--no-progress', action='store_true',
                      help='Disable progress saving')

    args = parser.parse_args()

    print(f"Starting data collection from {args.start_date}")
    df = fetch_solana_historical_data(
        start_date=args.start_date,
        api_key=args.api_key,
        save_progress=not args.no_progress
    )
    save_to_csv(df, args.output)
