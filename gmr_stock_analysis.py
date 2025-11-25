import pandas as pd
import numpy as np
import yfinance as yf
import json
from datetime import datetime

ticker = "GMRAIRPORT.NS"
print(f"\n{'='*100}")
print(f"GMR AIRPORTS STOCK ANALYSIS")
print(f"{'='*100}\n")

# Download data
print(f"Downloading {ticker} data...")
data_30d = yf.download(tickers=ticker, period="1mo", interval="1d", auto_adjust=True)
data_90d = yf.download(tickers=ticker, period="3mo", interval="1d", auto_adjust=True)

print(f"Downloading index data...")
nifty_30d = yf.download(tickers="^NSEI", period="1mo", interval="1d", auto_adjust=True)
sensex_30d = yf.download(tickers="^BSESN", period="1mo", interval="1d", auto_adjust=True)
nifty_90d = yf.download(tickers="^NSEI", period="3mo", interval="1d", auto_adjust=True)
sensex_90d = yf.download(tickers="^BSESN", period="3mo", interval="1d", auto_adjust=True)

# Flatten multi-index columns
for df in [data_30d, data_90d, nifty_30d, sensex_30d, nifty_90d, sensex_90d]:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if hasattr(df.index, 'tz'):
        df.index = df.index.tz_localize(None)

print(f"✅ Data downloaded successfully\n")

# Get stock info for valuation
stock = yf.Ticker(ticker)
info = stock.info

common_dates = data_30d.index.intersection(nifty_30d.index).intersection(sensex_30d.index)
common_dates = data_30d.index.intersection(nifty_30d.index).intersection(sensex_30d.index)

daily_analysis = pd.DataFrame()
daily_analysis['Date'] = data_30d.loc[common_dates].index.strftime('%Y-%m-%d')
daily_analysis['Open'] = data_30d.loc[common_dates, 'Open'].values
daily_analysis['High'] = data_30d.loc[common_dates, 'High'].values
daily_analysis['Low'] = data_30d.loc[common_dates, 'Low'].values
daily_analysis['Close'] = data_30d.loc[common_dates, 'Close'].values
daily_analysis['Volume'] = data_30d.loc[common_dates, 'Volume'].values

# NIFTY and SENSEX data
daily_analysis['NIFTY_Close'] = nifty_30d.loc[common_dates, 'Close'].values
daily_analysis['NIFTY_Change_Pct'] = nifty_30d.loc[common_dates, 'Close'].pct_change().values * 100
daily_analysis['SENSEX_Close'] = sensex_30d.loc[common_dates, 'Close'].values
daily_analysis['SENSEX_Change_Pct'] = sensex_30d.loc[common_dates, 'Close'].pct_change().values * 100

# Calculate metrics
daily_analysis['Daily_Change_Pct'] = data_30d.loc[common_dates, 'Close'].pct_change().values * 100
daily_analysis['Daily_Return'] = daily_analysis['Daily_Change_Pct']
daily_analysis['Intraday_Range'] = daily_analysis['High'] - daily_analysis['Low']
daily_analysis['Intraday_Range_Pct'] = (daily_analysis['Intraday_Range'] / daily_analysis['Close']) * 100
daily_analysis['Value_Traded_Cr'] = (daily_analysis['Volume'] * daily_analysis['Close']) / 10_000_000
daily_analysis['Volatility_5D'] = data_30d.loc[common_dates, 'Close'].pct_change().rolling(5).std().values * 100

avg_volume = daily_analysis['Volume'].mean()
daily_analysis['Volume_vs_Avg'] = (daily_analysis['Volume'] / avg_volume) * 100

common_dates_90d = data_90d.index.intersection(nifty_90d.index).intersection(sensex_90d.index)
common_dates_90d = data_90d.index.intersection(nifty_90d.index).intersection(sensex_90d.index)
gmr_returns_nifty = data_90d.loc[common_dates_90d, 'Close'].pct_change().dropna()
nifty_returns = nifty_90d.loc[common_dates_90d, 'Close'].pct_change().dropna()
gmr_returns_sensex = data_90d.loc[common_dates_90d, 'Close'].pct_change().dropna()
sensex_returns = sensex_90d.loc[common_dates_90d, 'Close'].pct_change().dropna()

# Beta calculation
beta_nifty = np.cov(gmr_returns_nifty, nifty_returns)[0][1] / np.var(nifty_returns)
beta_sensex = np.cov(gmr_returns_sensex, sensex_returns)[0][1] / np.var(sensex_returns)

# Correlation
correlation_nifty = np.corrcoef(gmr_returns_nifty, nifty_returns)[0][1]
correlation_sensex = np.corrcoef(gmr_returns_sensex, sensex_returns)[0][1]

