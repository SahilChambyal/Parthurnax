# Trading Features Documentation

## Table of Contents
1. [Original Data Features](#original-data-features)
2. [Derived Technical Features](#derived-technical-features)
3. [Price-Based Features](#price-based-features)
4. [Volume Features](#volume-features)
5. [Technical Indicators](#technical-indicators)
6. [Time-Based Features](#time-based-features)
7. [Target Variable](#target-variable)

## Original Data Features

### Time Features
- **OpenTime**
  - Description: Start time of the candlestick
  - Format: Unix timestamp in milliseconds
  - Example: 1731608816000 = "2024-11-14 12:08:00"
  - Usage: Time series analysis, pattern recognition

- **CloseTime**
  - Description: End time of the candlestick
  - Format: Unix timestamp in milliseconds
  - Range: OpenTime + 59999ms (for 1-minute candles)
  - Usage: Period verification, data continuity checks

### Price Features
- **Open**
  - Description: First trade price in the period
  - Usage: Gap analysis, candlestick patterns
  - Example: 215.77 USDT

- **High**
  - Description: Highest trade price in the period
  - Usage: Resistance levels, volatility calculation
  - Example: 215.95 USDT

- **Low**
  - Description: Lowest trade price in the period
  - Usage: Support levels, volatility calculation
  - Example: 215.64 USDT

- **Close**
  - Description: Last trade price in the period
  - Usage: Trend analysis, most technical indicators
  - Example: 215.74 USDT

### Volume Features
- **Volume**
  - Description: Total trading volume in base asset (SOL)
  - Usage: Trading activity measurement
  - Example: 3081.647 SOL

- **QuoteAssetVolume**
  - Description: Total trading volume in quote asset (USDT)
  - Calculation: Σ(Trade Price × Trade Amount)
  - Example: 664978.94664 USDT

- **NumberOfTrades**
  - Description: Count of individual trades
  - Usage: Trading activity density
  - Example: 3134 trades

- **TakerBuyBaseVolume**
  - Description: Volume from buy orders (in SOL)
  - Usage: Buy pressure analysis
  - Example: 1976.52 SOL

- **TakerBuyQuoteVolume**
  - Description: Volume from buy orders (in USDT)
  - Usage: Buy pressure in quote currency
  - Example: 426514.65939 USDT

## Derived Technical Features

### Moving Averages
- **Simple Moving Average (SMA)**
  ```python
  df[f'sma_{window}'] = df['Close'].rolling(window=window).mean()
  ```
  - Windows: [5, 15, 30, 60] periods
  - Usage: Trend identification
  - Interpretation:
    - Price > SMA: Uptrend
    - Price < SMA: Downtrend
  - Normal Range: Varies with price

- **Exponential Moving Average (EMA)**
  ```python
  df[f'ema_{window}'] = df['Close'].ewm(span=window).mean()
  ```
  - Windows: [5, 15, 30, 60] periods
  - Usage: Faster trend identification
  - Interpretation: Same as SMA but more responsive
  - Normal Range: Varies with price

### Price Relatives
- **Close to SMA Ratio**
  ```python
  df[f'close_to_sma_{window}'] = df['Close'] / df[f'sma_{window}']
  ```
  - Usage: Trend strength measurement
  - Interpretation:
    - > 1: Above average (potential overbought)
    - < 1: Below average (potential oversold)
  - Normal Range: 0.95 to 1.05

### Volatility Measures
- **Rolling Volatility**
  ```python
  df[f'volatility_{window}'] = df['Close'].rolling(window=window).std()
  ```
  - Windows: [5, 15, 30, 60] periods
  - Usage: Risk measurement
  - Normal Range: Varies by market conditions

- **Average True Range (ATR)**
  ```python
  df['atr'] = talib.ATR(df['High'], df['Low'], df['Close'], timeperiod=14)
  ```
  - Usage: Volatility measurement, stop-loss sizing
  - Normal Range: Varies by price and volatility
  - Interpretation: Higher values indicate higher volatility

### Momentum Indicators
- **Relative Strength Index (RSI)**
  ```python
  df['rsi'] = talib.RSI(df['Close'], timeperiod=14)
  ```
  - Range: 0 to 100
  - Key Levels:
    - > 70: Overbought
    - < 30: Oversold
  - Usage: Momentum measurement, reversal signals

- **MACD (Moving Average Convergence Divergence)**
  ```python
  df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(
      df['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
  ```
  - Components:
    - MACD Line: 12-EMA minus 26-EMA
    - Signal Line: 9-EMA of MACD Line
    - Histogram: MACD minus Signal
  - Usage: Trend and momentum analysis
  - Signals:
    - MACD crosses Signal: Trading signal
    - Histogram changes sign: Momentum shift

### Volume Features
- **Volume Ratios**
  ```python
  df[f'volume_ratio_{window}'] = df['Volume'] / df[f'volume_sma_{window}']
  ```
  - Windows: [5, 15, 30, 60] periods
  - Interpretation:
    - > 1: Higher than average volume
    - < 1: Lower than average volume
  - Usage: Volume trend analysis, breakout confirmation

### Price Patterns
- **High-Low Ratio**
  ```python
  df['high_low_ratio'] = df['High'] / df['Low']
  ```
  - Usage: Volatility measurement
  - Normal Range: 1.000 to 1.020 (typical)
  - Higher values indicate higher volatility

- **Close Position**
  ```python
  df['close_position'] = (df['Close'] - df['Low']) / (df['High'] - df['Low'])
  ```
  - Range: 0 to 1
  - Interpretation:
    - Near 1: Strong buying pressure
    - Near 0: Strong selling pressure
    - Near 0.5: Neutral

### Time Features
- **Cyclic Time Encodings**
  ```python
  df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
  df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
  ```
  - Range: -1 to 1
  - Usage: Capturing time-of-day patterns
  - Advantage: Preserves cyclic nature of time

## Target Variable
- **Trading Signal (target)**
  ```python
  df['target'] = {1: Buy, -1: Sell, 0: Hold}
  ```
  - Creation: Based on future returns and dynamic thresholds
  - Parameters:
    - profit_threshold: Minimum profit for trade (default 0.3%)
    - lookforward_window: Future price window (default 30)
    - min_trades_per_day: Target trade frequency (default 12)
  - Distribution: Typically imbalanced (more holds than trades)

## Usage Notes

### Feature Importance
- Most significant features typically include:
  1. RSI
  2. MACD components
  3. Volume ratios
  4. Close to SMA ratios

### Feature Combinations
- Trend + Momentum: SMA crosses with RSI
- Volume + Price: Volume ratios with price breakouts
- Time + Volume: Activity patterns by time of day

### Risk Management
- Use ATR for position sizing
- Combine RSI and BB Width for volatility assessment
- Monitor Volume Ratios for trade conviction

### Data Preparation
```python
# Complete data preparation
X, y, feature_columns, scaler = prepare_ml_data(
    df,
    lookforward_window=30,
    profit_threshold=0.003,
    min_trades_per_day=12
)
```

## Visualization Example
```python
import matplotlib.pyplot as plt

def plot_key_indicators(df, window=100):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 10))

    # Price and SMAs
    ax1.plot(df['Close'], label='Close')
    ax1.plot(df['sma_20'], label='SMA20')
    ax1.set_title('Price and SMA')
    ax1.legend()

    # RSI
    ax2.plot(df['rsi'], label='RSI')
    ax2.axhline(y=70, color='r', linestyle='--')
    ax2.axhline(y=30, color='g', linestyle='--')
    ax2.set_title('RSI')

    # Volume Ratio
    ax3.plot(df['volume_ratio_20'], label='Volume Ratio')
    ax3.axhline(y=1, color='k', linestyle='--')
    ax3.set_title('Volume Ratio')

    plt.tight_layout()
    plt.show()
```
## Moving Average Features in Detail

### Simple Moving Average (SMA)
```python
df[f'sma_{window}'] = df['Close'].rolling(window=window).mean()
```
- **Calculation**:
  ```
  SMA = (P1 + P2 + ... + Pn) / n
  where:
  P = Price
  n = window size
  ```
- **Windows Used**: [5, 15, 30, 60]
- **Example**: For SMA_5
  ```
  If prices are [10, 11, 12, 13, 14]
  SMA_5 = (10 + 11 + 12 + 13 + 14) / 5 = 12
  ```
- **Purpose**: Trend identification, noise reduction
- **Range**: Varies with price level
- **Signals**:
  - Price > SMA: Bullish
  - Price < SMA: Bearish
  - SMA slope: Trend direction

### Exponential Moving Average (EMA)
```python
df[f'ema_{window}'] = df['Close'].ewm(span=window).mean()
```
- **Calculation**:
  ```
  Multiplier = 2 / (window + 1)
  EMA = (Close - Previous EMA) × Multiplier + Previous EMA
  ```
- **Windows Used**: [5, 15, 30, 60]
- **Example**:
  ```
  For EMA_5:
  Multiplier = 2/(5+1) = 0.333
  If Current Price = 100, Previous EMA = 95
  EMA = (100 - 95) × 0.333 + 95 = 96.67
  ```
- **Purpose**: Faster trend identification than SMA
- **Range**: Varies with price level
- **Signals**: Similar to SMA but reacts faster

## Price Relative Features

### Close to SMA Ratio
```python
df[f'close_to_sma_{window}'] = df['Close'] / df[f'sma_{window}']
```
- **Calculation**:
  ```
  Ratio = Current Close Price / SMA
  ```
- **Example**:
  ```
  If Close = 105 and SMA = 100
  Ratio = 105/100 = 1.05 (5% above average)
  ```
- **Purpose**: Measure price deviation from trend
- **Range**: Typically 0.95 to 1.05
- **Signals**:
  - > 1: Above average (potential overbought)
  - < 1: Below average (potential oversold)

## Volatility Features

### Rolling Volatility
```python
df[f'volatility_{window}'] = df['Close'].rolling(window=window).std()
```
- **Calculation**:
  ```
  σ = √(Σ(x - μ)² / n)
  where:
  x = price
  μ = mean price
  n = window size
  ```
- **Windows Used**: [5, 15, 30, 60]
- **Purpose**: Measure price dispersion
- **Range**: Varies by market conditions
- **Usage**: Risk assessment, position sizing

### Bollinger Bands Components
```python
df['bb_upper'] = df['bb_middle'] + (2 * std_dev)
df['bb_lower'] = df['bb_middle'] - (2 * std_dev)
df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
```
- **Calculations**:
  ```
  Middle Band = 20-period SMA
  Upper Band = Middle Band + (2 × σ)
  Lower Band = Middle Band - (2 × σ)
  Width = (Upper - Lower) / Middle
  ```
- **Purpose**: Volatility and trend measurement
- **Range**:
  - Width typically 0.02 to 0.08
  - Increases during high volatility
- **Signals**:
  - Price > Upper: Overbought
  - Price < Lower: Oversold
  - Width expanding: Increasing volatility
  - Width contracting: Decreasing volatility

## Momentum Features

### RSI (Relative Strength Index)
```python
df['rsi'] = talib.RSI(df['Close'].values, timeperiod=14)
```
- **Calculation**:
  ```
  RSI = 100 - (100 / (1 + RS))
  RS = Average Gain / Average Loss
  ```
- **Period**: 14 (standard)
- **Range**: 0 to 100
- **Signals**:
  - > 70: Overbought
  - < 30: Oversold
  - Divergence with price: Potential reversal
- **Example**:
  ```
  If Avg Gain = 2 and Avg Loss = 1
  RS = 2/1 = 2
  RSI = 100 - (100 / (1 + 2)) = 66.67
  ```

### MACD Components
```python
df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(df['Close'].values)
```
- **Calculations**:
  ```
  MACD Line = 12-period EMA - 26-period EMA
  Signal Line = 9-period EMA of MACD Line
  Histogram = MACD Line - Signal Line
  ```
- **Purpose**: Trend and momentum measurement
- **Range**: Varies around zero
- **Signals**:
  - MACD crosses Signal: Trading signal
  - Histogram changes sign: Momentum shift
  - Divergence with price: Potential reversal

## Volume Features

### Volume Moving Average
```python
df[f'volume_sma_{window}'] = df['Volume'].rolling(window=window).mean()
```
- **Calculation**:
  ```
  Volume SMA = (V1 + V2 + ... + Vn) / n
  where:
  V = Volume
  n = window size
  ```
- **Windows Used**: [5, 15, 30, 60]
- **Purpose**: Baseline volume level
- **Range**: Varies by trading activity

### Volume Ratio
```python
df[f'volume_ratio_{window}'] = df['Volume'] / df[f'volume_sma_{window}']
```
- **Calculation**:
  ```
  Ratio = Current Volume / Volume SMA
  ```
- **Example**:
  ```
  If Current Volume = 1500 and Volume SMA = 1000
  Ratio = 1.5 (50% above average volume)
  ```
- **Purpose**: Identify volume spikes
- **Range**: Typically 0.5 to 2.0
- **Signals**:
  - > 1.5: High volume (strong move)
  - < 0.5: Low volume (weak move)

## Price Pattern Features

### High-Low Ratio
```python
df['high_low_ratio'] = df['High'] / df['Low']
```
- **Calculation**:
  ```
  Ratio = High Price / Low Price
  ```
- **Purpose**: Intraperiod volatility
- **Range**: ≥ 1.0
- **Example**:
  ```
  If High = 105 and Low = 100
  Ratio = 1.05 (5% range)
  ```

### Close Position
```python
df['close_position'] = (df['Close'] - df['Low']) / (df['High'] - df['Low'])
```
- **Calculation**:
  ```
  Position = (Close - Low) / (High - Low)
  ```
- **Range**: 0 to 1
- **Example**:
  ```
  If High = 110, Low = 100, Close = 105
  Position = (105-100)/(110-100) = 0.5
  ```
- **Interpretation**:
  - 1.0: Closed at high (strong buyers)
  - 0.0: Closed at low (strong sellers)
  - 0.5: Closed at midpoint (neutral)

## Time Features

### Cyclic Hour Encoding
```python
df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
```
- **Calculation**:
  ```
  hour_sin = sin(2π × hour/24)
  hour_cos = cos(2π × hour/24)
  ```
- **Range**: -1 to 1
- **Example**:
  ```
  For hour = 6:
  hour_sin = sin(2π × 6/24) = 1.0
  hour_cos = cos(2π × 6/24) = 0.0
  ```
- **Purpose**: Capture time patterns
- **Advantage**: Preserves cyclic nature of time

### Cyclic Minute Encoding
```python
df['minute_sin'] = np.sin(2 * np.pi * df['minute'] / 60)
df['minute_cos'] = np.cos(2 * np.pi * df['minute'] / 60)
```
- **Calculation**: Similar to hour encoding but with 60-minute cycle
- **Range**: -1 to 1
- **Purpose**: Capture intra-hour patterns

## Combined Usage Examples

### Trend Strength
```python
trend_strength = (df['close_to_sma_15'] > 1) & (df['volume_ratio_15'] > 1.5) & (df['rsi'] < 70)
```

### Volatility Alert
```python
volatility_high = (df['bb_width'] > df['bb_width'].mean()) & (df['high_low_ratio'] > 1.02)
```

### Momentum Setup
```python
momentum_setup = (df['macd'] > df['macd_signal']) & (df['rsi'] > 50) & (df['close_position'] > 0.8)
```
