import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ======================
# 初期設定
# ======================
st.set_page_config(page_title="米国株 短期売買アプリ", layout="wide")
st.title("📈 米国株 短期売買スクリーナー")

# ======================
# セクター日本語マップ
# ======================
SECTOR_JP = {
    "Technology": "情報技術",
    "Consumer Cyclical": "一般消費財",
    "Consumer Defensive": "生活必需品",
    "Healthcare": "ヘルスケア",
    "Financial Services": "金融",
    "Communication Services": "通信サービス",
    "Industrials": "資本財",
    "Energy": "エネルギー",
    "Utilities": "公益事業",
    "Real Estate": "不動産",
    "Basic Materials": "素材"
}

# ======================
# 対象銘柄（拡張版）
# ======================
TICKERS = [
    "AAPL","MSFT","GOOGL","AMZN","META",
    "NVDA","AMD","INTC","TSM","ASML",
    "TSLA","NFLX","ADBE","CRM","ORCL",
    "PYPL","SQ","COIN","SOFI",
    "SHOP","UBER","ABNB","DASH",
    "PLTR","SNOW","RBLX"
]

# ======================
# 関数群
# ======================
def get_sector_jp(ticker):
    try:
        info = yf.Ticker(ticker).info
        sector = info.get("sector", "Unknown")
        return SECTOR_JP.get(sector, sector)
    except:
        return "不明"

def calc_indicators(df):
    df["SMA5"] = df["Close"].rolling(5).mean()
    df["SMA20"] = df["Close"].rolling(20).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + rs))

    df["Volume_MA5"] = df["Volume"].rolling(5).mean()
    df["Volume_MA20"] = df["Volume"].rolling(20).mean()

    df["Return_5d"] = df["Close"].pct_change(5) * 100
    return df

def score_stock(df):
    score = 0
    if df["SMA5"].iloc[-1] > df["SMA20"].iloc[-1]:
        score += 2
    if 40 <= df["RSI"].iloc[-1] <= 60:
        score += 2
    if df["Volume_MA5"].iloc[-1] > df["Volume_MA20"].iloc[-1]:
        score += 1
    if -5 <= df["Return_5d"].iloc[-1] <= 5:
        score += 1
    return score

def plot_chart(df, ticker):
    fig, ax = plt.subplots(figsize=(10,4))
    ax.plot(df.index, df["Close"], label="終値")
    ax.plot(df.index, df["SMA5"], label="SMA5")
    ax.plot(df.index, df["SMA20"], label="SMA20")
    ax.set_title(ticker)
    ax.legend()
    return fig

# ======================
# メイン処理
# ======================
if st.button("🔍 分析開始"):
    results = []

    with st.spinner("分析中..."):
        for ticker in TICKERS:
            df = yf.download(ticker, period="3mo", progress=False)
            if df.empty or len(df) < 30:
                continue

            df = calc_indicators(df)
            score = score_stock(df)

            if score >= 3:
                results.append({
                    "銘柄": ticker,
                    "セクター": get_sector_jp(ticker),
                    "スコア": score,
                    "RSI": round(df["RSI"].iloc[-1], 1),
                    "5日騰落率(%)": round(df["Return_5d"].iloc[-1], 1)
                })

    ranking = pd.DataFrame(results).sort_values("スコア", ascending=False)

    st.subheader("📊 短期売買ランキング（スコア順）")
    st.dataframe(ranking, use_container_width=True)

    # ======================
    # 上位銘柄チャート
    # ======================
    top_n = st.slider("📈 チャート表示する上位銘柄数", 1, 5, 3)
    top_stocks = ranking.head(top_n)

    st.subheader("📈 上位銘柄チャート")

    for ticker in top_stocks["銘柄"]:
        df = yf.download(ticker, period="3mo", progress=False)
        df = calc_indicators(df)
        fig = plot_chart(df, ticker)
        st.pyplot(fig)
