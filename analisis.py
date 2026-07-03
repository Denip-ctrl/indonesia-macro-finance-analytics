import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

def calculate_indicators(df):
    if df.empty:
        return df
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))

    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Histogram'] = df['MACD'] - df['Signal_Line']
    return df

def predict_linear_regression(series, days_to_forecast):
    y = series.dropna().values
    x = np.arange(len(y))
    m, c = np.polyfit(x, y, 1)
    x_future = np.arange(len(y), len(y) + days_to_forecast)
    y_future = m * x_future + c
    return y_future, m

def render_tabs(df, df_monthly, info):
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Fundamental Emiten", "📉 Analisis Teknikal", 
        "🔮 Prediksi Harian (5 Hari)", "🪐 Prediksi Makro (3 Bulan)", 
        "🌍 Situasi Ekonomi", "🕵️‍♂️ Pergerakan Bandar (Bandarmologi)"
    ])

    with tab1:
        st.subheader("📋 Kesehatan Keuangan & Valuasi Saham")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            st.table(pd.DataFrame({"Metrik": ["Trailing PE", "Forward PE", "Price to Book (PBV)"], "Nilai": [info.get('trailingPE', 'N/A'), info.get('forwardPE', 'N/A'), info.get('priceToBook', 'N/A')]}))
        with f_col2:
            st.table(pd.DataFrame({"Metrik": ["Profit Margin", "Return on Equity (ROE)", "Revenue Growth (YoY)"], "Nilai": [info.get('profitMargins', 'N/A'), info.get('returnOnEquity', 'N/A'), info.get('revenueGrowth', 'N/A')]}))

    with tab2:
        st.subheader("📉 Grafik Tren Harga & Indikator Momentum")
        if not df.empty:
            fig_price = go.Figure()
            fig_price.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Harga'))
            fig_price.add_trace(go.Scatter(x=df.index, y=df['MA50'], line=dict(color='orange', width=1.5), name='MA 50'))
            fig_price.update_layout(xaxis_rangeslider_visible=False, height=300, template="plotly_white")
            st.plotly_chart(fig_price, use_container_width=True)

    with tab3:
        st.subheader("🔮 Proyeksi Jangka Pendek (5 Hari)")
        if len(df) > 10:
            recent_data = df['Close'].tail(60)
            predictions_5d, _ = predict_linear_regression(recent_data, 5)
            last_date = recent_data.index[-1]
            future_dates = [last_date] + [last_date + timedelta(days=i) for i in range(1, 6)]
            fig_pred_5d = go.Figure()
            fig_pred_5d.add_trace(go.Scatter(x=recent_data.index, y=recent_data.values, name="Harga Aktual"))
            fig_pred_5d.add_trace(go.Scatter(x=future_dates, y=[recent_data.values[-1]] + list(predictions_5d), name="Proyeksi", line=dict(color="red", dash="dash")))
            st.plotly_chart(fig_pred_5d, use_container_width=True)

    with tab4:
        st.subheader("🪐 Proyeksi Makro Bulanan (3 Bulan)")
        if not df_monthly.empty and len(df_monthly) > 6:
            monthly_close = df_monthly['Close'].dropna()
            predictions_3m, _ = predict_linear_regression(monthly_close, 3)
            last_m_date = monthly_close.index[-1]
            future_m = [last_m_date] + [last_m_date + pd.DateOffset(months=i) for i in range(1, 4)]
            fig_pred_3m = go.Figure()
            fig_pred_3m.add_trace(go.Scatter(x=monthly_close.index, y=monthly_close.values, name="Aktual Bulanan"))
            fig_pred_3m.add_trace(go.Scatter(x=future_m, y=[monthly_close.values[-1]] + list(predictions_3m), name="Proyeksi Makro", line=dict(color="orange", dash="dot")))
            st.plotly_chart(fig_pred_3m, use_container_width=True)

    with tab5:
        st.subheader("🏛️ Parameter Indikator Makro Ekonomi")
        st.metric("BI-Rate (Asumsi)", "6.25%")
        st.metric("Inflasi YoY (Asumsi)", "2.8%")

    with tab6:
        st.subheader("🕵️‍♂️ Deteksi Jejak Volume & Aktivitas Pasar")
        st.markdown("Analisis algoritma mendeteksi pergerakan dana besar berdasarkan anomali rasio *Volume vs Price Action*.")
        if len(df) > 20:
            df_recent = df.tail(30).copy()
            df_recent['Daily_Return_Pct'] = df_recent['Close'].pct_change() * 100
            df_recent['Vol_Ratio'] = df_recent['Volume'] / df_recent['Vol_MA20']
            sinyal_bandar = []
            for idx, row in df_recent.iterrows():
                tgl_str = idx.strftime('%Y-%m-%d')
                ret = row['Daily_Return_Pct']
                v_ratio = row['Vol_Ratio']
                if abs(ret) > 4.0 and v_ratio < 0.6:
                    sinyal_bandar.append({"Tanggal": tgl_str, "Tipe Anomali": "🚨 PERDAGANGAN KOSONG (POM-POM)", "Deskripsi": f"Harga bergerak agresif ({ret:.2f}%), namun volume sangat sepi ({v_ratio*100:.1f}% dari rata-rata). Indikasi harga dimanipulasi naik tanpa likuiditas riil."})
                elif abs(ret) < 1.5 and v_ratio > 2.2:
                    sinyal_bandar.append({"Tanggal": tgl_str, "Tipe Anomali": "🔥 AKUMULASI TERSEMBUNYI", "Deskripsi": f"Harga bergerak tenang ({ret:.2f}%), tetapi volume melonjak raksasa ({v_ratio:.1f}x lipat rata-rata). Tanda tangan besar sedang menyerap pasokan barang di bawah pasar."})
            fig_vol = go.Figure()
            fig_vol.add_trace(go.Bar(x=df_recent.index, y=df_recent['Volume'], name="Volume Transaksi Harian", marker_color="teal"))
            fig_vol.add_trace(go.Scatter(x=df_recent.index, y=df_recent['Vol_MA20'], name="Batas Rata-Rata (MA20)", line=dict(color="red", width=1.5)))
            fig_vol.update_layout(title="Visualisasi Lonjakan Volume Transaksi (30 Hari Terakhir)", template="plotly_white", height=350)
            st.plotly_chart(fig_vol, use_container_width=True)
            if sinyal_bandar:
                st.warning("⚠️ **Log Temuan Indikasi Aktivitas Pasar Tidak Wajar:**")
                st.table(pd.DataFrame(sinyal_bandar))
            else:
                st.success("✅ **Kondisi Normal:** Tidak terdeteksi anomali perdagangan kosong atau akumulasi ekstrem dalam 30 hari terakhir.")
        else:
            st.warning("Data harian tidak mencukupi untuk menjalankan modul pencatatan volume.")
