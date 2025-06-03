import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests
from fuzzywuzzy import fuzz
import json

st.set_page_config(
    page_title="Embase Conference Dashboard",
    page_icon="📊",
    layout="wide"
)

# File paths
EXCEL_FILE = "conference_list.xlsx"
EXCEL_URL = "https://assets.ctfassets.net/o78em1y1w4i4/3InSDlhY7ZDpfNXRWb6jId/0456ecded39532f57a1a016762ed2d86/2024-10_Conference-coverage-list.xlsx"
PINNED_FILE = "pinned_conferences.json"

# Function to create unique conference ID
def create_conference_id(row):
    """Create a unique identifier for a conference"""
    # Combine conference name, start date, and location for uniqueness
    conf_name = str(row.get('Conference Event', ''))
    start_date = str(row.get('Start Date', ''))
    location = str(row.get('Conference location', ''))
    return f"{conf_name}|{start_date}|{location}"

# Function to save pinned conferences
def save_pinned_conferences(pinned_data):
    """Save pinned conference data to JSON file"""
    try:
        with open(PINNED_FILE, 'w') as f:
            json.dump(list(pinned_data), f)
        return True
    except Exception as e:
        st.error(f"Error saving pinned conferences: {str(e)}")
        return False

# Function to load pinned conferences
def load_pinned_conferences():
    """Load pinned conference data from JSON file"""
    if os.path.exists(PINNED_FILE):
        try:
            with open(PINNED_FILE, 'r') as f:
                return set(json.load(f))
        except Exception as e:
            st.error(f"Error loading pinned conferences: {str(e)}")
            return set()
    return set()

st.title("Embase Conference Dashboard Prototype")
#st.markdown("Search and manage conference information from Embase")

# Initialize session state for pinned conferences
if 'pinned_conferences' not in st.session_state:
    st.session_state.pinned_conferences = load_pinned_conferences()

# Function to download the latest Excel file
def download_latest_excel():
    try:
        response = requests.get(EXCEL_URL)
        with open(EXCEL_FILE, 'wb') as f:
            f.write(response.content)
        return True, "Successfully downloaded the latest conference list!"
    except Exception as e:
        return False, f"Error downloading file: {str(e)}"

# Function to load conference data
@st.cache_data
def load_conference_data():
    if not os.path.exists(EXCEL_FILE):
        st.error(f"Conference list file not found: {EXCEL_FILE}")
        return pd.DataFrame()
    
    # Load all sheets except the header sheet
    all_data = []
    excel_file = pd.ExcelFile(EXCEL_FILE)
    
    for sheet_name in excel_file.sheet_names:
        if sheet_name != 'Header':
            df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
            df['Year'] = sheet_name
            all_data.append(df)
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Convert date columns to datetime
    combined_df['Start Date'] = pd.to_datetime(combined_df['Start Date'], errors='coerce')
    combined_df['End Date'] = pd.to_datetime(combined_df['End Date'], errors='coerce')
    
    # Add unique conference ID
    combined_df['conference_id'] = combined_df.apply(create_conference_id, axis=1)
    
    return combined_df

# Function to perform fuzzy search
def fuzzy_search(search_term, df, columns, threshold=60):
    """
    Perform fuzzy search on specified columns
    Returns indices of matching rows
    """
    if not search_term:
        return df.index.tolist()
    
    matching_indices = set()
    
    for column in columns:
        # Get non-null values from the column
        valid_data = df[column].dropna()
        
        if len(valid_data) == 0:
            continue
        
        # For each valid value, calculate fuzzy match score
        for idx, value in valid_data.items():
            # Use partial ratio for better matching of partial strings
            score = fuzz.partial_ratio(search_term.lower(), str(value).lower())
            if score >= threshold:
                matching_indices.add(idx)
    
    return list(matching_indices)

# Initialize search filters in session state
if 'search_text' not in st.session_state:
    st.session_state.search_text = ""
