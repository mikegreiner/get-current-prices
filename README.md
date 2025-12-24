# get-current-prices

A command-line tool to get current USD prices for cryptocurrency symbols with optional price comparison.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Options](#options)
- [Examples](#examples)
- [Symbol Mappings](#symbol-mappings)
- [Price Sources](#price-sources)
- [Output Format](#output-format)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features

- **Multiple price sources**: DefiLlama API (primary, no rate limits) with CoinGecko fallback
- **Price comparison**: Compare current prices to provided historical prices
- **Flexible input**: Command-line arguments, CSV, JSON, or free-form text files
- **Smart filtering**: Filter by symbol and/or price direction (up/down/unchanged)
- **Sorting**: Sort by any column (symbol, price, change %, etc.)
- **Auto-mapping**: Automatically discovers and saves new symbol mappings
- **Validation**: Cross-checks prices from multiple sources to catch mapping errors
- **Quiet mode**: Clean output for scripting/automation

## Installation

### Clone the Repository

```bash
git clone https://github.com/mikegreiner/get-current-prices.git
cd get-current-prices
```

### Install Dependencies

Requires Python 3.7+ and the `requests` library:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install requests
```

### Make Script Executable (Optional)

```bash
chmod +x get_current_prices.py
```

Then you can run it directly:

```bash
./get_current_prices.py BTC SOL ETH
```

### Verify Installation

```bash
python get_current_prices.py --help
```

## Quick Start

```bash
# Get prices for symbols
python get_current_prices.py BTC SOL ETH

# From file with price comparison
python get_current_prices.py --file input/sample-symbol-and-prices.txt

# Filter and sort
python get_current_prices.py --file prices.txt -F up -S change_pct

# Quiet mode (for scripting)
python get_current_prices.py BTC ETH -q
```

## Usage

### Command-Line Symbols

```bash
# Space-separated
python get_current_prices.py BTC SOL ETH

# Comma-separated
python get_current_prices.py BTC,SOL,ETH
```

### File Input

The tool auto-detects file format (CSV, JSON, or free-form text):

```bash
python get_current_prices.py --file prices.csv
python get_current_prices.py --file prices.json
python get_current_prices.py --file prices.txt
```

### File Formats

**CSV:**
```csv
symbol,price,notes
BTC,45000.00,Bought on Coinbase
SOL,95.50,Purchased on Kraken
```

**JSON:**
```json
[
  {"symbol": "BTC", "price": 45000.00, "notes": "Bought on Coinbase"},
  {"symbol": "SOL", "price": 95.50, "notes": "Purchased on Kraken"}
]
```

**Free-form text:**
```
- BTC (Coinbase, $45,000.00)
- SOL (Kraken, $95.50)
- ETH (Coinbase $2,900.00)
```

## Options

- `-f, --file FILE`: Input file with symbols (CSV, JSON, or free-form text)
- `-j, --json`: Output results as JSON instead of formatted table
- `-q, --quiet`: Suppress all progress messages (only show results)
- `-s, --filter-symbol SYMBOLS`: Filter by symbol(s), comma-separated (e.g., BTC,ETH)
- `-F, --filter DIRECTION`: Filter by price direction: `up`, `down`, `unchanged`, or `all`
- `-S, --sort FIELD`: Sort by field: `symbol`, `provided_price`, `current_price`, `change_usd`, `change_pct`, `status`
- `--sort-reverse`: Reverse the sort order
- `-d, --delay SECONDS`: Delay between API calls (default: 0.5)
- `-h, --help`: Show help message

## Examples

### Basic Price Lookup

```bash
python get_current_prices.py BTC SOL ETH
```

### Price Comparison

```bash
# File contains symbols and prices
python get_current_prices.py --file input/sample-symbol-and-prices.txt
```

### Filtering

```bash
# Show only coins that went up
python get_current_prices.py --file prices.txt -F up

# Show only specific symbols
python get_current_prices.py --file prices.txt -s BTC,ETH,SOL

# Combine filters
python get_current_prices.py --file prices.txt -F up -s BTC,ETH
```

### Sorting

```bash
# Sort by percentage change (highest first)
python get_current_prices.py --file prices.txt -S change_pct

# Sort by percentage change (lowest first)
python get_current_prices.py --file prices.txt -S change_pct --sort-reverse

# Sort by current price
python get_current_prices.py --file prices.txt -S current_price
```

### JSON Output

```bash
python get_current_prices.py BTC SOL --json
```

### Quiet Mode

```bash
# Clean output for scripting
python get_current_prices.py BTC ETH -q
```

## Symbol Mappings

The tool uses `symbol_mappings.json` to map symbols to CoinGecko IDs. This file:

- Is automatically created on first run with default mappings
- Can be edited to add/modify/fix mappings
- Automatically grows as new symbols are used
- Falls back to hardcoded defaults if the file is missing

**To fix a wrong mapping:**
1. Edit `symbol_mappings.json`
2. Change the mapping: `"SYMBOL": "correct-coingecko-id"`
3. Save and run again

**New symbols** are automatically:
- Looked up via CoinGecko search API
- Validated by cross-checking prices from multiple sources
- Saved to `symbol_mappings.json` for future use

## Price Sources

1. **DefiLlama API** (primary)
   - No rate limits
   - Batch requests supported
   - Uses CoinGecko IDs
   - **Update frequency**: Prices are updated in near real-time (typically within 1-2 minutes)
   - Prices are aggregated from multiple exchanges

2. **CoinGecko API** (fallback)
   - Rate-limited (free tier: 10-50 calls/minute)
   - Used when DefiLlama doesn't have the price
   - Also used for symbol search
   - **Update frequency**: Prices are updated frequently (typically within 1-5 minutes)
   - Prices are aggregated from multiple exchanges

**Note**: Both services aggregate prices from multiple exchanges, so the prices you see are market averages, not from a single exchange. For most use cases, this provides accurate current market prices.

## Output Format

### Table Output (Default)

```
========================================================================================================================
PRICE COMPARISON
========================================================================================================================
Symbol     | Provided Price     | Current Price      | Change (USD)    | Change (%)   | Status              
------------------------------------------------------------------------------------------------------------------------
BTC        | $45,000.00         | $87,328.89         | $+42328.89      | +94.06%      | ↑ Up       
ETH        | $2,900.00          | $2,932.75          | $+32.75         | +1.13%       | ↑ Up       
========================================================================================================================

Found prices for 2 of 2 symbols
Compared 2 symbols with provided prices
```

### JSON Output

```json
{
  "timestamp": "2025-12-24 12:00:00",
  "prices": {
    "BTC": 87328.89,
    "ETH": 2932.75
  },
  "comparisons": {
    "BTC": {
      "provided_price": 45000.00,
      "current_price": 87328.89,
      "change_usd": 42328.89,
      "change_percent": 94.06,
      "status": "Up",
      "status_symbol": "↑"
    }
  }
}
```

## Status Indicators

- **↑ Up** (green): Price increased
- **↓ Down** (red): Price decreased
- **═ Unchanged**: Price essentially unchanged (<0.01% difference)

## Troubleshooting

### "ModuleNotFoundError: No module named 'requests'"

Install the required dependency:

```bash
pip install requests
```

Or use the requirements file:

```bash
pip install -r requirements.txt
```

### "Symbol not found" or Wrong Price

If a symbol returns the wrong price or isn't found:

1. **Check the mapping**: Look in `symbol_mappings.json` to see what CoinGecko ID is mapped
2. **Fix the mapping**: Edit `symbol_mappings.json` with the correct CoinGecko ID
3. **Validate**: The tool automatically validates new mappings by cross-checking prices

**Example**: If SYRUP shows the wrong price, check if it's mapped to `pancakeswap-token` (CAKE) instead of `syrup` (Maple Finance).

### Rate Limiting Errors

If you see rate limit errors from CoinGecko:

- The tool automatically retries with exponential backoff
- DefiLlama (primary source) has no rate limits
- For large symbol lists, use `-d` to increase delay between API calls:

```bash
python get_current_prices.py --file large_list.txt -d 1.0
```

### Price Validation Warnings

If you see warnings about price mismatches:

- This means CoinGecko and DefiLlama returned different prices
- The tool will skip mappings that fail validation
- Check if the CoinGecko ID is correct for the symbol

### File Format Issues

**CSV files**: Must have a `symbol` column. `price` and `notes` columns are optional.

**JSON files**: Can be either an array of objects or an object with symbol keys.

**Free-form text**: Must have the symbol at the start of each line (uppercase), followed by optional text and a price starting with `$`.

## Development

### Running Tests

The project uses `pytest` for testing. Install test dependencies:

```bash
pip install -r requirements.txt
```

Run all tests:

```bash
pytest tests/ -v
```

Run tests with coverage:

```bash
pytest tests/ --cov=get_current_prices --cov-report=term-missing
```

### Test Structure

Tests are organized by functionality:
- `test_price_lookup.py` - Price lookup and validation
- `test_file_parsing.py` - File format parsing (CSV, JSON, text)
- `test_formatting.py` - Price and change formatting
- `test_sorting.py` - Result sorting functionality

### Contributing

When contributing:
1. Add tests for new features
2. Ensure all tests pass: `pytest tests/ -v`
3. Maintain test coverage
4. Follow existing code style

## License

MIT