# Volatility
returns_30d = data_30d.loc[common_dates, 'Close'].pct_change().dropna()
volatility_30d = returns_30d.std() * np.sqrt(252) * 100

# Max Drawdown
cumulative_returns = (1 + returns_30d).cumprod()
running_max = cumulative_returns.expanding().max()
drawdown = (cumulative_returns - running_max) / running_max
max_drawdown = drawdown.min() * 100

# Alpha calculation (Risk-free rate = 7% annually)
risk_free_rate_daily = 0.07 / 252
alpha_nifty = (gmr_returns_nifty.mean() - risk_free_rate_daily) - beta_nifty * (nifty_returns.mean() - risk_free_rate_daily)
alpha_nifty_annualized = alpha_nifty * 252 * 100
alpha_sensex = (gmr_returns_sensex.mean() - risk_free_rate_daily) - beta_sensex * (sensex_returns.mean() - risk_free_rate_daily)
alpha_sensex_annualized = alpha_sensex * 252 * 100

# Tracking Error & Information Ratio
tracking_error = (gmr_returns_nifty - nifty_returns).std() * np.sqrt(252) * 100
information_ratio = alpha_nifty_annualized / tracking_error if tracking_error != 0 else 0

stock_30d_return = ((daily_analysis['Close'].iloc[-1] - daily_analysis['Close'].iloc[0]) / daily_analysis['Close'].iloc[0]) * 100
stock_30d_return = ((daily_analysis['Close'].iloc[-1] - daily_analysis['Close'].iloc[0]) / daily_analysis['Close'].iloc[0]) * 100

# (B) 30-Day NIFTY Return
nifty_30d_return = ((daily_analysis['NIFTY_Close'].iloc[-1] - daily_analysis['NIFTY_Close'].iloc[0]) / daily_analysis['NIFTY_Close'].iloc[0]) * 100

# 30-Day SENSEX Return
sensex_30d_return = ((daily_analysis['SENSEX_Close'].iloc[-1] - daily_analysis['SENSEX_Close'].iloc[0]) / daily_analysis['SENSEX_Close'].iloc[0]) * 100

# Relative Strength vs NIFTY
relative_strength_nifty = stock_30d_return - nifty_30d_return

# (C) Price Stability Index
price_stability_index = daily_analysis['Intraday_Range_Pct'].mean()

# (D) Liquidity Risk Score Inputs
days_above_avg_volume = (daily_analysis['Volume'] > avg_volume).sum()
days_high_liquidity = (daily_analysis['Volume'] > 2 * avg_volume).sum()
days_low_liquidity = (daily_analysis['Volume'] < 0.5 * avg_volume).sum()
volume_stability = (daily_analysis['Volume'].std() / avg_volume) * 100

# (E) Trend Indicators
trend_5d_return = ((daily_analysis['Close'].iloc[-1] - daily_analysis['Close'].iloc[-6]) / daily_analysis['Close'].iloc[-6]) * 100 if len(daily_analysis) >= 6 else None
trend_30d_return = stock_30d_return

# (F) Volatility Skew
max_gain = daily_analysis['Daily_Return'].max()
max_loss = daily_analysis['Daily_Return'].min()
volatility_skew = max_gain - max_loss

# (G) Price Gap Risk
daily_analysis['Prev_Close'] = daily_analysis['Close'].shift(1)
gap_up_days = (daily_analysis['Open'] > daily_analysis['Prev_Close']).sum()
gap_down_days = (daily_analysis['Open'] < daily_analysis['Prev_Close']).sum()

# Price summary
current_price = daily_analysis['Close'].iloc[-1]
previous_close = daily_analysis['Close'].iloc[-2] if len(daily_analysis) > 1 else current_price
price_change_pct = ((current_price - previous_close) / previous_close) * 100
day_high = daily_analysis['High'].max()
day_low = daily_analysis['Low'].min()

# Sharpe Ratio
risk_free_rate_daily = 0.07 / 252
excess_returns = returns_30d - risk_free_rate_daily
sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252) if excess_returns.std() != 0 else 0

# =============================================================================
# DISPLAY OHLCV TABLE
# =============================================================================

print(f"\n📊 GMR AIRPORTS - OHLCV DATA (30 Days):")
print(f"{'='*100}\n")
print(f"{'Date':<12} {'Open':>8} {'High':>8} {'Low':>8} {'Close':>8} {'Volume':>12}")
print(f"{'-'*70}")

for idx, row in daily_analysis.iterrows():
    print(f"{row['Date']:<12} "
          f"₹{row['Open']:>7.2f} "
          f"₹{row['High']:>7.2f} "
          f"₹{row['Low']:>7.2f} "
          f"₹{row['Close']:>7.2f} "
          f"{row['Volume']:>12,.0f}")