if 'selected_country' not in st.session_state:
    st.session_state.selected_country = "All"
if 'selected_year' not in st.session_state:
    st.session_state.selected_year = "All"
if 'fuzzy_threshold' not in st.session_state:
    st.session_state.fuzzy_threshold = 80

# Load conference data
df = load_conference_data()

# Sidebar for refresh and filters
with st.sidebar:
    st.header("🔍 Search & Filters")
    
    # Search filters
    st.session_state.search_text = st.text_input(
        "Search by conference name", 
        value=st.session_state.search_text,
        placeholder="Enter conference name..."
    )
    
    st.session_state.fuzzy_threshold = st.slider(
        "Search sensitivity", 
        40, 100, 
        st.session_state.fuzzy_threshold, 
        5,
        help="Lower values = more fuzzy matches"
    )
    
    # Get unique countries and years from the data if it's loaded
    if not df.empty:
        countries = ['All'] + sorted(df['Country'].dropna().unique().tolist())
        st.session_state.selected_country = st.selectbox(
            "Country", 
            countries,
            index=countries.index(st.session_state.selected_country) if st.session_state.selected_country in countries else 0
        )
        
        years = ['All'] + sorted(df['Year'].unique().tolist(), reverse=True)
        st.session_state.selected_year = st.selectbox(
            "Year", 
            years,
            index=years.index(st.session_state.selected_year) if st.session_state.selected_year in years else 0
        )
    
    st.divider()
    
    #st.header("📊 Data Management")
    
    # Refresh button
    if st.button("🔄 Refresh Conference List", use_container_width=True):
        success, message = download_latest_excel()
        if success:
            st.success(message)
            # Clear cache to reload data
            st.cache_data.clear()
            st.rerun()
        else:
            st.error(message)
    
    # Show last update time
    if os.path.exists(EXCEL_FILE):
        mod_time = datetime.fromtimestamp(os.path.getmtime(EXCEL_FILE))
        st.info(f"Last updated: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")

if df.empty:
    st.warning("No conference data available. Please refresh the conference list.")
