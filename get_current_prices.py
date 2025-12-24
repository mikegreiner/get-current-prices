#!/usr/bin/env python3
"""
Get current USD prices for cryptocurrency symbols.

Features:
- Lookup current prices from command-line or file input
- Support for CSV, JSON, and free-form text file formats
- Price comparison: compare current prices to provided prices
- Uses DefiLlama API (no rate limits) with CoinGecko fallback

Usage:
    # Command-line symbols
    python get_current_prices.py BTC SOL ETH
    python get_current_prices.py BTC,SOL,ETH
    
    # From file (auto-detects format)
    python get_current_prices.py --file input/sample-symbol-and-prices.txt
    python get_current_prices.py --file prices.csv
    python get_current_prices.py --file prices.json
    
    # JSON output
    python get_current_prices.py --file prices.txt --json
"""

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests


class PriceLookup:
    """Handles cryptocurrency price lookups from multiple sources."""
    
    # Default symbol to CoinGecko ID mapping (fallback if file not found)
    DEFAULT_SYMBOLS = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'SOL': 'solana',
        'AVAX': 'avalanche-2',
        'BNB': 'binancecoin',
        'ADA': 'cardano',
        'XRP': 'ripple',
        'DOT': 'polkadot',
        'DOGE': 'dogecoin',
        'MATIC': 'matic-network',
        'LINK': 'chainlink',
        'UNI': 'uniswap',
        'LTC': 'litecoin',
        'ATOM': 'cosmos',
        'FIL': 'filecoin',
        'ETC': 'ethereum-classic',
        'XLM': 'stellar',
        'ALGO': 'algorand',
        'VET': 'vechain',
        'ICP': 'internet-computer',
        'THETA': 'theta-token',
        'EOS': 'eos',
        'AAVE': 'aave',
        'MKR': 'maker',
        'COMP': 'compound-governance-token',
        'YFI': 'yearn-finance',
        'SUSHI': 'sushi',
        'SNX': 'havven',
        'CRV': 'curve-dao-token',
        '1INCH': '1inch',
        'ENJ': 'enjincoin',
        'SAND': 'the-sandbox',
        'MANA': 'decentraland',
        'AXS': 'axie-infinity',
        'GALA': 'gala',
        'IMX': 'immutable-x',
        'ILV': 'illuvium',
        'RENDER': 'render-token',
        'SUPER': 'superfarm',
        'ONDO': 'ondo-finance',
        'AKT': 'akash-network',
        'BEAM': 'beam-2',
        'ATLAS': 'star-atlas',
        'AERO': 'aerodrome-finance',
        'PENGU': 'pudgy-penguins',
        'PRIME': 'echelon-prime',
        'WILD': 'wilder-world',
        'NOS': 'nosana',
        'SYRUP': 'syrup',  # Maple Finance (not PancakeSwap CAKE)
    }
    
    @staticmethod
    def _load_symbol_mappings(quiet: bool = False) -> Dict[str, str]:
        """
        Load symbol mappings from external JSON file, with fallback to defaults.
        Looks for symbol_mappings.json in the script directory.
        
        Args:
            quiet: If True, suppress output messages
        
        Returns:
            Dictionary mapping symbol to CoinGecko ID
        """
        # Try to load from external file
        script_dir = Path(__file__).parent
        mappings_file = script_dir / 'symbol_mappings.json'
        
        if mappings_file.exists():
            try:
                with open(mappings_file, 'r', encoding='utf-8') as f:
                    mappings = json.load(f)
                    if isinstance(mappings, dict):
                        if not quiet:
                            print(f"📋 Loaded {len(mappings)} symbol mappings from {mappings_file}", file=sys.stderr)
                        return mappings
                    else:
                        if not quiet:
                            print(f"⚠️  Invalid format in {mappings_file}, using defaults", file=sys.stderr)
            except (json.JSONDecodeError, IOError) as e:
                if not quiet:
                    print(f"⚠️  Error loading {mappings_file}: {e}, using defaults", file=sys.stderr)
        
        # Fallback to defaults
        return PriceLookup.DEFAULT_SYMBOLS.copy()
    
    def get_common_symbols(self, quiet: bool = False) -> Dict[str, str]:
        """Load symbol mappings (loads once, then caches)."""
        if not hasattr(self, '_common_symbols'):
            self._common_symbols = self._load_symbol_mappings(quiet=quiet)
        return self._common_symbols
    
    @property
    def COMMON_SYMBOLS(self) -> Dict[str, str]:
        """Lazy-load symbol mappings (loads once, then caches)."""
        if not hasattr(self, '_common_symbols'):
            self._common_symbols = self._load_symbol_mappings(quiet=False)
        return self._common_symbols
    
    def _save_symbol_mapping(self, symbol: str, coin_id: str, quiet: bool = False) -> bool:
        """
        Save a new symbol mapping to the external JSON file.
        
        Args:
            symbol: Cryptocurrency symbol (uppercase)
            coin_id: CoinGecko ID
            quiet: If True, suppress output messages
        
        Returns:
            True if saved successfully, False otherwise
        """
        script_dir = Path(__file__).parent
        mappings_file = script_dir / 'symbol_mappings.json'
        
        try:
            # Load existing mappings
            if mappings_file.exists():
                with open(mappings_file, 'r', encoding='utf-8') as f:
                    mappings = json.load(f)
            else:
                mappings = {}
            
            # Add new mapping
            mappings[symbol.upper()] = coin_id
            
            # Save back to file (sorted for readability)
            with open(mappings_file, 'w', encoding='utf-8') as f:
                json.dump(dict(sorted(mappings.items())), f, indent=2)
            
            if not quiet:
                print(f"💾 Added {symbol} → {coin_id} to symbol_mappings.json", file=sys.stderr)
            return True
            
        except (IOError, json.JSONDecodeError) as e:
            if not quiet:
                print(f"⚠️  Could not save mapping to {mappings_file}: {e}", file=sys.stderr)
            return False
    
    def __init__(self, quiet: bool = False):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Koinly-Price-Lookup/1.0'
        })
        self.quiet = quiet
        # Cache for symbol to CoinGecko ID mapping
        self.symbol_to_id_cache: Dict[str, str] = {}
        # Track which symbols were newly discovered (not in original mappings)
        self._new_symbols: Dict[str, str] = {}
        # Initialize cache with common symbols (loads from file or defaults)
        self.symbol_to_id_cache.update(self.get_common_symbols(quiet=quiet))
    
    def get_prices_defillama(self, symbols: List[str], max_retries: int = 3) -> Dict[str, Optional[float]]:
        """
        Get prices for multiple symbols from DefiLlama API (primary source, no rate limits).
        Uses CoinGecko IDs to query DefiLlama.
        
        Returns:
            Dictionary mapping symbol to price (or None if not found)
        """
        results = {}
        
        # Get CoinGecko IDs for all symbols
        coin_ids = {}
        for symbol in symbols:
            coin_id = self._get_coingecko_id(symbol)
            if coin_id:
                coin_ids[symbol] = coin_id
            else:
                results[symbol] = None
        
        if not coin_ids:
            return results
        
        # Build DefiLlama query string (format: coingecko:bitcoin,coingecko:ethereum)
        llama_ids = [f"coingecko:{coin_id}" for coin_id in coin_ids.values()]
        llama_ids_str = ','.join(llama_ids)
        
        for attempt in range(max_retries):
            try:
                url = "https://coins.llama.fi/prices/current/" + llama_ids_str
                
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                # DefiLlama returns data in format: {"coins": {"coingecko:bitcoin": {"price": 87384.0, ...}, ...}}
                coins = data.get('coins', {})
                
                # Map results back to symbols
                for symbol, coin_id in coin_ids.items():
                    llama_key = f"coingecko:{coin_id}"
                    if llama_key in coins and 'price' in coins[llama_key]:
                        results[symbol] = float(coins[llama_key]['price'])
                    else:
                        results[symbol] = None
                
                return results
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 1
                    print(f"⚠️  DefiLlama API error (attempt {attempt + 1}/{max_retries}): {e}", file=sys.stderr)
                    if attempt < max_retries - 1:
                        print(f"    Retrying in {wait_time} seconds...", file=sys.stderr)
                        time.sleep(wait_time)
                else:
                    print(f"⚠️  DefiLlama API error after {max_retries} attempts: {e}", file=sys.stderr)
                    # Set all remaining to None
                    for symbol in coin_ids.keys():
                        if symbol not in results:
                            results[symbol] = None
        
        return results
    
    def get_prices_coingecko_batch(self, symbols: List[str], max_retries: int = 3) -> Dict[str, Optional[float]]:
        """
        Get prices for multiple symbols in a batch from CoinGecko API.
        More efficient than individual requests and helps avoid rate limits.
        
        Returns:
            Dictionary mapping symbol to price (or None if not found)
        """
        results = {}
        
        # First, get CoinGecko IDs for all symbols
        coin_ids = {}
        for symbol in symbols:
            coin_id = self._get_coingecko_id(symbol)
            if coin_id:
                coin_ids[symbol] = coin_id
            else:
                results[symbol] = None
        
        if not coin_ids:
            return results
        
        # Batch request for all coin IDs at once
        coin_id_list = list(coin_ids.values())
        coin_id_str = ','.join(coin_id_list)
        
        for attempt in range(max_retries):
            try:
                url = "https://api.coingecko.com/api/v3/simple/price"
                params = {
                    'ids': coin_id_str,
                    'vs_currencies': 'usd'
                }
                
                response = self.session.get(url, params=params, timeout=15)
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    if attempt < max_retries - 1:
                        print(f"⚠️  Rate limited. Waiting {retry_after} seconds...", file=sys.stderr)
                        time.sleep(retry_after)
                        continue
                    else:
                        print(f"⚠️  Rate limit exceeded after {max_retries} attempts", file=sys.stderr)
                        break
                
                response.raise_for_status()
                data = response.json()
                
                # Map results back to symbols
                for symbol, coin_id in coin_ids.items():
                    if coin_id in data and 'usd' in data[coin_id]:
                        results[symbol] = float(data[coin_id]['usd'])
                    else:
                        results[symbol] = None
                
                return results
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    print(f"⚠️  API error (attempt {attempt + 1}/{max_retries}): {e}", file=sys.stderr)
                    print(f"    Retrying in {wait_time} seconds...", file=sys.stderr)
                    time.sleep(wait_time)
                else:
                    print(f"⚠️  CoinGecko API error after {max_retries} attempts: {e}", file=sys.stderr)
                    # Set all remaining to None
                    for symbol in coin_ids.keys():
                        if symbol not in results:
                            results[symbol] = None
        
        return results
    
    def get_price_coingecko(self, symbol: str) -> Optional[float]:
        """
        Get price from CoinGecko API (single symbol).
        Returns price in USD or None if not found.
        """
        results = self.get_prices_coingecko_batch([symbol])
        return results.get(symbol)
    
    def _validate_coin_id(self, symbol: str, coin_id: str, threshold: float = 0.20) -> bool:
        """
        Validate a CoinGecko ID by cross-checking prices from multiple sources.
        Returns True if prices are consistent, False if there's a significant discrepancy.
        
        Args:
            symbol: The symbol being validated
            coin_id: The CoinGecko ID to validate
            threshold: Maximum price difference percentage (default 20%) to consider valid
        
        Returns:
            True if validation passes, False otherwise
        """
        try:
            # Get price from CoinGecko
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {'ids': coin_id, 'vs_currencies': 'usd'}
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code != 200:
                return True  # Can't validate, assume OK
            data = response.json()
            cg_price = data.get(coin_id, {}).get('usd')
            if cg_price is None:
                return True  # No price available, can't validate
            
            # Get price from DefiLlama
            llama_url = f"https://coins.llama.fi/prices/current/coingecko:{coin_id}"
            response2 = self.session.get(llama_url, timeout=10)
            if response2.status_code != 200:
                return True  # Can't validate, assume OK
            data2 = response2.json()
            llama_price = data2.get('coins', {}).get(f'coingecko:{coin_id}', {}).get('price')
            if llama_price is None:
                return True  # No price available, can't validate
            
            # Compare prices
            if cg_price > 0 and llama_price > 0:
                price_diff = abs(cg_price - llama_price) / max(cg_price, llama_price)
                if price_diff > threshold:
                    # Note: This warning is always shown even in quiet mode as it indicates a problem
                    print(f"⚠️  Warning: Price mismatch for {symbol} ({coin_id}): CoinGecko=${cg_price:.6f}, DefiLlama=${llama_price:.6f} (diff: {price_diff*100:.1f}%)", file=sys.stderr)
                    return False
            
            return True
            
        except Exception:
            # If validation fails, assume OK (don't block lookup)
            return True
    
    def _get_coingecko_id(self, symbol: str, max_retries: int = 3, validate: bool = True) -> Optional[str]:
        """
        Get CoinGecko ID for a symbol.
        Uses cache if available, otherwise searches CoinGecko.
        Optionally validates the mapping by cross-checking prices from multiple sources.
        
        Args:
            symbol: Cryptocurrency symbol
            max_retries: Maximum number of retry attempts
            validate: If True, validate the mapping by checking prices from multiple sources
        """
        symbol_upper = symbol.upper()
        
        # Check cache first (includes common symbols)
        if symbol_upper in self.symbol_to_id_cache:
            return self.symbol_to_id_cache[symbol_upper]
        
        # Check common symbols mapping
        if symbol_upper in self.COMMON_SYMBOLS:
            coin_id = self.COMMON_SYMBOLS[symbol_upper]
            self.symbol_to_id_cache[symbol_upper] = coin_id
            return coin_id
        
        for attempt in range(max_retries):
            try:
                # Search CoinGecko for the symbol
                url = "https://api.coingecko.com/api/v3/search"
                params = {'query': symbol_upper}
                
                response = self.session.get(url, params=params, timeout=10)
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    if attempt < max_retries - 1:
                        time.sleep(retry_after)
                        continue
                    else:
                        return None
                
                response.raise_for_status()
                data = response.json()
                
                # Look for exact symbol match in coins
                if 'coins' in data and data['coins']:
                    for coin in data['coins']:
                        if coin.get('symbol', '').upper() == symbol_upper:
                            coin_id = coin.get('id')
                            if coin_id:
                                # Validate the mapping if requested
                                if validate and not self._validate_coin_id(symbol_upper, coin_id):
                                    # If validation fails, continue to next match
                                    if not self.quiet:
                                        print(f"⚠️  Skipping {coin_id} for {symbol_upper} due to price validation failure", file=sys.stderr)
                                    continue
                                
                                # Cache it
                                self.symbol_to_id_cache[symbol_upper] = coin_id
                                
                                # Track as new symbol (not in original mappings) and save to file
                                if symbol_upper not in self.get_common_symbols(quiet=self.quiet):
                                    self._new_symbols[symbol_upper] = coin_id
                                    self._save_symbol_mapping(symbol_upper, coin_id, quiet=self.quiet)
                                
                                return coin_id
                
                return None
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    time.sleep(wait_time)
                else:
                    return None
        
        return None
    
    def get_price_dexscreener(self, symbol: str) -> Optional[float]:
        """
        Get price from DexScreener API (fallback).
        Note: DexScreener works better with contract addresses than symbols.
        This is a last resort fallback.
        """
        # DexScreener doesn't have a good symbol-based API
        # This would require contract addresses, which we don't have
        # For now, return None - we can enhance this later if needed
        return None
    
    def get_price(self, symbol: str, retry_delay: float = 1.0) -> Optional[float]:
        """
        Get current USD price for a symbol.
        Tries multiple sources with retry logic.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            retry_delay: Delay between retries in seconds (not used for DefiLlama)
            
        Returns:
            Price in USD or None if not found
        """
        symbol = symbol.strip().upper()
        
        # Try DefiLlama first (no rate limits)
        results = self.get_prices_defillama([symbol])
        price = results.get(symbol)
        if price is not None:
            return price
        
        # Fallback to CoinGecko if DefiLlama fails
        time.sleep(retry_delay)
        price = self.get_price_coingecko(symbol)
        if price is not None:
            return price
        
        return None