print(f"{'-'*70}\n")

# =============================================================================
# DISPLAY JSON SUMMARY IN TERMINAL
# =============================================================================

print(f"\n{'='*100}")
print(f"📋 JSON OUTPUT SUMMARY")
print(f"{'='*100}\n")

print(f"✅ Price Summary:")
print(f"   Current: ₹{current_price:.2f} | Change: {price_change_pct:+.2f}%")
print(f"   30D High: ₹{day_high:.2f} | 30D Low: ₹{day_low:.2f}")

print(f"\n✅ Returns Summary:")
print(f"   GMR 30D Return: {stock_30d_return:+.2f}%")
print(f"   NIFTY 30D Return: {nifty_30d_return:+.2f}%")
print(f"   SENSEX 30D Return: {sensex_30d_return:+.2f}%")
print(f"   Relative Strength vs NIFTY: {relative_strength_nifty:+.2f}%")

print(f"\n✅ Liquidity:")
print(f"   Avg Daily Volume: {avg_volume:,.0f} shares")
print(f"   Total 30D Volume: {daily_analysis['Volume'].sum():,.0f} shares")
print(f"   Total 30D Value: ₹{daily_analysis['Value_Traded_Cr'].sum():.2f} Cr")
print(f"   High Volume Days: {days_high_liquidity} | Low Volume Days: {days_low_liquidity}")
print(f"   Volume Stability Index: {volume_stability:.2f}")

print(f"\n✅ Risk Metrics:")
print(f"   Beta (NIFTY): {beta_nifty:.3f} | Beta (SENSEX): {beta_sensex:.3f}")
print(f"   Volatility (30D): {volatility_30d:.2f}% | Max Drawdown: {max_drawdown:.2f}%")
print(f"   Alpha (NIFTY): {alpha_nifty_annualized:+.2f}% | Alpha (SENSEX): {alpha_sensex_annualized:+.2f}%")
print(f"   Sharpe Ratio: {sharpe_ratio:.3f} | Information Ratio: {information_ratio:.3f}")

print(f"\n✅ Trend Indicators:")
print(f"   5D Trend: {trend_5d_return:+.2f}%" if trend_5d_return else "   5D Trend: N/A")
print(f"   30D Trend: {trend_30d_return:+.2f}%")
print(f"   Price Stability Index: {price_stability_index:.2f}")
print(f"   Volatility Skew: {volatility_skew:.2f}")

print(f"\n✅ Gap Risk:")
print(f"   Gap Up Days: {gap_up_days} | Gap Down Days: {gap_down_days}")

print(f"\n✅ Complete Data: {len(daily_analysis)} days included\n")

# =============================================================================
# DISPLAY ANALYSIS SUMMARY
# =============================================================================

print(f"\n{'='*100}")
print(f"📊 ANALYSIS SUMMARY - GMR AIRPORTS")
print(f"{'='*100}\n")

print(f"💰 PRICE SUMMARY:")
print(f"   Current Price: ₹{current_price:.2f}")
print(f"   Previous Close: ₹{previous_close:.2f}")
print(f"   Change: {price_change_pct:+.2f}%")
print(f"   30-Day High: ₹{day_high:.2f}")
print(f"   30-Day Low: ₹{day_low:.2f}")

print(f"\n📈 RETURNS SUMMARY (30 Days):")
print(f"   GMR Stock Return: {stock_30d_return:+.2f}%")
print(f"   NIFTY 50 Return: {nifty_30d_return:+.2f}%")
print(f"   SENSEX Return: {sensex_30d_return:+.2f}%")
print(f"   Relative Strength vs NIFTY: {relative_strength_nifty:+.2f}%")

print(f"\n💧 LIQUIDITY:")
print(f"   Avg Daily Volume: {avg_volume:,.0f} shares")
print(f"   Avg Daily Value: ₹{daily_analysis['Value_Traded_Cr'].mean():.2f} Cr")
print(f"   Total 30D Volume: {daily_analysis['Volume'].sum():,.0f} shares")
print(f"   Total 30D Value: ₹{daily_analysis['Value_Traded_Cr'].sum():.2f} Cr")
print(f"   High Volume Days (>2x avg): {days_high_liquidity}")
print(f"   Low Volume Days (<0.5x avg): {days_low_liquidity}")
print(f"   Volume Stability Index: {volume_stability:.2f}%")

