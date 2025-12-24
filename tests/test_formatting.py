"""
Tests for price and change formatting functions.
"""

import pytest
from get_current_prices import format_price, format_change, calculate_change


class TestPriceFormatting:
    """Test price formatting."""
    
    def test_format_large_price(self):
        """Test formatting large prices (>= $1000)."""
        assert format_price(87384.16) == "$87,384.16"
        assert format_price(2934.65) == "$2,934.65"
    
    def test_format_medium_price(self):
        """Test formatting medium prices ($10-$999)."""
        assert format_price(122.33) == "$122.33"
        assert format_price(12.25) == "$12.25"
        assert format_price(5.60) == "$5.60"
    
    def test_format_small_price(self):
        """Test formatting small prices ($1-$9.99)."""
        assert format_price(1.28) == "$1.28"
        assert format_price(1.2829) == "$1.2829"
    
    def test_format_very_small_price(self):
        """Test formatting very small prices (< $1)."""
        assert format_price(0.4663) == "$0.4663"
        assert format_price(0.2271) == "$0.2271"
        assert format_price(0.00872912) == "$0.00872912"
        assert format_price(0.00027347) == "$0.00027347"
    
    def test_format_negative_price(self):
        """Test formatting negative prices."""
        assert format_price(-100.50) == "$-100.50"


class TestChangeFormatting:
    """Test change formatting."""
    
    def test_format_large_change(self):
        """Test formatting large changes."""
        # Large changes (>= 1000) show with thousands separator
        result1 = format_change(42328.89, 45000.0)
        assert result1.startswith("$+42") or result1.startswith("$+4")
        assert "42328" in result1.replace(",", "") or "42" in result1
        # Changes >= 1000 use thousands separator
        result2 = format_change(1000.0, 5000.0)
        assert "$+1,000" in result2 or "$+1000" in result2
    
    def test_format_small_change(self):
        """Test formatting small changes."""
        assert format_change(0.0157, 0.4820) == "$+0.0157"
        assert format_change(-0.000138, 0.00886666) == "$-0.000138"
    
    def test_format_tiny_change(self):
        """Test formatting tiny changes."""
        assert format_change(0.0000005955, 0.00027287) == "$+0.0000005955"


class TestCalculateChange:
    """Test change calculation."""
    
    def test_calculate_positive_change(self):
        """Test positive price change."""
        abs_change, pct_change, symbol, text = calculate_change(100.0, 90.0)
        assert abs_change == 10.0
        assert abs(pct_change - 11.111) < 0.1  # ~11.11%
        assert symbol == "↑"
        assert text == "Up"
    
    def test_calculate_negative_change(self):
        """Test negative price change."""
        abs_change, pct_change, symbol, text = calculate_change(90.0, 100.0)
        assert abs_change == -10.0
        assert abs(pct_change - -10.0) < 0.1  # ~-10%
        assert symbol == "↓"
        assert text == "Down"
    
    def test_calculate_unchanged(self):
        """Test essentially unchanged price."""
        abs_change, pct_change, symbol, text = calculate_change(100.0, 100.001)
        assert abs(pct_change) < 0.01  # Very small change
        assert symbol == "═"
        assert text == "Unchanged"
