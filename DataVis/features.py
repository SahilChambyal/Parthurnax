import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import talib

# Explanation of the functions
# create_target_labels: Create target labels for ML model based on future price movements
# create_features: Create features for ML model
# prepare_ml_data: Prepare data for machine learning model
# This file just contains the functions that are used in the main file


def create_target_labels(df, profit_threshold=0.003, lookforward_window=30):
    """
    Create target labels based on maximum future profitability within the lookforward window.
    Prioritizes higher profitability over spacing between trades.
    Handles buy and sell signals separately.

    Parameters:
    df: DataFrame with OHLCV data
    profit_threshold: Minimum price movement to consider for a trade (default 0.3%)
    lookforward_window: How far to look ahead for price movement

    Returns:
    Updated DataFrame with 'target' column.
    """
    df = df.copy()

    # Ensure Close prices are float
    df['Close'] = df['Close'].astype(float)

    # Calculate future returns within the lookforward window
    future_returns = []
    for i in range(1, lookforward_window + 1):
        future_return = df['Close'].shift(-i) / df['Close'] - 1
        future_returns.append(future_return)

    # Combine future returns into a DataFrame for easier processing
    future_returns_df = pd.concat(future_returns, axis=1)
    future_returns_df.columns = [f'return_{i}' for i in range(1, lookforward_window + 1)]

    # Calculate maximum and minimum returns
    df['max_return'] = future_returns_df.max(axis=1)
    df['min_return'] = future_returns_df.min(axis=1)

    # Initialize target column with zeros
    df['target'] = 0

    # Assign buy (1) signals based on maximum return
    df.loc[df['max_return'] > profit_threshold, 'target'] = 1

    # Assign sell (-1) signals based on minimum return
    df.loc[df['min_return'] < -profit_threshold, 'target'] = -1

    # Resolve conflicts for buy signals
    last_buy_signal_idx = None
    for i in range(len(df)):
        if df['target'].iloc[i] == 1:
            # Check for overlapping buy signals
            if last_buy_signal_idx is not None and i - last_buy_signal_idx < lookforward_window:
                # Compare current buy signal with last buy signal
                if df['max_return'].iloc[i] > df['max_return'].iloc[last_buy_signal_idx]:
                    # Current buy signal is better, remove previous
                    df.iloc[last_buy_signal_idx, df.columns.get_loc('target')] = 0
                    last_buy_signal_idx = i
                else:
                    # Previous buy signal is better, remove current
                    df.iloc[i, df.columns.get_loc('target')] = 0
            else:
                last_buy_signal_idx = i

    # Resolve conflicts for sell signals
    last_sell_signal_idx = None
    for i in range(len(df)):
        if df['target'].iloc[i] == -1:
            # Check for overlapping sell signals
            if last_sell_signal_idx is not None and i - last_sell_signal_idx < lookforward_window:
                # Compare current sell signal with last sell signal
                if df['min_return'].iloc[i] < df['min_return'].iloc[last_sell_signal_idx]:
                    # Current sell signal is better (more negative min_return), remove previous
                    df.iloc[last_sell_signal_idx, df.columns.get_loc('target')] = 0
                    last_sell_signal_idx = i
                else:
                    # Previous sell signal is better, remove current
                    df.iloc[i, df.columns.get_loc('target')] = 0
            else:
                last_sell_signal_idx = i

    return df



def create_features(df, windows=[5, 15, 30, 60]):
    """
    Create features for ML model

    Parameters:
    df: DataFrame with OHLCV data
    windows: List of lookback windows for different features
    """
    df = df.copy()

    # Ensure numeric types
    price_cols = ['Open', 'High', 'Low', 'Close']
    df[price_cols + ['Volume']] = df[price_cols + ['Volume']].astype(float)

    features = []

    # 1. Price-based features
    for window in windows:
        # Moving averages
        df[f'sma_{window}'] = df['Close'].rolling(window=window).mean()
        df[f'ema_{window}'] = df['Close'].ewm(span=window).mean()

        # Price relative to moving averages
        df[f'close_to_sma_{window}'] = df['Close'] / df[f'sma_{window}']

        # Volatility
        df[f'volatility_{window}'] = df['Close'].rolling(window=window).std()

        # Price momentum
        df[f'momentum_{window}'] = df['Close'] / df['Close'].shift(window)

        features.extend([f'sma_{window}', f'ema_{window}', f'close_to_sma_{window}',
                        f'volatility_{window}', f'momentum_{window}'])

    # 2. Technical indicators
    # RSI
    df['rsi'] = talib.RSI(df['Close'].values, timeperiod=14)

    # MACD
    df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(
        df['Close'].values, fastperiod=12, slowperiod=26, signalperiod=9)

    # Bollinger Bands
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
        df['Close'].values, timeperiod=20)
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']

    # Average True Range
    df['atr'] = talib.ATR(df['High'].values, df['Low'].values,
                         df['Close'].values, timeperiod=14)

    features.extend(['rsi', 'macd', 'macd_signal', 'macd_hist',
                    'bb_width', 'atr'])

    # 3. Volume-based features
    for window in windows:
        df[f'volume_sma_{window}'] = df['Volume'].rolling(window=window).mean()
        df[f'volume_ratio_{window}'] = df['Volume'] / df[f'volume_sma_{window}']

        features.extend([f'volume_sma_{window}', f'volume_ratio_{window}'])

    # 4. Price pattern features
    df['high_low_ratio'] = df['High'] / df['Low']
    df['close_position'] = (df['Close'] - df['Low']) / (df['High'] - df['Low'])

    features.extend(['high_low_ratio', 'close_position'])

    # 5. Time-based features (assuming OpenTime is datetime)
    df['hour'] = pd.to_datetime(df['OpenTime']).dt.hour
    df['minute'] = pd.to_datetime(df['OpenTime']).dt.minute

    # Convert hour and minute to cyclic features
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    df['minute_sin'] = np.sin(2 * np.pi * df['minute'] / 60)
    df['minute_cos'] = np.cos(2 * np.pi * df['minute'] / 60)

    features.extend(['hour_sin', 'hour_cos', 'minute_sin', 'minute_cos'])

    # Drop rows with NaN values
    df = df.dropna()

    return df, features

# Function to prepare data for ML
def prepare_ml_data(df, lookforward_window=30, profit_threshold=0.003):
    """
    Prepare data for machine learning model
    """
    # Create target labels
    df = create_target_labels(df, profit_threshold, lookforward_window)

    # Create features
    df, feature_columns = create_features(df)

    # Normalize features
    scaler = MinMaxScaler()
    df[feature_columns] = scaler.fit_transform(df[feature_columns])

    # Prepare final datasets
    X = df[feature_columns]
    y = df['target']

    return X, y, feature_columns, scaler
