---
name: stock-alerts
description: Monitor watchlist tickers and fire spoken alerts on significant price moves
user-invocable: true
---

# Stock Alerts

When triggered by the heartbeat `stock_check` task or when the user asks
about price moves:

1. Call `get_stock_price` for each ticker in the user's watchlist
   (default: AAPL, NVDA, BTC-USD, SPY — override from memory key `stock_watchlist`)
2. Compare to the previous check (stored in memory key `stock_last_prices`)
3. If any ticker moved ≥ 2.5% since last check, fire a one-sentence spoken alert
4. Update `stock_last_prices` in memory with the new prices

Alert format (spoken, one sentence per mover):
  "{TICKER} is up/down {X}% to ${price}."

If nothing has moved significantly, stay silent — do not say "all clear".
After alerting, call `show_stocks` to switch the HUD to the stocks panel.

## Example invocations
- "How are my stocks doing?"
- "Any big moves today?"
- Heartbeat task: `stock_check`