print(f"\n📊 RISK METRICS:")
print(f"   Beta (vs NIFTY): {beta_nifty:.3f}")
print(f"   Beta (vs SENSEX): {beta_sensex:.3f}")
print(f"   Correlation (NIFTY): {correlation_nifty:.3f}")
print(f"   Correlation (SENSEX): {correlation_sensex:.3f}")
print(f"   30-Day Volatility (Annualized): {volatility_30d:.2f}%")
print(f"   Max Drawdown: {max_drawdown:.2f}%")
print(f"   Alpha (vs NIFTY): {alpha_nifty_annualized:+.2f}%")
print(f"   Alpha (vs SENSEX): {alpha_sensex_annualized:+.2f}%")
print(f"   Sharpe Ratio: {sharpe_ratio:.3f}")
print(f"   Information Ratio: {information_ratio:.3f}")
print(f"   Tracking Error: {tracking_error:.2f}%")

print(f"\n📉 TREND INDICATORS:")
print(f"   5-Day Trend: {trend_5d_return:+.2f}%" if trend_5d_return else "   5-Day Trend: N/A")
print(f"   30-Day Trend: {trend_30d_return:+.2f}%")
print(f"   Price Stability Index: {price_stability_index:.2f}%")
print(f"   Volatility Skew: {volatility_skew:.2f}%")

print(f"\n⚠️  GAP RISK:")
print(f"   Gap Up Days: {gap_up_days}")
print(f"   Gap Down Days: {gap_down_days}")
print(f"   Total Gap Days: {gap_up_days + gap_down_days}")

print(f"\n{'='*100}\n")

# =============================================================================
# BUILD FINAL JSON OUTPUT
# =============================================================================

# OHLCV data list (only OHLCV, no extra fields)
ohlcv_data = []
for idx, row in daily_analysis.iterrows():
    ohlcv_data.append({
        "date": row['Date'],
        "open": float(row['Open']),
        "high": float(row['High']),
        "low": float(row['Low']),
        "close": float(row['Close']),
        "volume": int(row['Volume'])
    })

final_output = {
    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    "symbol": "GMRAIRPORT.NS",
    "company_name": "GMR Airports Ltd",
    
    "price_summary": {
        "current_price": float(current_price),
        "previous_close": float(previous_close),
        "change_percent": float(price_change_pct),
        "30_day_high": float(day_high),
        "30_day_low": float(day_low)
    },
    
    "returns_summary": {
        "30_day_stock_return_percent": float(stock_30d_return),
        "30_day_nifty_return_percent": float(nifty_30d_return),
        "30_day_sensex_return_percent": float(sensex_30d_return),
        "relative_strength_vs_nifty_percent": float(relative_strength_nifty)
    },
    
    "liquidity": {
        "avg_daily_volume": int(avg_volume),
        "avg_daily_value_cr": float(daily_analysis['Value_Traded_Cr'].mean()),
        "max_daily_volume": int(daily_analysis['Volume'].max()),
        "min_daily_volume": int(daily_analysis['Volume'].min()),
        "high_volume_days": int(days_high_liquidity),
        "low_volume_days": int(days_low_liquidity),
        "volume_stability_index": float(volume_stability),
        "total_traded_volume_30d": int(daily_analysis['Volume'].sum()),
        "total_traded_value_cr_30d": float(daily_analysis['Value_Traded_Cr'].sum())
    },
    
    "risk_metrics": {
        "beta_nifty": float(beta_nifty),
        "correlation_nifty": float(correlation_nifty),
        "beta_sensex": float(beta_sensex),
        "correlation_sensex": float(correlation_sensex),
        "volatility_30d_annualized_percent": float(volatility_30d),
        "max_drawdown_percent": float(max_drawdown),
        "alpha_nifty_percent": float(alpha_nifty_annualized),
        "alpha_sensex_percent": float(alpha_sensex_annualized),
        "sharpe_ratio": float(sharpe_ratio),
        "information_ratio": float(information_ratio),
        "tracking_error_percent": float(tracking_error),
        "avg_daily_return_percent": float(daily_analysis['Daily_Return'].mean()),
        "avg_intraday_range_percent": float(daily_analysis['Intraday_Range_Pct'].mean())
    },
    
    "trend_indicators": {
        "trend_5d_return_percent": float(trend_5d_return) if trend_5d_return else None,
        "trend_30d_return_percent": float(trend_30d_return),
        "price_stability_index": float(price_stability_index),
        "volatility_skew": float(volatility_skew)
    },
    
    "gap_risk": {
        "gap_up_days": int(gap_up_days),
        "gap_down_days": int(gap_down_days),
        "total_gap_days": int(gap_up_days + gap_down_days)
    },
    
    "ohlcv_data_30d": ohlcv_data
}

# Save to JSON
with open('gmr_stock_analysis.json', 'w') as f:
    json.dump(final_output, f, indent=2)

print(f"\n{'='*100}")
print(f"✅ Analysis complete! Data saved to 'gmr_stock_analysis.json'")
print(f"{'='*100}\n")
