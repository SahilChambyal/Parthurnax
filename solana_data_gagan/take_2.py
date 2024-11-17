import requests
import pandas as pd
import io
import zipfile
from datetime import datetime, timedelta
import concurrent.futures

def download_and_process_file(date_str):
    """
    Download and process a single day's trading data
    """
    base_url = "https://data.binance.vision/data/spot/daily/trades/SOLUSDT/"
    filename = f"SOLUSDT-trades-{date_str}.zip"
    url = base_url + filename

    try:
        # Download the file
        response = requests.get(url)
        response.raise_for_status()

        # Read the zip file
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # Read CSV from zip
            with z.open(z.namelist()[0]) as f:
                df = pd.read_csv(f, names=['trade_id', 'price', 'quantity', 'quote_quantity',
                                         'timestamp', 'is_buyer_maker', 'is_best_match'])

        print(f"Successfully processed {date_str}")
        return df

    except Exception as e:
        print(f"Error processing {date_str}: {str(e)}")
        return None

def get_all_trading_data(start_date, end_date):
    """
    Download and combine trading data for a date range
    """
    # Convert dates to datetime objects
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    # Generate list of dates
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)

    # Download and process files in parallel
    all_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(download_and_process_file, date): date
                  for date in dates}

        for future in concurrent.futures.as_completed(futures):
            df = future.result()
            if df is not None:
                all_data.append(df)

    # Combine all dataframes
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)

        # Convert timestamp to datetime
        combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'], unit='ms')

        # Sort by timestamp
        combined_df = combined_df.sort_values('timestamp')

        return combined_df
    else:
        return None

def analyze_trading_data(df):
    """
    Perform basic analysis on the trading data
    """
    if df is None or len(df) == 0:
        return "No data to analyze"

    analysis = {
        'total_trades': len(df),
        'start_time': df['timestamp'].min(),
        'end_time': df['timestamp'].max(),
        'average_price': df['price'].mean(),
        'min_price': df['price'].min(),
        'max_price': df['price'].max(),
        'total_volume': df['quantity'].sum(),
        'total_quote_volume': df['quote_quantity'].sum(),
        'buyer_maker_percentage': (df['is_buyer_maker'].mean() * 100)
    }

    return analysis

# Example usage
if __name__ == "__main__":
    # Example date range (adjust as needed)
    start_date = '2024-11-05'  # From your earliest date in the image
    end_date = '2024-11-12'    # To your latest date in the image

    print("Downloading and processing data...")
    df = get_all_trading_data(start_date, end_date)

    if df is not None:
        print("\nData downloaded successfully!")
        print(f"Total rows: {len(df)}")

        print("\nBasic Analysis:")
        analysis = analyze_trading_data(df)
        for key, value in analysis.items():
            print(f"{key}: {value}")

        # Save to file if needed
        df.to_csv('combined_SOLUSDT_trades.csv', index=False)
        print("\nData saved to 'combined_SOLUSDT_trades.csv'")