def parse_freeform_text(file_path: Path) -> List[Tuple[str, Optional[float], str]]:
    """
    Parse free-form text file with symbols and optional prices.
    Returns list of (symbol, provided_price, notes) tuples.
    
    Handles formats like:
    - AERO (Coinbase, $0.4820)
    - ETH (Coinbase $2,918.5698)
    - FIL (Kraken, after unstaking, $1.3424)
    """
    results = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Try to extract symbol and price
            # Pattern: symbol followed by optional text and $price
            # Examples:
            # - AERO (Coinbase, $0.4820)
            # - ETH (Coinbase $2,918.5698)
            # - BEAM (Kraken, $.00269)
            
            # First, try to find a price (starts with $, may have commas, may start with .)
            # Handles formats like: $0.00269, $.00269, $2,918.57
            price_match = re.search(r'\$([\d,]*\.?\d+)', line)
            provided_price = None
            if price_match:
                price_str = price_match.group(1).replace(',', '')
                # Handle missing leading zero (e.g., ".00269" -> "0.00269")
                if price_str.startswith('.'):
                    price_str = '0' + price_str
                try:
                    provided_price = float(price_str)
                except ValueError:
                    pass
            
            # Extract symbol (uppercase alphanumeric, typically at start of line or after -)
            # Remove leading - or * if present
            line_clean = line.lstrip('-* ').strip()
            
            # Symbol is typically the first word (uppercase)
            symbol_match = re.match(r'^([A-Z0-9]+)', line_clean)
            if symbol_match:
                symbol = symbol_match.group(1).upper()
                # Notes are everything after the symbol
                notes = line_clean[len(symbol):].strip()
                results.append((symbol, provided_price, notes))
            else:
                # If no clear symbol, try to extract any uppercase word
                words = line_clean.split()
                for word in words:
                    # Remove punctuation
                    word_clean = re.sub(r'[^\w]', '', word).upper()
                    if word_clean and word_clean.isalnum() and len(word_clean) >= 2:
                        # Check if it looks like a crypto symbol (2-10 chars, mostly uppercase)
                        if word_clean.isupper() or (word_clean[0].isupper() and len(word_clean) <= 10):
                            notes = line_clean.replace(word, '').strip()
                            results.append((word_clean, provided_price, notes))
                            break
    
    return results


