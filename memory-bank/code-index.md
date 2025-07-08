# Code Index

## Main Application Files

### `run_scenario_ladder.py` (1,235 lines)
Primary Dash web application providing the trading ladder interface. Handles TT API integration, price conversions, P&L calculations, and real-time data display. Contains callback functions for user interactions, spot price fetching via Pricing Monkey automation, and data table rendering.

### `lifo_pnl_monitor.py` (242 lines)
Background monitoring script that processes filled orders using LIFO (Last In, First Out) accounting methodology. Continuously monitors CSV files for new trades, calculates realized P&L, and maintains position stack state. Supports filtering for specific contracts (ZN Sep25) and provides configurable monitoring parameters.

### `continuous_fill_monitor.py` (603 lines)
Continuously polls TT API for filled orders and maintains CSV output files. Implements comprehensive error handling, retry logic, and state persistence. Provides detailed logging and supports multiple command-line options for polling intervals and output configuration.

### `position_monitor.py` (242 lines)
Retrieves and displays current positions from TT API using the ttmonitor service. Filters for CME exchange positions and provides formatted output highlighting ZN Sep25 contracts. Supports command-line arguments for account filtering and JSON output options.

### `download_filled_orders.py` (35+ lines)
Utility script for downloading filled orders from TT API and saving to JSON files. Uses existing TT API infrastructure with proper token management and error handling. Provides foundation for ad-hoc fill data extraction and analysis.

## Library Components

### `lib/components/core/base_component.py` (55 lines)
Abstract base class for all UI components ensuring consistent interface and theme handling. Provides ID validation, theme injection, and standardized render() method contract. Foundation for the component factory pattern used throughout the UI system.

### `lib/components/core/protocols.py`
Protocol definitions for component interfaces ensuring type safety and consistent API contracts. Defines abstract interfaces that components must implement for proper integration with the theme system.

### `lib/components/basic/button.py`
Button component wrapper providing consistent styling and behavior. Extends base component with theme support and standardized event handling for Dash applications.

### `lib/components/advanced/datatable.py`
Advanced DataTable component with comprehensive theming support. Provides enhanced functionality for displaying trading data with color coding, sorting, and responsive design. Core component for the ladder visualization interface.

### `lib/components/advanced/grid.py`
Grid layout component using Bootstrap for responsive design. Provides consistent spacing and alignment for complex UI layouts in the trading interface.

### `lib/components/themes/colour_palette.py`
Color definitions and theme configurations for consistent visual styling. Defines color schemes for buy/sell indicators, profit/loss display, and general UI elements throughout the application.

## Trading Logic

### `lib/trading/ladder/price_formatter.py` (78 lines)
Core price conversion utilities for TT bond format handling. Converts decimal prices to TT special format (e.g., 110.015625 → "110'005") and vice versa. Includes comprehensive test cases and handles fractional tick calculations with precision.

### `lib/trading/ladder/csv_to_sqlite.py` (177 lines)
Database utilities for loading CSV data into SQLite databases. Provides functions for DataFrame-to-SQLite conversion, schema inspection, and data querying. Handles SOD (Start of Day) data processing for baseline position calculations.

### `lib/trading/tt_api/config.py` (24 lines)
Configuration file containing TT API credentials and environment settings. Defines API keys for UAT and SIM environments, application identifiers, and token management settings. Central configuration point for all TT API interactions.

### `lib/trading/tt_api/token_manager.py` (125+ lines)
Comprehensive token management system for TT API authentication. Handles token acquisition, automatic refresh, environment-specific storage, and thread-safe access. Implements proper error handling and state persistence for reliable API access.

### `lib/trading/tt_api/utils.py`
Utility functions for TT API interactions including GUID generation, request ID creation, and bearer token formatting. Provides common functionality used across all API integration points.

### `lib/trading/tt_api/__init__.py` (37 lines)
Package initialization file exposing all TT API functionality. Provides clean import interface for token management, configuration, and utility functions used throughout the application.

## Background Monitoring

### `fill_download (1).py` (910+ lines)
Legacy fill download script with comprehensive TT API integration. Implements token management, market enum caching, and continuous monitoring capabilities. Provides foundation for understanding TT API patterns and error handling approaches.

## Data Files

### `data/input/ladder/my_working_orders_response.json`
Mock data file containing sample TT API responses for working orders. Used for development and testing when `USE_MOCK_DATA = True`. Provides realistic data structure for offline development work.

### `data/input/sod/SampleSOD.csv`
Sample Actant Start of Day data containing baseline position information. Used for calculating position baselines and integrating with external position management systems.

### `data/output/ladder/actant_data.db`
SQLite database created from SOD CSV data. Contains processed position information used for baseline calculations and historical analysis.

### `data/output/ladder/continuous_fills.csv`
Output file from continuous fill monitoring containing trade records. Includes timestamps, quantities, prices, and side information for all processed fills.

## Configuration & Scripts

### `requirements.txt` (9 lines)
Python dependency specification including Dash, pandas, requests, and Windows automation libraries. Defines minimum versions for all required packages ensuring compatibility and functionality.

### `README.md` (169 lines)
Comprehensive documentation covering installation, configuration, usage, and troubleshooting. Provides complete setup instructions, feature explanations, and common issue resolution guidance.

### `ttcheatsheet.md`
Quick reference guide for TT API usage and common operations. Contains code examples, API endpoints, and troubleshooting tips for TT integration.

### `check_system_status.bat`
Windows batch script for verifying system status and process health. Checks for running Python processes and provides basic system diagnostics.

### `detailed_system_check.bat` (47 lines)
Comprehensive system diagnostic script checking file activity, trade counts, and recent system updates. Provides detailed analysis of monitoring system health and data flow status.

### `start_streaming_system.bat`
Windows batch script for starting background monitoring processes. Launches fill monitors and position tracking in background mode for continuous operation.

### `restart_clean_system.bat`
System restart script that cleans up existing processes and starts fresh monitoring instances. Provides clean slate startup for troubleshooting and maintenance.

## Jupyter Notebooks

### `LIFO.ipynb` (1,400+ lines)
Comprehensive analysis notebook for LIFO P&L calculations and position tracking. Contains detailed trade analysis, position calculations, and data visualization for understanding trading patterns and P&L attribution.

## State & Log Files

### `lifo_streaming_state.pkl`
Pickle file containing serialized state for LIFO position tracking. Maintains position stack and processed transaction history for system recovery and continuity.

### `AuditTrail.csv`
Comprehensive audit log of all system operations and data changes. Provides complete traceability for compliance and debugging purposes.

### `data/output/ladder/logs/`
Directory containing dated log files from monitoring processes. Includes fill monitor logs, price monitor logs, and system operation logs with timestamps and detailed activity records. 