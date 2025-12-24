"""
Tests for file parsing functions.
"""

import pytest
import tempfile
from pathlib import Path
from get_current_prices import (
    parse_csv_file,
    parse_json_file,
    parse_freeform_text,
    parse_input_file
)


class TestCSVParsing:
    """Test CSV file parsing."""
    
    def test_parse_csv_basic(self):
        """Test basic CSV parsing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('symbol,price,notes\n')
            f.write('BTC,45000.00,Bought on Coinbase\n')
            f.write('SOL,95.50,Purchased on Kraken\n')
            f.flush()
            
            result = parse_csv_file(Path(f.name))
            assert len(result) == 2
            assert result[0][0] == 'BTC'
            assert result[0][1] == 45000.00
            assert result[1][0] == 'SOL'
            assert result[1][1] == 95.50
    
    def test_parse_csv_with_dollar_sign(self):
        """Test CSV parsing with dollar signs in price."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('symbol,price,notes\n')
            f.write('BTC,$45000.00,Bought\n')  # Dollar sign removed
            f.flush()
            
            result = parse_csv_file(Path(f.name))
            assert result[0][1] == 45000.00
    
    def test_parse_csv_with_commas_in_price(self):
        """Test CSV parsing with commas in price (CSV handles this)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('symbol,price,notes\n')
            f.write('BTC,\"45,000.00\",Bought\n')  # Quoted to preserve comma
            f.flush()
            
            result = parse_csv_file(Path(f.name))
            # CSV reader should handle quoted values correctly
            assert result[0][1] == 45000.00


class TestJSONParsing:
    """Test JSON file parsing."""
    
    def test_parse_json_array(self):
        """Test JSON array format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('[{"symbol": "BTC", "price": 45000.00, "notes": "Bought"}]')
            f.flush()
            
            result = parse_json_file(Path(f.name))
            assert len(result) == 1
            assert result[0][0] == 'BTC'
            assert result[0][1] == 45000.00
    
    def test_parse_json_object(self):
        """Test JSON object format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"BTC": {"price": 45000.00, "notes": "Bought"}}')
            f.flush()
            
            result = parse_json_file(Path(f.name))
            assert len(result) == 1
            assert result[0][0] == 'BTC'
            assert result[0][1] == 45000.00


class TestFreeformParsing:
    """Test free-form text parsing."""
    
    def test_parse_freeform_basic(self):
        """Test basic free-form text parsing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('- BTC (Coinbase, $45,000.00)\n')
            f.write('- SOL (Kraken, $95.50)\n')
            f.flush()
            
            result = parse_freeform_text(Path(f.name))
            assert len(result) == 2
            assert result[0][0] == 'BTC'
            assert result[0][1] == 45000.00
            assert result[1][0] == 'SOL'
            assert result[1][1] == 95.50
    
    def test_parse_freeform_without_leading_zero(self):
        """Test parsing prices without leading zero (e.g., $.00269)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('- BEAM (Kraken, $.00269)\n')
            f.flush()
            
            result = parse_freeform_text(Path(f.name))
            assert len(result) == 1
            assert result[0][0] == 'BEAM'
            assert result[0][1] == 0.00269
    
    def test_parse_freeform_no_price(self):
        """Test parsing lines without prices."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('- BTC (Coinbase)\n')
            f.write('- SOL\n')
            f.flush()
            
            result = parse_freeform_text(Path(f.name))
            assert len(result) == 2
            assert result[0][0] == 'BTC'
            assert result[0][1] is None
            assert result[1][0] == 'SOL'
            assert result[1][1] is None


class TestAutoDetect:
    """Test auto-detection of file format."""
    
    def test_auto_detect_csv(self):
        """Test CSV auto-detection."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('symbol,price\nBTC,45000\n')
            f.flush()
            
            result = parse_input_file(Path(f.name))
            assert len(result) == 1
            assert result[0][0] == 'BTC'
    
    def test_auto_detect_json(self):
        """Test JSON auto-detection."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('[{"symbol": "BTC", "price": 45000}]')
            f.flush()
            
            result = parse_input_file(Path(f.name))
            assert len(result) == 1
            assert result[0][0] == 'BTC'
    
    def test_auto_detect_text(self):
        """Test text auto-detection."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('- BTC (Coinbase, $45000)\n')
            f.flush()
            
            result = parse_input_file(Path(f.name))
            assert len(result) == 1
            assert result[0][0] == 'BTC'