def parse_csv_file(file_path: Path) -> List[Tuple[str, Optional[float], str]]:
    """
    Parse CSV file with symbols and optional prices.
    Expected format:
    symbol,price,notes
    BTC,45000.00,Bought on Coinbase
    SOL,95.50,
    """
    results = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = row.get('symbol', '').strip().upper()
            if not symbol:
                continue
            
            price_str = row.get('price', '').strip()
            provided_price = None
            if price_str:
                try:
                    # Remove $ and commas
                    price_clean = price_str.replace('$', '').replace(',', '').strip()
                    provided_price = float(price_clean)
                except ValueError:
                    pass
            
            notes = row.get('notes', '').strip()
            results.append((symbol, provided_price, notes))
    
    return results


def parse_json_file(file_path: Path) -> List[Tuple[str, Optional[float], str]]:
    """
    Parse JSON file with symbols and optional prices.
    Expected formats:
    [{"symbol": "BTC", "price": 45000.00, "notes": "..."}, ...]
    or
    {"BTC": {"price": 45000.00, "notes": "..."}, ...}
    """
    results = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        # Array format
        for item in data:
            if isinstance(item, dict):
                symbol = item.get('symbol', '').strip().upper()
                if not symbol:
                    continue
                provided_price = item.get('price')
                if provided_price is not None:
                    try:
                        provided_price = float(provided_price)
                    except (ValueError, TypeError):
                        provided_price = None
                notes = item.get('notes', '').strip()
                results.append((symbol, provided_price, notes))
    elif isinstance(data, dict):
        # Object format
        for symbol, info in data.items():
            symbol = symbol.strip().upper()
            if not symbol:
                continue
            
            if isinstance(info, dict):
                provided_price = info.get('price')
                if provided_price is not None:
                    try:
                        provided_price = float(provided_price)
                    except (ValueError, TypeError):
                        provided_price = None
                notes = info.get('notes', '').strip()
            elif isinstance(info, (int, float)):
                # Simple format: {"BTC": 45000.00}
                provided_price = float(info)
                notes = ''
            else:
                continue
            
            results.append((symbol, provided_price, notes))
    
    return results


