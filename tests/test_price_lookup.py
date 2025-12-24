"""
Tests for PriceLookup class and price fetching functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from get_current_prices import PriceLookup


class TestPriceLookup:
    """Test PriceLookup class."""
    
    def test_common_symbols_loaded(self):
        """Test that common symbols are loaded."""
        lookup = PriceLookup(quiet=True)
        assert 'BTC' in lookup.COMMON_SYMBOLS
        assert 'ETH' in lookup.COMMON_SYMBOLS
        assert lookup.COMMON_SYMBOLS['BTC'] == 'bitcoin'
    
    def test_get_coingecko_id_from_cache(self):
        """Test getting CoinGecko ID from cache."""
        lookup = PriceLookup(quiet=True)
        # BTC should be in common symbols
        coin_id = lookup._get_coingecko_id('BTC', validate=False)
        assert coin_id == 'bitcoin'
    
    @patch('get_current_prices.requests.Session')
    def test_get_coingecko_id_search(self, mock_session):
        """Test CoinGecko ID search for unknown symbol."""
        lookup = PriceLookup(quiet=True)
        
        # Mock the search response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'coins': [
                {'symbol': 'TEL', 'id': 'telcoin'},
                {'symbol': 'TEL', 'id': 'wrong-token'}
            ]
        }
        mock_session.return_value.get.return_value = mock_response
        
        # Should return first match
        coin_id = lookup._get_coingecko_id('TEL', validate=False)
        assert coin_id == 'telcoin'
    
    def test_validate_coin_id_price_match(self):
        """Test price validation with matching prices."""
        lookup = PriceLookup(quiet=True)
        
        with patch.object(lookup.session, 'get') as mock_get:
            # Mock CoinGecko response
            cg_response = Mock()
            cg_response.status_code = 200
            cg_response.json.return_value = {'telcoin': {'usd': 0.0038}}
            
            # Mock DefiLlama response
            llama_response = Mock()
            llama_response.status_code = 200
            llama_response.json.return_value = {
                'coins': {'coingecko:telcoin': {'price': 0.0038}}
            }
            
            mock_get.side_effect = [cg_response, llama_response]
            
            # Prices match (within threshold)
            result = lookup._validate_coin_id('TEL', 'telcoin', threshold=0.20)
            assert result is True
    
    def test_validate_coin_id_price_mismatch(self):
        """Test price validation with mismatched prices."""
        lookup = PriceLookup(quiet=True)
        
        with patch.object(lookup.session, 'get') as mock_get:
            # Mock CoinGecko response
            cg_response = Mock()
            cg_response.status_code = 200
            cg_response.json.return_value = {'telcoin': {'usd': 0.0038}}
            
            # Mock DefiLlama response with very different price
            llama_response = Mock()
            llama_response.status_code = 200
            llama_response.json.return_value = {
                'coins': {'coingecko:telcoin': {'price': 1.0}}  # Very different
            }
            
            mock_get.side_effect = [cg_response, llama_response]
            
            # Prices don't match (exceeds threshold)
            result = lookup._validate_coin_id('TEL', 'telcoin', threshold=0.20)
            assert result is False
