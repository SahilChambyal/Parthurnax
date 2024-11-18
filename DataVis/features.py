import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import talib

def create_target_labels(df, profit_threshold=0.003, lookforward_window=30, min_trades_per_day=10):
    """
    Create target labels for ML model based on future price movements
    1 for buy signals, -1 for sell signals, 0 for hold

    Parameters:
    df: DataFrame with OHLCV data
    profit_threshold: Minimum price movement to consider for a trade (0.3% default)
    lookforward_window: How far to look ahead for price movement
    min_trades_per_day: Target minimum number of trades per day
    """
    df = df.copy()

    # Convert price columns to float if they aren't already
    df['Close'] = df['Close'].astype(float)

    # Calculate future returns for different time windows
    future_returns = []
    for window in [5, 15, 30]:  # Multiple windows for robustness
        future_return = df['Close'].shift(-window) / df['Close'] - 1
        future_returns.append(future_return)

    # Combine future returns (average them)
    df['future_return'] = sum(future_returns) / len(future_returns)

    # Initialize labels
    df['target'] = 0

    # Calculate price volatility
    df['volatility'] = df['Close'].rolling(window=lookforward_window).std()

    # Adjust profit threshold based on local volatility
    dynamic_threshold = profit_threshold * (df['volatility'] / df['volatility'].mean())

    # Generate basic signals based on future returns
    df.loc[df['future_return'] > dynamic_threshold, 'target'] = 1  # Buy signal
    df.loc[df['future_return'] < -dynamic_threshold, 'target'] = -1  # Sell signal

    # Ensure minimum spacing between trades
    min_spacing = int(24 * 60 / min_trades_per_day)  # Assuming 1-minute data

    last_signal_idx = 0
    for i in range(len(df)):
        if df.iloc[i]['target'] != 0:
            if i - last_signal_idx < min_spacing:
                df.iloc[i, df.columns.get_loc('target')] = 0
            else:
                last_signal_idx = i

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
def prepare_ml_data(df, lookforward_window=30, profit_threshold=0.003, min_trades_per_day=12):
    """
    Prepare data for machine learning model
    """
    # Create target labels
    df = create_target_labels(df, profit_threshold, lookforward_window, min_trades_per_day)

    # Create features
    df, feature_columns = create_features(df)

    # Normalize features
    scaler = MinMaxScaler()
    df[feature_columns] = scaler.fit_transform(df[feature_columns])

    # Prepare final datasets
    X = df[feature_columns]
    y = df['target']

    return X, y, feature_columns, scaler