def parse_input_file(file_path: Path) -> List[Tuple[str, Optional[float], str]]:
    """
    Parse input file, auto-detecting format (CSV, JSON, or free-form text).
    Returns list of (symbol, provided_price, notes) tuples.
    """
    suffix = file_path.suffix.lower()
    
    if suffix == '.csv':
        return parse_csv_file(file_path)
    elif suffix == '.json':
        return parse_json_file(file_path)
    else:
        # Assume free-form text
        return parse_freeform_text(file_path)


def format_price(price: float) -> str:
    """
    Format price with appropriate decimal places based on value.
    Shows enough precision to be meaningful while avoiding excessive digits.
    Removes trailing zeros but keeps at least 2 decimals for prices >= $1.
    """
    abs_price = abs(price)
    
    # Determine appropriate precision
    if abs_price >= 1000:
        # Large prices: 2 decimals, with thousands separator
        return f"${price:,.2f}"
    elif abs_price >= 10:
        # Medium-large prices: 2 decimals
        return f"${price:.2f}"
    elif abs_price >= 1:
        # Medium prices: 4 decimals, but remove trailing zeros (keep min 2)
        formatted = f"${price:.4f}"
        # Remove trailing zeros but ensure at least 2 decimal places
        if '.' in formatted:
            parts = formatted.split('.')
            if len(parts) == 2:
                decimal = parts[1].rstrip('0')
                if len(decimal) < 2:
                    decimal = decimal.ljust(2, '0')  # Keep at least 2 decimals
                return f"${parts[0].lstrip('$')}.{decimal}"
        return formatted
    elif abs_price >= 0.1:
        # Small prices: 4 decimals, remove trailing zeros
        formatted = f"${price:.4f}"
        return formatted.rstrip('0').rstrip('.')
    elif abs_price >= 0.01:
        # Smaller prices: 6 decimals, remove trailing zeros
        formatted = f"${price:.6f}"
        return formatted.rstrip('0').rstrip('.')
    elif abs_price >= 0.001:
        # Very small prices: 8 decimals, remove trailing zeros
        formatted = f"${price:.8f}"
        return formatted.rstrip('0').rstrip('.')
    else:
        # Extremely small prices: 10 decimals, remove trailing zeros
        formatted = f"${price:.10f}"
        return formatted.rstrip('0').rstrip('.')


