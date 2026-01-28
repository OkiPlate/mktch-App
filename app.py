"""
Marketcheck Comparables App
A real-time market analysis tool for used cars using the Marketcheck API.
"""

import os
import streamlit as st
import pandas as pd
import requests
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# ============================================================================
# API FUNCTIONS
# ============================================================================

def decode_vin(vin: str, api_key: str) -> Optional[Dict]:
    """
    Decode a VIN using the Marketcheck API.
    
    Args:
        vin: 17-character Vehicle Identification Number
        api_key: Marketcheck API key
        
    Returns:
        Dictionary with vehicle specs or None if error occurs
    """
    url = f"https://mc-api.marketcheck.com/v2/decode/car/{vin}/specs"
    headers = {
        "Host": "mc-api.marketcheck.com"
    }
    params = {
        "api_key": api_key
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error decoding VIN: {str(e)}")
        return None


def search_comps(
    api_key: str,
    make: str,
    model: str,
    year: int,
    trim: Optional[str] = None,
    mileage: Optional[int] = None,
    search_mode: str = "Strict Match",
    engine_filter: Optional[str] = None,
    transmission_filter: Optional[str] = None,
    trim_filter: Optional[str] = None,
    zip_code: Optional[str] = None,
    radius: Optional[int] = None
) -> Optional[Dict]:
    """
    Search for comparable vehicles on Marketcheck.
    
    Args:
        api_key: Marketcheck API key
        make: Vehicle make
        model: Vehicle model
        year: Vehicle year
        trim: Vehicle trim (optional for lenient search)
        mileage: Vehicle mileage (optional)
        search_mode: "Strict Match" or "Lenient Match"
        engine_filter: Filter by engine type (e.g., "3.5L V6")
        transmission_filter: Filter by transmission type (e.g., "Automatic")
        trim_filter: Filter by specific trim level
        zip_code: ZIP code for location-based search
        radius: Search radius in miles from zip_code
        
    Returns:
        Dictionary with search results or None if error occurs
    """
    url = "https://mc-api.marketcheck.com/v2/search/car/active"
    headers = {
        "Host": "mc-api.marketcheck.com"
    }
    
    # Base parameters
    params = {
        "api_key": api_key,
        "car_type": "used",
        "make": make,
        "model": model,
        "rows": 50,
        "start": 0
    }
    
    # Apply search mode logic
    if search_mode == "Strict Match":
        # Strict: exact year, make, model, trim - NO mileage filtering
        # Mileage varies too much to be useful as a strict filter
        params["year"] = year
        if trim:
            params["trim"] = trim
        # Note: mileage is NOT filtered in strict mode
    
    else:  # Lenient Match
        # Lenient: +/- 1 year, no trim filter
        year_min = year - 1
        year_max = year + 1
        params["year"] = f"{year_min}-{year_max}"
        # Note: trim is intentionally NOT included
        
        # Wide mileage range: +/- 30% (only in lenient mode if provided)
        if mileage:
            range_percent = 0.30
            min_miles = int(mileage * (1 - range_percent))
            max_miles = int(mileage * (1 + range_percent))
            params["miles_range"] = f"{min_miles}-{max_miles}"
    
    # Apply additional filters
    if engine_filter:
        params["engine"] = engine_filter
    
    if transmission_filter:
        params["transmission"] = transmission_filter
    
    if trim_filter:
        # Override trim from search mode if user specifies a filter
        params["trim"] = trim_filter
    
    # Location-based filtering
    if zip_code:
        params["zip"] = zip_code
        if radius:
            params["radius"] = radius
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error searching comparables: {str(e)}")
        return None


def extract_vehicle_info(decode_response: Dict) -> Tuple[str, str, str, int]:
    """
    Extract make, model, trim, and year from decode response.
    
    Args:
        decode_response: Response from decode_vin API call
        
    Returns:
        Tuple of (make, model, trim, year)
    """
    # Navigate the response structure - adjust based on actual API response
    # Common structure: response may have 'car' or direct keys
    if 'car' in decode_response:
        car_data = decode_response['car']
    else:
        car_data = decode_response
    
    make = car_data.get('make', 'Unknown')
    model = car_data.get('model', 'Unknown')
    trim = car_data.get('trim', '')
    year = car_data.get('year', 0)
    
    return make, model, trim, year


def parse_listings(search_response: Dict) -> pd.DataFrame:
    """
    Parse search results into a clean DataFrame.
    
    Args:
        search_response: Response from search_comps API call
        
    Returns:
        DataFrame with listing information
    """
    listings = search_response.get('listings', [])
    
    if not listings:
        return pd.DataFrame()
    
    # Extract relevant fields from each listing
    data = []
    for listing in listings:
        # Get the build object which contains vehicle specs
        build = listing.get('build', {})
        
        # Build vehicle heading
        heading = listing.get('heading', '')
        if not heading:
            year = build.get('year', '')
            make = build.get('make', '')
            model = build.get('model', '')
            trim = build.get('trim', '')
            heading = f"{year} {make} {model} {trim}".strip()
        
        # Extract price
        price = listing.get('price', 0)
        
        # Extract mileage
        miles = listing.get('miles', 0)
        
        # Extract vehicle specs from build object
        year = build.get('year', '')
        trim = build.get('trim', '')
        engine = build.get('engine', '')
        transmission = build.get('transmission', '')
        
        # Extract seller information
        dealer = listing.get('dealer', {})
        seller_name = dealer.get('name', 'Unknown')
        city = dealer.get('city', '')
        state = dealer.get('state', '')
        
        # Extract distance if available (for location-based searches)
        distance = listing.get('dist', None)
        
        # Extract VDP URL
        vdp_url = listing.get('vdp_url', listing.get('link', ''))
        
        data.append({
            'Heading': heading,
            'Price': price,
            'Miles': miles,
            'Year': year,
            'Trim': trim,
            'Engine': engine,
            'Transmission': transmission,
            'Seller Name': seller_name,
            'City': city,
            'State': state,
            'Distance': distance,
            'VDP URL': vdp_url
        })
    
    df = pd.DataFrame(data)
    
    # Sort by price (ascending) or distance if available
    if not df.empty:
        if df['Distance'].notna().any():
            df = df.sort_values('Distance', ascending=True).reset_index(drop=True)
        else:
            df = df.sort_values('Price', ascending=True).reset_index(drop=True)
    
    return df


# ============================================================================
# STREAMLIT UI
# ============================================================================

def main():
    """Main Streamlit application."""
    
    # Page configuration
    st.set_page_config(
        page_title="Marketcheck Comparables",
        page_icon="🚗",
        layout="wide"
    )
    
    # Title
    st.title("🚗 Marketcheck Comparables App")
    st.markdown("*Real-time market analysis tool for used cars*")
    st.markdown("---")
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("Search Parameters")
        
        # API Key input - pre-populate from .env if available
        default_api_key = os.getenv("MARKETCHECK_API_KEY", "")
        api_key = st.text_input(
            "Marketcheck API Key",
            value=default_api_key,
            type="password",
            help="Enter your Marketcheck API key (or set MARKETCHECK_API_KEY in .env)"
        )
        
        st.markdown("---")
        
        # VIN input
        vin = st.text_input(
            "Vehicle VIN",
            max_chars=17,
            help="Enter the 17-character VIN"
        ).strip().upper()
        
        # Mileage input
        mileage = st.number_input(
            "Current Mileage (optional)",
            min_value=0,
            max_value=500000,
            value=0,
            step=1000,
            help="Enter the vehicle's current mileage"
        )
        
        # If mileage is 0, treat as None
        if mileage == 0:
            mileage = None
        
        # Search mode
        search_mode = st.radio(
            "Search Mode",
            options=["Strict Match", "Lenient Match"],
            help=(
                "**Strict Match:** Exact year, make, model, trim (no mileage filter)\n\n"
                "**Lenient Match:** +/- 1 year, no trim filter, optional mileage range (+/- 30%)"
            )
        )
        
        st.markdown("---")
        
        # Advanced Filters Section
        with st.expander("🔧 Advanced Filters", expanded=False):
            # Trim filter
            trim_filter = st.text_input(
                "Trim",
                help="Filter by specific trim level (e.g., EX, Limited, SX)"
            ).strip()
            if not trim_filter:
                trim_filter = None
            
            # Engine filter
            engine_filter = st.text_input(
                "Engine",
                help="Filter by engine type (e.g., 2.0L I4, 3.5L V6)"
            ).strip()
            if not engine_filter:
                engine_filter = None
            
            # Transmission filter
            transmission_filter = st.selectbox(
                "Transmission",
                options=["Any", "Automatic", "Manual"],
                help="Filter by transmission type"
            )
            if transmission_filter == "Any":
                transmission_filter = None
        
        st.markdown("---")
        
        # Location Filters Section
        with st.expander("📍 Location Filters", expanded=False):
            # ZIP Code input
            zip_code = st.text_input(
                "ZIP Code",
                max_chars=5,
                help="Enter a 5-digit ZIP code for location-based search"
            ).strip()
            if not zip_code or len(zip_code) != 5:
                zip_code = None
            
            # Radius input (only show if ZIP code is provided)
            radius = st.slider(
                "Search Radius (miles)",
                min_value=10,
                max_value=500,
                value=100,
                step=10,
                help="Search radius from the ZIP code (in miles)"
            )
            
            if not zip_code:
                radius = None
                st.caption("Enter a ZIP code to enable radius search")
        
        st.markdown("---")
        
        # Search button
        search_button = st.button("🔍 Find Comps", type="primary", use_container_width=True)
    
    # Main content area
    if search_button:
        # Validation
        if not api_key:
            st.error("⚠️ Please enter your Marketcheck API key in the sidebar.")
            return
        
        if not vin or len(vin) != 17:
            st.error("⚠️ Please enter a valid 17-character VIN.")
            return
        
        # Step 1: Decode VIN
        with st.spinner("Decoding VIN..."):
            decode_response = decode_vin(vin, api_key)
        
        if not decode_response:
            st.error("❌ Failed to decode VIN. Please check the VIN and API key.")
            return
        
        # Extract vehicle information
        try:
            make, model, trim, year = extract_vehicle_info(decode_response)
        except Exception as e:
            st.error(f"❌ Error parsing vehicle information: {str(e)}")
            st.json(decode_response)  # Show raw response for debugging
            return
        
        # Display decoded vehicle
        st.success(f"✅ Vehicle Decoded: **{year} {make} {model} {trim}**")
        
        # Step 2: Search for comparables
        with st.spinner(f"Searching for comparables ({search_mode})..."):
            search_response = search_comps(
                api_key=api_key,
                make=make,
                model=model,
                year=year,
                trim=trim if search_mode == "Strict Match" else None,
                mileage=mileage,
                search_mode=search_mode,
                engine_filter=engine_filter,
                transmission_filter=transmission_filter,
                trim_filter=trim_filter,
                zip_code=zip_code,
                radius=radius
            )
        
        if not search_response:
            st.error("❌ Failed to search comparables.")
            return
        
        # Parse listings
        df = parse_listings(search_response)
        
        if df.empty:
            st.warning(
                "⚠️ No comparables found. "
                "Try switching to **Lenient Match** for broader results."
            )
            return
        
        # Display results
        st.markdown("---")
        st.header(f"📊 Market Data for: {year} {make} {model} {trim if trim else ''}")
        
        # Show active filters summary
        active_filters = []
        if engine_filter:
            active_filters.append(f"Engine: {engine_filter}")
        if transmission_filter:
            active_filters.append(f"Transmission: {transmission_filter}")
        if trim_filter:
            active_filters.append(f"Trim: {trim_filter}")
        if zip_code:
            active_filters.append(f"Location: {zip_code} ({radius} mi radius)")
        
        if active_filters:
            st.info(f"**Active Filters:** {' | '.join(active_filters)}")
        
        # Metrics - adjust based on whether distance is available
        if df['Distance'].notna().any():
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_price = df['Price'].mean()
                st.metric("Average Price", f"${avg_price:,.0f}")
            
            with col2:
                avg_miles = df['Miles'].mean()
                st.metric("Average Mileage", f"{avg_miles:,.0f} mi")
            
            with col3:
                total_comps = len(df)
                st.metric("Total Comparables", total_comps)
            
            with col4:
                avg_distance = df['Distance'].mean()
                st.metric("Avg Distance", f"{avg_distance:.1f} mi")
        else:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_price = df['Price'].mean()
                st.metric("Average Price", f"${avg_price:,.0f}")
            
            with col2:
                avg_miles = df['Miles'].mean()
                st.metric("Average Mileage", f"{avg_miles:,.0f} mi")
            
            with col3:
                total_comps = len(df)
                st.metric("Total Comparables", total_comps)
        
        st.markdown("---")
        
        # Data table
        st.subheader("Comparable Listings")
        
        # Format the dataframe for display
        df_display = df.copy()
        df_display['Price'] = df_display['Price'].apply(lambda x: f"${x:,.0f}" if x else "N/A")
        df_display['Miles'] = df_display['Miles'].apply(lambda x: f"{x:,.0f}" if x else "N/A")
        
        # Format distance column if it has values
        if df_display['Distance'].notna().any():
            df_display['Distance'] = df_display['Distance'].apply(
                lambda x: f"{x:.1f} mi" if pd.notna(x) else "N/A"
            )
        else:
            # Drop distance column if no location search was performed
            df_display = df_display.drop(columns=['Distance'])
        
        # Define column config
        column_config = {
            "VDP URL": st.column_config.LinkColumn(
                "VDP URL",
                help="Click to view listing",
                display_text="View Listing"
            ),
            "Price": st.column_config.TextColumn("Price"),
            "Miles": st.column_config.TextColumn("Miles"),
            "Year": st.column_config.NumberColumn("Year", format="%d"),
        }
        
        # Display with clickable links
        st.dataframe(
            df_display,
            column_config=column_config,
            hide_index=True,
            use_container_width=True
        )
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"marketcheck_comps_{vin}_{year}_{make}_{model}.csv",
            mime="text/csv"
        )
    
    else:
        # Initial state - show instructions
        st.info(
            "👈 **Get Started:**\n\n"
            "1. Enter your Marketcheck API key in the sidebar\n"
            "2. Enter the vehicle's VIN\n"
            "3. Optionally enter the current mileage\n"
            "4. Choose a search mode (Strict or Lenient)\n"
            "5. Use Advanced Filters to narrow by trim, engine, or transmission\n"
            "6. Use Location Filters to search by ZIP code and radius\n"
            "7. Click '🔍 Find Comps' to analyze the market"
        )
        
        # Show feature comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎯 Strict Match")
            st.markdown("""
            - Exact year, make, model, trim
            - No mileage restriction
            - Higher precision on vehicle specs
            - Best for specific vehicle matching
            """)
        
        with col2:
            st.markdown("### 🌐 Lenient Match")
            st.markdown("""
            - +/- 1 year range
            - All trims included
            - Optional mileage range (+/- 30%)
            - Higher volume, broader market view
            """)
        
        # Show filter options
        st.markdown("---")
        st.markdown("### 🔧 Available Filters")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Advanced Filters:**
            - **Trim** - Filter by specific trim level
            - **Engine** - Filter by engine type (e.g., 3.5L V6)
            - **Transmission** - Automatic or Manual
            """)
        
        with col2:
            st.markdown("""
            **Location Filters:**
            - **ZIP Code** - Search near a specific location
            - **Radius** - Set search radius (10-500 miles)
            - Results sorted by distance when location is set
            """)


if __name__ == "__main__":
    main()