else:
    # Main content area
    tab1, tab2 = st.tabs(["🔍 Search Conferences", "📌 Pinned Conferences"])
    
    with tab1:
        # Apply filters using session state values
        filtered_df = df.copy()
        
        if st.session_state.search_text:
            # Use fuzzy search for conference name and location
            matching_indices = fuzzy_search(
                st.session_state.search_text, 
                filtered_df, 
                ['Conference Event', 'Conference location'], 
                threshold=st.session_state.fuzzy_threshold
            )
            filtered_df = filtered_df.loc[matching_indices]
        
        if st.session_state.selected_country != 'All':
            filtered_df = filtered_df[filtered_df['Country'] == st.session_state.selected_country]
        
        if st.session_state.selected_year != 'All':
            filtered_df = filtered_df[filtered_df['Year'] == st.session_state.selected_year]
        
        # Display results count
        st.info(f"Found {len(filtered_df)} conferences")
        
        # Display filtered results
        if not filtered_df.empty:
            # Info about double-click limitation
            st.info("💡 **Tip:** Due to a Streamlit limitation, you may need to click the pin checkbox twice - once to focus the cell, and once to toggle the pin.")
            
            # Make a copy to avoid modifying the original
            display_df = filtered_df.copy()
            
            # Add a column for pinning
            display_df['Pin'] = display_df['conference_id'].isin(st.session_state.pinned_conferences)
            
            # Configure columns to display
            columns_to_display = ['Pin', 'Conference Event', 'Conference location', 'Country', 
                                'Start Date', 'End Date', 'Number of abstracts', 'Year']
            
            # Create an editable dataframe with a unique key
            edited_df = st.data_editor(
                display_df[columns_to_display],
                column_config={
                    "Pin": st.column_config.CheckboxColumn(
                        "📌",
                        help="Pin this conference (may require two clicks)",
                        width="small"
                    ),
                    "Conference Event": st.column_config.TextColumn(
                        "Conference Event",
                        width="large"
                    ),
                    "Start Date": st.column_config.DateColumn(
                        "Start Date",
                        format="YYYY-MM-DD"
                    ),
                    "End Date": st.column_config.DateColumn(
                        "End Date",
                        format="YYYY-MM-DD"
                    ),
                    "Number of abstracts": st.column_config.NumberColumn(
                        "Abstracts",
                        format="%d"
                    )
                },
                hide_index=True,
                use_container_width=True,
                key="search_results_table"
            )
            
            # Process the changes only if there's a difference
            current_pinned = set(display_df.loc[edited_df[edited_df['Pin']].index, 'conference_id'].tolist())
            
            if current_pinned != st.session_state.pinned_conferences:
                st.session_state.pinned_conferences = current_pinned
                save_pinned_conferences(st.session_state.pinned_conferences)
    
    with tab2:
        st.header("Pinned Conferences")
        
        if st.session_state.pinned_conferences:
            # Filter by conference IDs
            pinned_df = df[df['conference_id'].isin(st.session_state.pinned_conferences)].copy()
            
            # Add select column for deletion
            pinned_df['Select'] = False
            
            # Configure columns to display
            columns_to_display = ['Select', 'Conference Event', 'Conference location', 'Country', 
                                'Start Date', 'End Date', 'Number of abstracts', 'Year']
            
            # Create an editable dataframe for selection
            st.info("💡 **Tip:** Select conferences to unpin them. You may need to click checkboxes twice.")
            
            edited_pinned_df = st.data_editor(
                pinned_df[columns_to_display],
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select to unpin",
                        width="small"
                    ),
                    "Conference Event": st.column_config.TextColumn(
                        "Conference Event",
                        width="large"
                    ),
                    "Start Date": st.column_config.DateColumn(
                        "Start Date",
                        format="YYYY-MM-DD"
                    ),
                    "End Date": st.column_config.DateColumn(
                        "End Date",
                        format="YYYY-MM-DD"
                    ),
                    "Number of abstracts": st.column_config.NumberColumn(
                        "Abstracts",
                        format="%d"
                    )
                },
                hide_index=True,
                use_container_width=True,
                key="pinned_table"
            )
            
            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 4])
            
            with col1:
                if st.button("🗑️ Unpin Selected", type="secondary"):
                    # Get selected conference IDs
                    selected_rows = edited_pinned_df[edited_pinned_df['Select']]
                    if not selected_rows.empty:
                        selected_ids = pinned_df.loc[selected_rows.index, 'conference_id'].tolist()
                        # Remove selected conferences from pinned list
                        for conf_id in selected_ids:
                            st.session_state.pinned_conferences.discard(conf_id)
                        # Save updated list
                        save_pinned_conferences(st.session_state.pinned_conferences)
                        st.success(f"Unpinned {len(selected_ids)} conference(s)")
                        st.rerun()
                    else:
                        st.warning("No conferences selected")
            
            with col2:
                # Download button for pinned conferences
                if st.button("📥 Download as Excel", type="primary"):
                    # Create Excel file in memory
                    from io import BytesIO
                    output = BytesIO()
                    
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        pinned_df[['Conference Event', 'Conference location', 'Country', 
                                  'Start Date', 'End Date', 'Number of abstracts', 'Year']].to_excel(
                            writer, sheet_name='Pinned Conferences', index=False
                        )
                    
                    output.seek(0)
                    
                    st.download_button(
                        label="Click to Download",
                        data=output,
                        file_name=f"pinned_conferences_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.info("No conferences pinned yet. Use the search tab to find and pin conferences.")

# Footer
st.markdown("---")
st.markdown("💡 **Tips:** Use the search filters to find conferences, pin the ones you're interested in, and download your selection as an Excel file.")