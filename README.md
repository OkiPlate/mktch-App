# Marketcheck Comparables App

A real-time market analysis tool for used cars built with Streamlit and the Marketcheck API.

## Features

- **VIN Decoding**: Automatically decode vehicle specifications from a VIN
- **Smart Comparable Search**: Find 30-50 active market listings based on your criteria
- **Dual Search Modes**:
  - **Strict Match**: High precision with exact year, make, model, trim (no mileage restriction)
  - **Lenient Match**: Broader results with +/- 1 year range, all trims, and optional mileage range (+/- 30%)
- **Advanced Filters**:
  - **Trim**: Filter by specific trim level
  - **Engine**: Filter by engine type (e.g., 2.0L I4, 3.5L V6)
  - **Transmission**: Filter by Automatic or Manual
- **Location-Based Search**:
  - **ZIP Code**: Search near a specific location
  - **Radius**: Configurable search radius (10-500 miles)
  - Results sorted by distance when location filters are active
- **Interactive Dashboard**: Clean, sortable data table with clickable listing links
- **Market Metrics**: Average price, average mileage, total comparables (and average distance when using location filters)
- **CSV Export**: Download results for further analysis

## Installation

1. **Clone or download this repository**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure your API key** (recommended):
   - Open the `.env` file
   - Replace `your_api_key_here` with your actual Marketcheck API key
   - Save the file

   Example:
   ```
   MARKETCHECK_API_KEY=abc123xyz456
   ```

   Alternatively, you can enter the API key directly in the app's sidebar.

## Usage

1. **Run the application**:
```bash
streamlit run app.py
```

2. **In the app**:
   - Enter your Marketcheck API key (get one at [marketcheck.com](https://www.marketcheck.com))
   - Input the 17-character VIN
   - Optionally enter the vehicle's current mileage
   - Choose your search mode (Strict or Lenient)
   - (Optional) Expand "Advanced Filters" to filter by trim, engine, or transmission
   - (Optional) Expand "Location Filters" to search by ZIP code and radius
   - Click "Find Comps" to see results

## Requirements

- Python 3.9+
- Streamlit
- Pandas
- Requests

## API Configuration

This app uses the Marketcheck V2 API:
- **VIN Decode**: `GET /v2/decode/car/{vin}/specs`
- **Search**: `GET /v2/search/car/active`

You'll need a valid Marketcheck API key to use this application.

## Project Structure

```
MktChkApp/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Search Logic

### Strict Match
- Exact match on: Year, Make, Model, Trim
- No mileage filtering (mileage varies too much)
- Use case: Finding vehicles with identical specs

### Lenient Match
- Make and Model match required
- Year range: +/- 1 year
- Trim: All trims included
- Mileage range: +/- 30% (if provided)
- Use case: Broader market analysis

## Output

The app displays:
1. **Vehicle Summary**: Decoded vehicle information
2. **Active Filters**: Shows which filters are currently applied
3. **Key Metrics**: Average price, average mileage, total comparables (+ average distance for location searches)
4. **Data Table**: Complete listing details with columns:
   - Heading
   - Price
   - Miles
   - Year
   - Trim
   - Engine
   - Transmission
   - Seller Name
   - City
   - State
   - Distance (when using location filters)
   - VDP URL (clickable link to listing)
5. **CSV Export**: Download button for all results

## Error Handling

The app gracefully handles:
- Invalid VINs
- Missing API keys
- API connection errors
- Zero results (with suggestion to try Lenient mode)

## License

This is a demonstration project for educational purposes.
