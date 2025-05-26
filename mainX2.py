import os
import requests
import pandas as pd
from dotenv import load_dotenv
import plotly.graph_objects as go

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("SECRET_KEY")

if not api_key or not api_secret:
    raise ValueError("API Key hoặc API Secret không hợp lệ")

# Lấy dữ liệu Futures từ Binance (PERPETUAL only)
def get_futures_symbols():
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    response = requests.get(url)
    symbols = response.json()['symbols']
    perpetual_pairs = [s['symbol'] for s in symbols if s['contractType'] == 'PERPETUAL']
    return perpetual_pairs[:90]  # lấy 20 cặp đầu tiên

# Lấy giá hiện tại cho các cặp Futures
def get_futures_prices(pairs):
    prices = {}
    for pair in pairs:
        url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={pair}"
        res = requests.get(url)
        if res.status_code == 200:
            prices[pair] = float(res.json()['price'])
        else:
            print(f"Lỗi khi lấy giá {pair}: {res.status_code}")
    return prices

# Tính toán SL/TP theo yêu cầu: lỗ 1.5 USDT, lời 500 điểm
def calculate_sl_tp(price, balance=5, risk_pct=0.3, reward_pct=0.6, leverage=125):
    max_loss = balance * risk_pct        # số USDT có thể lỗ
    target_profit = balance * reward_pct # số USDT muốn lời

    position_value = balance * leverage  # tổng giá trị vị thế
    quantity = position_value / price    # số coin có thể mua

    # Tính mức lỗ lời trên mỗi coin
    loss_per_unit = max_loss / quantity
    profit_per_unit = target_profit / quantity

    stop_loss_price = price - loss_per_unit
    take_profit_price = price + profit_per_unit

    return round(stop_loss_price, 4), round(take_profit_price, 4), round(quantity, 3)

# Lấy dữ liệu nến (OHLC)
def get_binance_ohlc(symbol="BTCUSDT", interval="1h", limit=300):
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(url, params=params)
    data = response.json()
    ohlc = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    ohlc['timestamp'] = pd.to_datetime(ohlc['timestamp'], unit='ms')
    ohlc[['open', 'high', 'low', 'close']] = ohlc[['open', 'high', 'low', 'close']].astype(float)
    return ohlc

# MA
def calculate_moving_average(df, window):
    return df['close'].rolling(window=window).mean()

# Biểu đồ nến + MA
def plot_candlestick_chart(df, symbol):
    fig = go.Figure(data=[go.Candlestick(
        x=df['timestamp'],
        open=df['open'], high=df['high'],
        low=df['low'], close=df['close'], name=symbol
    )])

    df['MA50'] = calculate_moving_average(df, 50)
    df['MA200'] = calculate_moving_average(df, 200)

    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['MA50'], mode='lines', name='MA50', line={'color': 'blue'}))
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['MA200'], mode='lines', name='MA200', line={'color': 'red'}))
    fig.update_layout(title=f'{symbol} Futures Candlestick Chart', xaxis_title='Time', yaxis_title='Price')
    fig.show()

# ---------- MAIN ----------
# ---------- MAIN ----------
symbols = get_futures_symbols()
prices = get_futures_prices(symbols)
i = 0
for symbol in symbols:
    current_price = prices[symbol]
    stop_loss, take_profit, qty = calculate_sl_tp(current_price)

    print(f"--- {symbol} ---")
    print(f"Giá hiện tại: {current_price}")
    print(f"Khối lượng có thể vào: {qty} {symbol}")
    print(f"Stop Loss: {stop_loss}")
    print(f"Take Profit: {take_profit}")
    print()

    # Nếu muốn vẽ biểu đồ cho từng cặp, bỏ comment dòng dưới
    ohlc_data = get_binance_ohlc(symbol)
    plot_candlestick_chart(ohlc_data, symbol)
    if i >= 10:
      input("Enter to continue!")
      i=0
    i+=1
