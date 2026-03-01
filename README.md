# DTSignals — Professional Telegram Trading Bot

A professional-grade Telegram trading bot providing real-time technical analysis, options flow, pattern detection, and price alerts for US equities.

---

## Features

| Command | Description |
|---|---|
| `/stock TICKER` | Full analysis: price, volume, indicators, key levels, trend |
| `/chart TICKER [timeframe]` | Candlestick chart with pattern overlays and MA/VWAP |
| `/scan PATTERN` | Scan 100+ US stocks for a named chart pattern |
| `/options TICKER` | Options chain: volume, OI, P/C ratio, IV rank, GEX |
| `/flow TICKER` | Unusual options flow: sweeps, blocks, premium bias |
| `/volume TICKER` | Volume analysis: OBV, spikes, accumulation/distribution |
| `/alert TICKER TYPE` | Set persistent price/volume/gamma alerts |

### Supported Patterns (scanner & chart)
`breakout`, `h&s`, `inverse_hs`, `double_top`, `double_bottom`, `cup_handle`, `ascending_triangle`, `descending_triangle`, `flag` / `bull_flag`, `unusual_volume`

---

## Quick Start

### 1. Clone & install dependencies

```bash
git clone https://github.com/your-org/DTsignals.git
cd DTsignals
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set TELEGRAM_BOT_TOKEN (required)
# Optionally set POLYGON_API_KEY, TRADIER_API_KEY, etc.
```

### 3. Run the bot

```bash
python -m bot.main
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | — | Bot token from [@BotFather](https://t.me/BotFather) |
| `POLYGON_API_KEY` | ❌ | — | Polygon.io key (optional enrichment) |
| `TRADIER_API_KEY` | ❌ | — | Tradier key (optional) |
| `ALPHA_VANTAGE_API_KEY` | ❌ | — | Alpha Vantage key (optional) |
| `DATABASE_PATH` | ❌ | `./bot.db` | SQLite database file path |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`) |
| `SCAN_INTERVAL_MINUTES` | ❌ | `30` | How often the background scanner runs |

---

## Project Structure

```
bot/
├── main.py                  # Entry point, job scheduling
├── handlers.py              # Command handler registration
├── commands/
│   ├── stock.py             # /stock command
│   ├── chart.py             # /chart command
│   ├── scan.py              # /scan command
│   ├── options.py           # /options command
│   ├── flow.py              # /flow command
│   ├── volume.py            # /volume command
│   └── alert.py             # /alert command
├── services/
│   ├── data_service.py      # yfinance data fetching & technical indicators
│   ├── options_service.py   # Black-Scholes, IV rank, options chain, flow
│   ├── scanner_service.py   # Async stock universe scanner
│   ├── pattern_engine.py    # Chart pattern detection (9 patterns)
│   ├── chart_service.py     # mplfinance candlestick chart generation
│   └── alert_service.py     # Background alert checker
├── database/
│   └── db.py                # aiosqlite async database (alerts, cache, scan results)
└── utils/
    ├── formatters.py         # Price/volume/pct formatting helpers
    └── rate_limiter.py       # Async API rate limiter
```

---

## Architecture

- **Data layer**: [yfinance](https://github.com/ranaroussi/yfinance) as primary data source; Polygon.io supported via env key.
- **Pattern engine**: Uses `scipy.signal.argrelextrema` for peak/trough detection; implements 9 classical chart patterns with confidence scoring and volume confirmation.
- **Options analytics**: Black-Scholes Greeks, IV Rank/Percentile from rolling historical volatility, put/call ratio, gamma exposure (GEX), unusual flow detection.
- **Charts**: Dark-themed candlestick charts via `mplfinance` with MA20/MA50/MA200/VWAP overlays and pattern annotation lines (target, invalidation, neckline).
- **Database**: `aiosqlite` SQLite with tables for alerts, scan results, options flow, price cache, and user preferences.
- **Scheduling**: `python-telegram-bot` job queue runs the scanner every `SCAN_INTERVAL_MINUTES` and checks alerts every 60 seconds.

---

## Command Examples

```
/stock AAPL
/chart NVDA 1mo
/scan breakout
/scan cup_handle
/options SPY
/flow TSLA
/volume AMD
/alert AAPL breakout
/alert NVDA unusual_volume
```

---

## Requirements

- Python 3.10+
- See `requirements.txt` for full dependency list

---

## License

MIT