def format_change(change: float, reference_price: float) -> str:
    """
    Format price change with appropriate precision.
    Shows enough precision to see meaningful differences based on both
    absolute value and relative to the reference price.
    
    Args:
        change: Absolute change in USD
        reference_price: Reference price (for determining precision)
    """
    abs_change = abs(change)
    abs_ref = abs(reference_price)
    
    # Calculate relative change to determine precision needs
    if abs_ref > 0:
        change_ratio = abs_change / abs_ref
    else:
        change_ratio = 1.0
    
    # Determine precision based on absolute value, but ensure we can see
    # meaningful differences even for small relative changes
    if abs_change >= 1000:
        formatted = f"${change:+,.2f}"
    elif abs_change >= 100:
        formatted = f"${change:+.2f}"
    elif abs_change >= 10:
        formatted = f"${change:+.2f}"
    elif abs_change >= 1:
        # For changes between $1-$10, show 2-4 decimals depending on relative size
        if change_ratio < 0.01:  # Very small relative change (< 1%)
            formatted = f"${change:+.4f}"
        else:
            formatted = f"${change:+.2f}"
    elif abs_change >= 0.1:
        # For changes between $0.1-$1, show 4 decimals
        formatted = f"${change:+.4f}"
    elif abs_change >= 0.01:
        # For changes between $0.01-$0.1, show 4-6 decimals
        if change_ratio < 0.001:  # Tiny relative change
            formatted = f"${change:+.6f}"
        else:
            formatted = f"${change:+.4f}"
    elif abs_change >= 0.001:
        # For changes between $0.001-$0.01, show 6 decimals
        formatted = f"${change:+.6f}"
    elif abs_change >= 0.0001:
        # For changes between $0.0001-$0.001, show 6-8 decimals
        if change_ratio < 0.0001:  # Extremely small relative change
            formatted = f"${change:+.8f}"
        else:
            formatted = f"${change:+.6f}"
    elif abs_change >= 0.00001:
        # For changes between $0.00001-$0.0001, show 8 decimals
        formatted = f"${change:+.8f}"
    else:
        # Extremely small changes: up to 10 decimals
        formatted = f"${change:+.10f}"
    
    # Remove trailing zeros but keep at least one decimal place if non-zero
    if '.' in formatted:
        # Keep the sign and $, remove trailing zeros
        parts = formatted.split('.')
        if len(parts) == 2:
            decimal_part = parts[1].rstrip('0')
            if decimal_part:
                formatted = f"${change:+.{len(decimal_part)}f}"
            else:
                # All zeros after decimal, show as integer
                formatted = f"${change:+.0f}"
    
    return formatted


def calculate_change(current: float, provided: float) -> Tuple[float, float, str, str]:
    """
    Calculate price change.
    Returns: (absolute_change, percent_change, status_symbol, status_text)
    """
    absolute_change = current - provided
    percent_change = (absolute_change / provided) * 100 if provided > 0 else 0.0
    
    if abs(percent_change) < 0.01:  # Essentially equal
        status_symbol = "═"
        status_text = "Unchanged"
    elif percent_change > 0:
        status_symbol = "↑"
        status_text = "Up"
    else:
        status_symbol = "↓"
        status_text = "Down"
    
    return absolute_change, percent_change, status_symbol, status_text


def sort_results(results: List[Tuple[str, Optional[float]]], sort_by: str, provided_prices: Dict[str, float] = None, reverse: bool = False) -> List[Tuple[str, Optional[float]]]:
    """
    Sort results by the specified field.
    
    Args:
        results: List of (symbol, price) tuples
        sort_by: Field to sort by: 'symbol', 'provided_price', 'current_price', 'change_usd', 'change_pct', 'status'
        provided_prices: Dictionary of provided prices (needed for some sorts)
        reverse: If True, sort in descending order
        
    Returns:
        Sorted list of (symbol, price) tuples
    """
    if not results:
        return results
    
    # Build list with sort keys
    sortable = []
    for symbol, current_price in results:
        provided_price = provided_prices.get(symbol) if provided_prices else None
        
        if sort_by == 'symbol':
            sort_key = symbol.upper()
        elif sort_by == 'provided_price':
            sort_key = provided_price if provided_price is not None else float('-inf')
        elif sort_by == 'current_price':
            sort_key = current_price if current_price is not None else float('-inf')
        elif sort_by == 'change_usd':
            if current_price is not None and provided_price is not None:
                abs_change, _, _, _ = calculate_change(current_price, provided_price)
                sort_key = abs_change
            else:
                sort_key = float('-inf')
        elif sort_by == 'change_pct':
            if current_price is not None and provided_price is not None:
                _, pct_change, _, _ = calculate_change(current_price, provided_price)
                sort_key = pct_change
            else:
                sort_key = float('-inf')
        elif sort_by == 'status':
            if current_price is not None and provided_price is not None:
                _, _, _, status_text = calculate_change(current_price, provided_price)
                # Order: Up, Down, Unchanged
                status_order = {'Up': 0, 'Down': 1, 'Unchanged': 2}
                sort_key = status_order.get(status_text, 3)
            else:
                sort_key = 999  # Put missing at end
        else:
            sort_key = symbol.upper()  # Default to symbol
        
        sortable.append((sort_key, symbol, current_price))
    
    # Sort: default reverse for numeric fields (highest first), forward for symbol/status
    if sort_by in ['change_usd', 'change_pct', 'provided_price', 'current_price']:
        # For numeric fields, reverse=True means descending (highest first)
        sortable.sort(key=lambda x: x[0], reverse=(not reverse if reverse else True))
    else:
        # For symbol/status, reverse means reverse alphabetical/order
        sortable.sort(key=lambda x: x[0], reverse=reverse)
    
    return [(symbol, price) for _, symbol, price in sortable]


