import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# IMPORT DARI FILE RAHASIA YANG SUDAH DIKOMPILASI (.pyc)
import analisis

st.set_page_config(page_title="FinSight Pro Dashboard", layout="wide", page_icon="📈")
st.title("📈 Advanced Finance Analytics & Prediction Dashboard")
st.markdown("Aplikasi analisis & prediksi saham berbasis **Teknikal, Fundamental, Makro, Linear Regression, & Bandarmologi**.")

st.sidebar.header("⚙️ Pengaturan Analisis")
ticker_input = st.sidebar.text_input("Simbol Saham (Ticker):", value="BBRI.JK").upper()

col_date1, col_date2 = st.sidebar.columns(2)
with col_date1:
    start_date = st.date_input("Mulai:", datetime.now() - timedelta(days=365))
with col_date2:
    end_date = st.date_input("Selesai:", datetime.now())

btn_analyze = st.sidebar.button("Mulai Analisis", type="primary")

@st.cache_data
def load_stock_data(ticker, start, end):
    stock = yf.Ticker(ticker)
    df = stock.history(start=start, end=end)
    df = analisis.calculate_indicators(df) # Memanggil dari file .pyc
    info = stock.info
    try:
        df_m = stock.history(period="5y", interval="1mo")
    except:
        df_m = pd.DataFrame()
    return df, df_m, info

if btn_analyze or ticker_input:
    with st.spinner('Mengambil dan memproses data dari pasar...'):
        try:
            df, df_monthly, info = load_stock_data(ticker_input, start_date, end_date)
            st.subheader(f"{info.get('longName', ticker_input)} ({ticker_input})")

            current_price = info.get('currentPrice', df['Close'].iloc[-1] if not df.empty else 0)
            currency = info.get('currency', 'IDR')

            metric_col1, metric_col2, metric_col3 = st.columns(3)
            metric_col1.metric("Harga Terakhir", f"{currency} {current_price:,}")
            metric_col2.metric("Kapitalisasi Pasar", f"{info.get('marketCap', 0):,}")
            metric_col3.metric("Rekomendasi Konsensus Global", info.get('recommendationKey', 'N/A').upper())

            # MEMANGGIL RENDER TAB DARI FILE .PYC
            analisis.render_tabs(df, df_monthly, info)

            # --- SINTESIS AKHIR ---
            st.divider()
            st.subheader("🤖 Hasil Analisis Sintesis Mandiri Terpadu")
            skor_mandiri = 0
            total_bobot = 4
            catatan_analisis = []

            if not df.empty:
                harga_terakhir = df['Close'].iloc[-1]
                ma50_terakhir = df['MA50'].iloc[-1]
                rsi_terakhir = df['RSI'].iloc[-1]
                macd_terakhir = df['MACD'].iloc[-1]
                signal_terakhir = df['Signal_Line'].iloc[-1]

                if harga_terakhir > ma50_terakhir:
                    skor_mandiri += 1
                    catatan_analisis.append("✅ **Teknikal (MA50):** Harga berada di atas MA50 (Tren jangka menengah Bullish).")
                else:
                    catatan_analisis.append("❌ **Teknikal (MA50):** Harga di bawah MA50 (Tren cenderung turun/Bearish).")

                if rsi_terakhir < 30:
                    skor_mandiri += 1
                    catatan_analisis.append(f"🔥 **Teknikal (RSI):** RSI berada di angka {rsi_terakhir:.2f} (< 30). Kondisi *Oversold*.")
                elif rsi_terakhir > 70:
                    catatan_analisis.append(f"🚨 **Teknikal (RSI):** RSI berada di angka {rsi_terakhir:.2f} (> 70). Kondisi *Overbought*.")
                else:
                    skor_mandiri += 0.5
                    catatan_analisis.append(f"🟡 **Teknikal (RSI):** RSI normal di angka {rsi_terakhir:.2f}. Momentum stabil.")

                if macd_terakhir > signal_terakhir:
                    skor_mandiri += 1
                    catatan_analisis.append("✅ **Teknikal (MACD):** MACD line di atas Signal line (*Golden Cross*).")
                else:
                    catatan_analisis.append("❌ **Teknikal (MACD):** MACD line di bawah Signal line (*Death Cross*).")

            pbv = info.get('priceToBook', 0)
            if pbv and pbv < 2.0:
                skor_mandiri += 1
                catatan_analisis.append(f"✅ **Fundamental:** PBV menarik di angka {pbv:.2f} (< 2.0).")
            else:
                catatan_analisis.append(f"❌ **Fundamental:** PBV premium/cukup mahal yaitu {pbv if pbv else 'N/A'}.")

            if skor_mandiri >= 3.5:
                status_rekomendasi = "STRONG BUY 🔥"
                warna_box = st.success
            elif skor_mandiri >= 2.5:
                status_rekomendasi = "ACCUMULATE / BUY 📈"
                warna_box = st.info
            elif skor_mandiri >= 1.5:
                status_rekomendasi = "HOLD / NEUTRAL ⏳"
                warna_box = st.warning
            else:
                status_rekomendasi = "AVOID / BEARISH 🚨"
                warna_box = st.error

            st.markdown("### 💻 Kesimpulan Rekomendasi Aplikasi")
            warna_box(f"**Rekomendasi Utama Mandiri:** {status_rekomendasi} (Skor Otomatis: {skor_mandiri}/{total_bobot})")
            
            st.write("")
            st.markdown("**Poin Konsiderasi Pembuat Keputusan:**")
            for poin in catatan_analisis:
                st.markdown(poin)

        except Exception as e:
            st.error(f"Gagal memproses kalkulasi dasbor terpadu: {e}")
