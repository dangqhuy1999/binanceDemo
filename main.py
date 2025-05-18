import os
import requests
from dotenv import load_dotenv
import plotly.graph_objects as go
import pandas as pd


# Tải thông tin từ file .env
load_dotenv()

# Lấy API Key và API Secret từ file .env
api_key = os.getenv("API_KEY")
api_secret = os.getenv("SECRET_KEY")

# Kiểm tra xem API Key và API Secret có hợp lệ không
if not api_key or not api_secret:
    raise ValueError("API Key hoặc API Secret không hợp lệ")

# Hàm lấy giá của 20 cặp tiền trên Binance
def get_prices():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Lỗi kết nối API: {response.status_code}")

    # Lấy danh sách các cặp giao dịch từ Binance
    symbols = response.json()['symbols']
    usdt_pairs = [symbol['symbol'] for symbol in symbols if 'USDT' in symbol['symbol'] and symbol['status'] == 'TRADING']

    # Chọn 20 cặp tiền bất kỳ
    selected_pairs = usdt_pairs[:20]
    
    prices = {}
    for pair in selected_pairs:
        price_url = f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"
        price_response = requests.get(price_url)
        
        if price_response.status_code == 200:
            price_data = price_response.json()
            prices[pair] = price_data['price']
        else:
            print(f"Lỗi khi lấy giá của {pair}: {price_response.status_code}")

    return prices

# Hàm tính toán Stop Loss và Take Profit
def calculate_sl_tp(price, leverage=125, risk_percentage=0.5, reward_percentage=1.0):
    # Stop Loss: giảm 0.5% giá
    stop_loss_price = price * (1 - risk_percentage / 100)
    
    # Take Profit: tăng 1% giá
    take_profit_price = price * (1 + reward_percentage / 100)
    
    # Với đòn bẩy x125, tính giá trị Stop Loss và Take Profit sau khi nhân đòn bẩy
    stop_loss_leverage = stop_loss_price * leverage
    take_profit_leverage = take_profit_price * leverage

    return stop_loss_price, take_profit_price, stop_loss_leverage, take_profit_leverage


# Hàm lấy dữ liệu OHLC từ Binance
def get_binance_ohlc(symbol="BTCUSDT", interval="1h", limit=100):
    url = f'https://api.binance.com/api/v1/klines'
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }
    response = requests.get(url, params=params)
    data = response.json()

    # Chuyển dữ liệu về DataFrame
    ohlc = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    ohlc['timestamp'] = pd.to_datetime(ohlc['timestamp'], unit='ms')
    ohlc['close'] = ohlc['close'].astype(float)
    return ohlc

# Hàm tính toán MA (Moving Average)
def calculate_moving_average(df, window):
    return df['close'].rolling(window=window).mean()

# Vẽ biểu đồ với Plotly
def plot_candlestick_chart(df, symbol):
    fig = go.Figure(data=[go.Candlestick(
        x=df['timestamp'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name=symbol
    )])

    # Tính toán các chỉ báo MA (Moving Average)
    df['MA50'] = calculate_moving_average(df, window=50)
    df['MA200'] = calculate_moving_average(df, window=200)

    # Thêm các đường MA vào biểu đồ
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['MA50'], mode='lines', name='MA50', line={'color': 'blue'}))
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['MA200'], mode='lines', name='MA200', line={'color': 'red'}))

    fig.update_layout(title=f'{symbol} Candlestick Chart', xaxis_title='Time', yaxis_title='Price')
    fig.show()

# Lấy dữ liệu và vẽ biểu đồ cho cặp BTCUSDT
symbol = "BTCUSDT"
ohlc_data = get_binance_ohlc(symbol)
plot_candlestick_chart(ohlc_data, symbol)

'''
# Lấy giá của 20 cặp tiền trên Binance
prices = get_prices()

# In ra giá và tính toán Stop Loss, Take Profit
for symbol, price in prices.items():
    price = float(price)  # Convert giá về kiểu float
    sl, tp, sl_leverage, tp_leverage = calculate_sl_tp(price)

    print(f"{symbol}:")
    print(f"  Giá hiện tại: {price}")
    print(f"  Stop Loss: {sl}, Take Profit: {tp}")
    print(f"  Stop Loss (với x125): {sl_leverage}, Take Profit (với x125): {tp_leverage}")
    print("="*50)

'''