def print_price_table(results: List[Tuple[str, Optional[float]]], compare_mode: bool = False, provided_prices: Dict[str, float] = None, filter_direction: Optional[str] = None, filter_symbols: Optional[List[str]] = None, sort_by: str = 'symbol', sort_reverse: bool = False, quiet: bool = False):
    """
    Print price results in a formatted table.
    
    Args:
        results: List of (symbol, price) tuples
        compare_mode: Whether to show comparison mode
        provided_prices: Dictionary of provided prices for comparison
        filter_direction: Filter by direction: 'up', 'down', 'unchanged', or None for all
        filter_symbols: List of symbols to filter by (case-insensitive)
        sort_by: Field to sort by: 'symbol', 'provided_price', 'current_price', 'change_usd', 'change_pct', 'status'
        sort_reverse: If True, reverse the sort order
    """
    # Filter results by symbols if specified
    if filter_symbols:
        symbol_set = {s.upper() for s in filter_symbols}
        results = [(symbol, price) for symbol, price in results if symbol.upper() in symbol_set]
    
    # Filter results by direction if filter is specified and we're in compare mode
    if compare_mode and provided_prices and filter_direction and filter_direction.lower() != 'all':
        filtered_results = []
        for symbol, current_price in results:
            provided_price = provided_prices.get(symbol)
            if current_price is not None and provided_price is not None:
                _, _, _, status_text = calculate_change(current_price, provided_price)
                if status_text.lower() == filter_direction.lower():
                    filtered_results.append((symbol, current_price))
        results = filtered_results
    
    # Sort results
    results = sort_results(results, sort_by, provided_prices, sort_reverse)
    
    if compare_mode and provided_prices:
        if not quiet:
            print()
        print("=" * 120)
        print("PRICE COMPARISON")
        print("=" * 120)
        print(f"{'Symbol':<10} | {'Provided Price':<18} | {'Current Price':<18} | {'Change (USD)':<15} | {'Change (%)':<12} | {'Status':<20}")
        print("-" * 120)
        
        for symbol, current_price in results:
            provided_price = provided_prices.get(symbol)
            
            if current_price is None:
                status_display = "❌ Not found"
                current_str = "N/A"
                change_str = "N/A"
                pct_str = "N/A"
            elif provided_price is None:
                status_display = "✅ Found"
                current_str = format_price(current_price)
                change_str = "N/A"
                pct_str = "N/A"
            else:
                abs_change, pct_change, status_symbol, status_text = calculate_change(current_price, provided_price)
                # Color code: green for up, red for down, default for unchanged
                if status_text == "Up":
                    status_display = f"\033[92m{status_symbol}\033[0m {status_text}"  # Green
                elif status_text == "Down":
                    status_display = f"\033[91m{status_symbol}\033[0m {status_text}"  # Red
                else:
                    status_display = f"{status_symbol} {status_text}"  # Default color
                current_str = format_price(current_price)
                # Use smart formatting for change based on reference price
                change_str = format_change(abs_change, provided_price)
                # Format percentage with appropriate precision
                if abs(pct_change) >= 100:
                    pct_str = f"{pct_change:+.1f}%"
                elif abs(pct_change) >= 10:
                    pct_str = f"{pct_change:+.2f}%"
                elif abs(pct_change) >= 1:
                    pct_str = f"{pct_change:+.2f}%"
                else:
                    pct_str = f"{pct_change:+.3f}%"
            
            provided_str = format_price(provided_price) if provided_price is not None else "N/A"
            print(f"{symbol:<10} | {provided_str:<18} | {current_str:<18} | {change_str:<15} | {pct_str:<12} | {status_display:<20}")
        
        print("=" * 120)
        
        # Summary
        found = sum(1 for _, price in results if price is not None)
        total = len(results)
        compared = sum(1 for s in results if s[0] in provided_prices and provided_prices[s[0]] is not None and s[1] is not None)
        
        filter_notes = []
        if filter_direction:
            filter_notes.append(f"direction: {filter_direction}")
        if filter_symbols:
            filter_notes.append(f"symbols: {','.join(filter_symbols)}")
        filter_note = f" (filtered: {', '.join(filter_notes)})" if filter_notes else ""
        # Summary is always shown (not suppressed in quiet mode)
        print(f"\nFound prices for {found} of {total} symbols{filter_note}")
        if compared > 0:
            print(f"Compared {compared} symbols with provided prices")
    else:
        if not quiet:
            print()
        print("=" * 70)
        print("CURRENT PRICES (USD)")
        print("=" * 70)
        print(f"{'Symbol':<10} | {'Price (USD)':<20} | {'Status':<10}")
        print("-" * 70)
        
        for symbol, price in results:
            if price is not None:
                status = "✅"
                price_str = format_price(price)
            else:
                status = "❌ Not found"
                price_str = "N/A"
            
            print(f"{symbol:<10} | {price_str:<20} | {status:<10}")
        
        print("=" * 70)
        
        # Summary (always shown, not suppressed in quiet mode)
        found = sum(1 for _, price in results if price is not None)
        total = len(results)
        print(f"\nFound prices for {found} of {total} symbols")


