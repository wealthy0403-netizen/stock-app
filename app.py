import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="米国株 短期売買アプリ", layout="wide")
st.title("📈 米国株 短期売買スクリーナー")

# -----------------------
# テクニカル計算
# -----------------------
def calc_indicators(df):
    df["SMA5"] = df["Close"].rolling(5).mean()
    df["SMA20"] = df["Close"].rolling(20).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(9).mean() / loss.rolling(9).mean()
    df["RSI"] = 100 - (100 / (1 + rs))

    ema12 = df["Close"].ewm(span=12).mean()
    ema26 = df["Close"].ewm(span=26).mean()
    df["MACD"] = ema12 - ema26
    df["Signal"] = df["MACD"].ewm(span=9).mean()

    return df

# -----------------------
# チャート描画
# -----------------------
def plot_chart(df, ticker):
    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)

    axes[0].plot(df.index, df["Close"], label="株価")
    axes[0].plot(df.index, df["SMA5"], label="SMA5")
    axes[0].plot(df.index, df["SMA20"], label="SMA20")
    axes[0].set_title(f"{ticker} 株価")
    axes[0].legend()

    axes[1].plot(df.index, df["RSI"], label="RSI")
    axes[1].axhline(40, linestyle="--")
    axes[1].axhline(60, linestyle="--")
    axes[1].set_title("RSI")
    axes[1].legend()

    axes[2].plot(df.index, df["MACD"], label="MACD")
    axes[2].plot(df.index, df["Signal"], label="Signal")
    axes[2].axhline(0, linestyle="--")
    axes[2].set_title("MACD")
    axes[2].legend()

    plt.tight_layout()
    return fig

# -----------------------
# 分析実行
# -----------------------
if st.button("🔍 分析開始"):
    tickers = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "JPM", "V", "KO"]
    results = []

    with st.spinner("分析中..."):
        for t in tickers:
            df = yf.Ticker(t).history(period="6mo")
            if len(df) < 30:
                continue

            df = calc_indicators(df)

            buy_score = 0
            sell_score = 0

            if df["RSI"].iloc[-1] < 40:
                buy_score += 1
            if df["RSI"].iloc[-1] > 60:
                sell_score += 1
            if df["MACD"].iloc[-1] > df["Signal"].iloc[-1]:
                buy_score += 1
            if df["MACD"].iloc[-1] < df["Signal"].iloc[-1]:
                sell_score += 1
            if df["SMA5"].iloc[-1] > df["SMA20"].iloc[-1]:
                buy_score += 1
            if df["SMA5"].iloc[-1] < df["SMA20"].iloc[-1]:
                sell_score += 1

            results.append({
                "ティッカー": t,
                "終値": round(df["Close"].iloc[-1], 2),
                "買いスコア": buy_score,
                "売りスコア": sell_score
            })

    result_df = pd.DataFrame(results)

    st.subheader("🟢 買い候補")
    st.dataframe(result_df.sort_values("買いスコア", ascending=False))

    st.subheader("🔴 売り候補")
    st.dataframe(result_df.sort_values("売りスコア", ascending=False))

    st.subheader("📊 チャート表示")
    selected = st.selectbox("銘柄を選択", result_df["ティッカー"])

    chart_df = yf.Ticker(selected).history(period="6mo")
    chart_df = calc_indicators(chart_df)

    fig = plot_chart(chart_df, selected)
    st.pyplot(fig)
