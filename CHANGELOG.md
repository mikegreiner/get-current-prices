# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-12-24

### Added
- Python 3.13 support in test matrix
- CSV output format (`-o csv` or `--output-format csv`)
- Comprehensive test suite with pytest
- GitHub Actions CI workflow
- Local multi-version testing script (`test-matrix.sh`)
- pyenv support in test matrix script
- Auto-handling of ensurepip issues in test script
- Symbol mappings externalized to `symbol_mappings.json` with auto-save
- Cross-source price validation for new symbol mappings
- Quiet mode (`-q`/`--quiet`) for scripting
- Filtering by price direction (`-F up|down|unchanged`)
- Filtering by symbol (`-s SYMBOLS`)
- Sorting by multiple fields (`-S FIELD` with `--sort-reverse`)
- Variable decimal precision for prices and changes
- Status indicators (↑ Down, ↓ Up, ═ Unchanged)
- Improved price parsing for formats like `$.00269`
- Documentation: SETUP_PYENV.md, FIX_PYENV_VENV.md

### Changed
- Prefer pyenv versions over system Python in test script
- Better error handling: distinguish skipped vs failed test versions
- Updated User-Agent to `Crypto-Price-Lookup/1.0`
- Dropped Python 3.7 support (EOL since June 2023)

### Fixed
- SYRUP symbol mapping (was incorrectly mapped to pancakeswap-token)
- Price parsing for prices without leading zeros (`$.00269`)
- Test sorting verification to check actual sort order

## [1.1.0] - 2025-12-24

### Added
- Price comparison feature (compare current vs provided prices)
- File input support (CSV, JSON, free-form text)
- Symbol filtering and price direction filtering
- Sorting capabilities
- JSON output format

## [1.0.0] - 2025-12-24

### Added
- Initial release
- Command-line symbol lookup
- DefiLlama and CoinGecko price sources
- Symbol-to-CoinGecko ID mapping
- Basic price formatting

[1.2.0]: https://github.com/mikegreiner/get-current-prices/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/mikegreiner/get-current-prices/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/mikegreiner/get-current-prices/releases/tag/v1.0.0