def main():
    parser = argparse.ArgumentParser(
        prog='get_current_prices.py',
        description='Get current USD prices for cryptocurrency symbols',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Command-line symbols
  %(prog)s BTC SOL ETH
  %(prog)s BTC,SOL,ETH
  
  # From file (auto-detects CSV, JSON, or free-form text)
  %(prog)s -f input/sample-symbol-and-prices.txt
  %(prog)s --file prices.csv
  %(prog)s --file prices.json
  
  # JSON output
  %(prog)s BTC SOL -j
  %(prog)s -f prices.txt --json
  
  # With delay between API calls
  %(prog)s -f prices.txt -d 1.0
  
  # Filter by price direction (only shows coins that went up/down/unchanged)
  %(prog)s -f prices.txt -F up
  %(prog)s -f prices.txt --filter down
  %(prog)s -f prices.txt -F unchanged
  
  # Filter by symbol(s)
  %(prog)s -f prices.txt -s BTC,ETH
  %(prog)s -f prices.txt --filter-symbol SOL
  
  # Combine filters (symbol and direction)
  %(prog)s -f prices.txt -F up -s BTC,ETH,SOL
  
  # Sort results
  %(prog)s -f prices.txt -S change_pct
  %(prog)s -f prices.txt --sort change_usd --sort-reverse
        """
    )
    
    parser.add_argument(
        'symbols',
        nargs='*',
        metavar='SYMBOL',
        help='Cryptocurrency symbols (space-separated or comma-separated). Ignored if --file is used.'
    )
    
    parser.add_argument(
        '-f', '--file',
        type=Path,
        metavar='FILE',
        dest='file',
        help='Input file with symbols (CSV, JSON, or free-form text). If file contains prices, they will be compared to current prices.'
    )
    
    parser.add_argument(
        '-j', '--json',
        action='store_true',
        dest='json',
        help='Output results as JSON instead of formatted table'
    )
    
    parser.add_argument(
        '-d', '--delay',
        type=float,
        default=0.5,
        metavar='SECONDS',
        dest='delay',
        help='Delay between API calls in seconds (default: 0.5)'
    )
    
    parser.add_argument(
        '-F', '--filter',
        type=str,
        choices=['up', 'down', 'unchanged', 'all'],
        metavar='DIRECTION',
        dest='filter_direction',
        help='Filter results by price direction: up, down, unchanged, or all. Only applies when comparing prices (file with provided prices).'
    )
    
    parser.add_argument(
        '-s', '--filter-symbol',
        type=str,
        metavar='SYMBOLS',
        dest='filter_symbols',
        help='Filter results by symbol(s). Accepts comma-separated list (e.g., BTC,ETH,SOL). Case-insensitive. Can be combined with --filter direction. If provided, only these symbols will be looked up (efficiency optimization).'
    )
    
    parser.add_argument(
        '-S', '--sort',
        type=str,
        choices=['symbol', 'provided_price', 'current_price', 'change_usd', 'change_pct', 'status'],
        default='symbol',
        metavar='FIELD',
        dest='sort_by',
        help='Sort results by field: symbol (default), provided_price, current_price, change_usd, change_pct, status. Numeric fields default to descending (highest first).'
    )
    
    parser.add_argument(
        '--sort-reverse',
        action='store_true',
        dest='sort_reverse',
        help='Reverse the sort order. For numeric fields, this makes ascending (lowest first) instead of descending.'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        dest='quiet',
        help='Suppress all progress messages and warnings. Only output the results table or JSON.'
    )
    
    args = parser.parse_args()
    
    # Parse input: either from file or command-line arguments
    input_data: List[Tuple[str, Optional[float], str]] = []
    provided_prices: Dict[str, float] = {}
    
    if args.file:
        if not args.file.exists():
            if not args.quiet:
                print(f"❌ File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        
        if not args.quiet:
            print(f"📄 Reading symbols from file: {args.file}")
        input_data = parse_input_file(args.file)
        
        # Extract symbols and provided prices
        unique_symbols = []
        seen = set()
        for symbol, provided_price, notes in input_data:
            symbol_upper = symbol.upper()
            if symbol_upper not in seen:
                seen.add(symbol_upper)
                unique_symbols.append(symbol_upper)
                if provided_price is not None:
                    provided_prices[symbol_upper] = provided_price
        
        if not unique_symbols:
            if not args.quiet:
                print("❌ No valid symbols found in file", file=sys.stderr)
            sys.exit(1)
        
        if not args.quiet:
            print(f"   Found {len(unique_symbols)} symbol(s)")
            if provided_prices:
                print(f"   Found {len(provided_prices)} provided price(s) for comparison")
    
    else:
        # Parse symbols from command-line (handle both space-separated and comma-separated)
        if not args.symbols:
            parser.print_help()
            sys.exit(1)
        
        symbols = []
        for arg in args.symbols:
            if ',' in arg:
                symbols.extend([s.strip() for s in arg.split(',')])
            else:
                symbols.append(arg.strip())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_symbols = []
        for symbol in symbols:
            symbol_upper = symbol.upper()
            if symbol_upper not in seen:
                seen.add(symbol_upper)
                unique_symbols.append(symbol_upper)
        
        if not unique_symbols:
            if not args.quiet:
                print("❌ No valid symbols provided", file=sys.stderr)
            sys.exit(1)
    
    # Parse filter symbols if provided (for efficiency - only lookup requested symbols)
    filter_symbols_list = None
    if args.filter_symbols:
        filter_symbols_list = [s.strip().upper() for s in args.filter_symbols.split(',') if s.strip()]
        
        # If filter_symbols is provided, only lookup those symbols for efficiency
        if filter_symbols_list:
            symbol_set = set(filter_symbols_list)
            original_count = len(unique_symbols)
            unique_symbols = [s for s in unique_symbols if s.upper() in symbol_set]
            if not unique_symbols:
                if not args.quiet:
                    print(f"❌ No symbols from filter list found in input. Filter: {', '.join(filter_symbols_list)}", file=sys.stderr)
                sys.exit(1)
            if not args.quiet:
                print(f"🔍 Filtering to {len(unique_symbols)} symbol(s) from {original_count} total (efficiency optimization)")
    
    if not args.quiet:
        print(f"🔍 Looking up prices for {len(unique_symbols)} symbol(s): {', '.join(unique_symbols)}")
    
    # Lookup prices using batch API for efficiency
    lookup = PriceLookup(quiet=args.quiet)
    
    # Get CoinGecko IDs for symbols not in common mapping
    if not args.quiet:
        print("\n📋 Mapping symbols to CoinGecko IDs...")
    symbols_needing_search = []
    for symbol in unique_symbols:
        coin_id = lookup._get_coingecko_id(symbol, validate=not args.quiet)
        if not coin_id:
            symbols_needing_search.append(symbol)
    
    # Only search for symbols not in common mapping (with rate limiting)
    if symbols_needing_search and not args.quiet:
        print(f"   Searching for {len(symbols_needing_search)} symbol(s) not in common mapping...")
    for i, symbol in enumerate(symbols_needing_search):
        if i > 0 and i % 3 == 0:  # Rate limit: wait every 3 symbols
            time.sleep(args.delay * 3)
        lookup._get_coingecko_id(symbol, validate=not args.quiet)
    
    # Batch fetch prices (DefiLlama primary, no rate limits)
    if not args.quiet:
        print("\n💰 Fetching current prices from DefiLlama (batch request, no rate limits)...")
    price_dict = lookup.get_prices_defillama(unique_symbols)
    
    # Fallback to CoinGecko for any symbols not found
    missing_symbols = [s for s, p in price_dict.items() if p is None]
    if missing_symbols:
        if not args.quiet:
            print(f"   {len(missing_symbols)} symbol(s) not found in DefiLlama, trying CoinGecko...")
        time.sleep(args.delay)
        coingecko_prices = lookup.get_prices_coingecko_batch(missing_symbols)
        # Update price_dict with CoinGecko results
        for symbol, price in coingecko_prices.items():
            if price is not None:
                price_dict[symbol] = price
    
    # Convert to list of tuples for display
    results = [(symbol, price_dict.get(symbol)) for symbol in unique_symbols]
    
    # Note: filter_symbols_list was already parsed earlier and used to filter unique_symbols
    # So at this point, results already only contain the filtered symbols
    # We still need filter_symbols_list for the display function to show the filter note
    
    # Output results
    if args.json:
        # Apply symbol filter first
        filtered_results = results
        if filter_symbols_list:
            symbol_set = set(filter_symbols_list)
            filtered_results = [(symbol, price) for symbol, price in results if symbol.upper() in symbol_set]
        
        # Apply direction filter if specified and in compare mode
        if args.filter_direction and provided_prices and args.filter_direction.lower() != 'all':
            direction_filtered = []
            for symbol, current_price in filtered_results:
                provided_price = provided_prices.get(symbol)
                if current_price is not None and provided_price is not None:
                    _, _, _, status_text = calculate_change(current_price, provided_price)
                    if status_text.lower() == args.filter_direction.lower():
                        direction_filtered.append((symbol, current_price))
            filtered_results = direction_filtered
        
        output = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'prices': {
                symbol: price if price is not None else None
                for symbol, price in filtered_results
            }
        }
        
        # Add comparison data if provided prices exist
        if provided_prices:
            output['comparisons'] = {}
            for symbol, current_price in filtered_results:
                if symbol in provided_prices and current_price is not None:
                    provided_price = provided_prices[symbol]
                    abs_change, pct_change, status_symbol, status_text = calculate_change(current_price, provided_price)
                    output['comparisons'][symbol] = {
                        'provided_price': provided_price,
                        'current_price': current_price,
                        'change_usd': abs_change,
                        'change_percent': pct_change,
                        'status': status_text,
                        'status_symbol': status_symbol
                    }
        
        # Sort JSON output if needed (convert to list, sort, convert back)
        if args.sort_by != 'symbol' or args.sort_reverse:
            # For JSON, we need to sort the comparisons dict
            if 'comparisons' in output and output['comparisons']:
                sorted_items = []
                for symbol, current_price in results:
                    if symbol in output['comparisons']:
                        comp = output['comparisons'][symbol]
                        if args.sort_by == 'symbol':
                            sort_key = symbol.upper()
                        elif args.sort_by == 'provided_price':
                            sort_key = comp.get('provided_price', float('-inf'))
                        elif args.sort_by == 'current_price':
                            sort_key = comp.get('current_price', float('-inf'))
                        elif args.sort_by == 'change_usd':
                            sort_key = comp.get('change_usd', float('-inf'))
                        elif args.sort_by == 'change_pct':
                            sort_key = comp.get('change_percent', float('-inf'))
                        elif args.sort_by == 'status':
                            status_order = {'Up': 0, 'Down': 1, 'Unchanged': 2}
                            sort_key = status_order.get(comp.get('status', ''), 3)
                        else:
                            sort_key = symbol.upper()
                        sorted_items.append((sort_key, symbol, comp))
                
                # Apply sort
                if args.sort_by in ['change_usd', 'change_pct', 'provided_price', 'current_price']:
                    sorted_items.sort(key=lambda x: x[0], reverse=(not args.sort_reverse if args.sort_reverse else True))
                else:
                    sorted_items.sort(key=lambda x: x[0], reverse=args.sort_reverse)
                
                # Rebuild comparisons dict in sorted order
                output['comparisons'] = {symbol: comp for _, symbol, comp in sorted_items}
        
        print(json.dumps(output, indent=2))
    else:
        print_price_table(results, compare_mode=bool(provided_prices), provided_prices=provided_prices, filter_direction=args.filter_direction, filter_symbols=filter_symbols_list, sort_by=args.sort_by, sort_reverse=args.sort_reverse, quiet=args.quiet)


if __name__ == "__main__":
    main()
