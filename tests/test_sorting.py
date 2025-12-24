"""
Tests for sorting functionality.
"""

import pytest
from get_current_prices import sort_results


class TestSorting:
    """Test result sorting."""
    
    def test_sort_by_symbol(self):
        """Test sorting by symbol."""
        results = [('ETH', 2934.0), ('BTC', 87384.0), ('SOL', 122.0)]
        sorted_results = sort_results(results, 'symbol', None, False)
        assert sorted_results[0][0] == 'BTC'
        assert sorted_results[1][0] == 'ETH'
        assert sorted_results[2][0] == 'SOL'
    
    def test_sort_by_current_price_descending(self):
        """Test sorting by current price (default descending)."""
        results = [('SOL', 122.0), ('BTC', 87384.0), ('ETH', 2934.0)]
        provided_prices = {}
        sorted_results = sort_results(results, 'current_price', provided_prices, False)
        # Highest first
        assert sorted_results[0][0] == 'BTC'
        assert sorted_results[1][0] == 'ETH'
        assert sorted_results[2][0] == 'SOL'
    
    def test_sort_by_current_price_ascending(self):
        """Test sorting by current price (ascending with reverse)."""
        results = [('SOL', 122.0), ('BTC', 87384.0), ('ETH', 2934.0)]
        provided_prices = {}
        sorted_results = sort_results(results, 'current_price', provided_prices, True)
        # Lowest first
        assert sorted_results[0][0] == 'SOL'
        assert sorted_results[1][0] == 'ETH'
        assert sorted_results[2][0] == 'BTC'
    
    def test_sort_by_change_pct(self):
        """Test sorting by percentage change."""
        results = [('LOW', 110.0), ('HIGH', 200.0), ('MED', 150.0)]
        provided_prices = {'LOW': 100.0, 'HIGH': 100.0, 'MED': 100.0}
        sorted_results = sort_results(results, 'change_pct', provided_prices, False)
        # Highest % change first
        assert sorted_results[0][0] == 'HIGH'  # +100%
        assert sorted_results[1][0] == 'MED'    # +50%
        assert sorted_results[2][0] == 'LOW'   # +10%
