# CSV Schema Documentation

## Overview

BloomFolio accepts Wealthsimple-like portfolio CSV exports. The parser normalizes column names using accepted aliases and validates data types.

## Required Columns

| Column | Type | Description |
|--------|------|-------------|
| `ticker` | string | Security symbol |
| `quantity` | decimal | Shares/units held |
| `currency` | string | `CAD` or `USD` |
| `account_name` | string | Account label |

## Optional Columns

| Column | Type | Description |
|--------|------|-------------|
| `security_name` | string | Human-readable name |
| `market_value` | decimal | Current market value |
| `book_cost` | decimal | Total cost basis |
| `average_cost` | decimal | Average cost per share |
| `current_price` | decimal | Current price per share |
| `asset_type` | string | `stock`, `etf`, `cash`, `crypto`, `bond`, `other` |
| `exchange` | string | TSX, NYSE, NASDAQ, etc. |
| `sector` | string | Sector classification |
| `country` | string | Issuer country |
| `portfolio_weight` | decimal | Portfolio weight percentage |
| `unrealized_gain_loss` | decimal | Absolute gain/loss |
| `unrealized_gain_loss_pct` | decimal | Percentage gain/loss |

## Aliases

The parser accepts common aliases for column names:

- **ticker**: symbol, security symbol, stock symbol
- **quantity**: qty, shares, units
- **market_value**: market value, current value, value
- **book_cost**: book cost, cost basis, acb
- **account_name**: account, account name, account type

## Example

```csv
ticker,security_name,quantity,currency,account_name,market_value,book_cost
VFV,Vanguard S&P 500 Index ETF,25,CAD,TFSA,3450.00,3100.00
AAPL,Apple Inc.,10,USD,Personal,1850.00,1600.00
```

## Validation Rules

1. Header row is required
2. Required columns must be present
3. Empty tickers are invalid
4. Quantities must be numeric and >= 0
5. Currency should be CAD or USD
6. Cash rows are accepted but not analyzed
