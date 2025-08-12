import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- Page Configuration ---
# Sets the title and icon that appear in the browser tab
st.set_page_config(
    page_title="Court Cases Dashboard",
    page_icon="⚖️",
    layout="wide",
)

# --- Data Loading and Cleaning from Google Sheets ---
# This function will be cached, meaning it only re-runs when the input changes
# or after 10 minutes (ttl=600 seconds), so your app stays fast.
@st.cache_data(ttl=600)
def load_data(sheet_id, gid="0"):
    """Loads and cleans data from a public Google Sheet."""
    try:
        # Construct the URL to download the sheet as a CSV
        url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}'
        
        # Load the data, skipping the first row which might be a title
        df = pd.read_csv(url, skiprows=1)

        # --- Data Cleaning and Preprocessing ---
        # This section is the same as before. It standardizes your data.
        df.columns = [
            's_no', 'supervisor_office', 'branch_name', 'clerk', 'case_no',
            'case_title', 'case_status', 'status_comment', 'pending_stage',
            'court_name', 'dc_action_needed', 'dc_action_to_be_taken',
            'reply_by', 'reply_filed', 'next_hearing_date', 'case_detail',
            'court_directions', 'direction_details', 'compliance_of_direction',
            'status_reply_required', 'status_reply_filed', 'case_documents',
            'remarks', 'days_left'
        ]
        df = df.iloc[1:].reset_index(drop=True)
        df.dropna(subset=['s_no'], inplace=True)
        df['case_status'] = df['case_status'].str.strip().str.title().fillna('Not Specified')
        status_replacements = {'Pending': 'Pending', 'Decided': 'Decided', 'Dismissed': 'Decided', 'Disposed': 'Decided'}
        df['case_status'] = df['case_status'].replace(status_replacements).fillna('Not Specified')
        df['court_name'] = df['court_name'].str.strip().str.title().fillna('Not Specified')
        court_replacements = {'Punjab And Haryana High Court': 'High Court', 'District Court Ludhiana': 'District Court', 'Supreme Court Of India': 'Supreme Court'}
        df['court_name'] = df['court_name'].replace(court_replacements)
        df['next_hearing_date'] = pd.to_datetime(df['next_hearing_date'], errors='coerce')
        df['supervisor_office'] = df['supervisor_office'].fillna('Not Assigned')
        
        return df
    except Exception as e:
        # Show a helpful error message if the Google Sheet can't be accessed
        st.error(f"Error loading data from Google Sheet: {e}")
        st.error("Please make sure your Google Sheet is shared with 'Anyone with the link' as a 'Viewer'.")
        return pd.DataFrame()

# --- Main App Logic ---
#
# Your specific Google Sheet ID and GID have been added here.
#
SHEET_ID = "1lmN_fpYqk63Zq8P1cJMtFD_5UpVbGYXvTa5hU1G6eLM" 
GID = "322810088" # This has been updated to point to your specific sheet.

# Load the data using the function
df = load_data(SHEET_ID, GID)

# Only run the rest of the app if the data was loaded successfully
if not df.empty:
    # --- Page Title ---
    st.title("⚖️ Court Cases Analysis Dashboard")
    st.markdown("An interactive dashboard to monitor and analyze court cases for the DC Office, Ludhiana.")

    # --- Sidebar Filters ---
    st.sidebar.header("Dashboard Filters")
    supervisor_office = st.sidebar.multiselect(
        "Select Supervisor Office",
        options=df["supervisor_office"].unique(),
        default=df["supervisor_office"].unique()
    )
    case_status = st.sidebar.multiselect(
        "Select Case Status",
        options=df["case_status"].unique(),
        default=df["case_status"].unique()
    )
    court_name = st.sidebar.multiselect(
        "Select Court",
        options=df["court_name"].unique(),
        default=df["court_name"].unique()
    )

    # Filter the DataFrame based on the user's selections
    df_filtered = df.query(
        "supervisor_office == @supervisor_office & case_status == @case_status & court_name == @court_name"
    )

    # --- Key Metrics (KPIs) ---
    st.header("Key Metrics")
    total_cases = df_filtered.shape[0]
    pending_cases = df_filtered[df_filtered["case_status"] == "Pending"].shape[0]
    decided_cases = df_filtered[df_filtered["case_status"] == "Decided"].shape[0]
    upcoming_hearings_total = df_filtered[df_filtered['next_hearing_date'] > datetime.now()].shape[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Cases", f"{total_cases}")
    col2.metric("Pending Cases", f"{pending_cases}")
    col3.metric("Decided Cases", f"{decided_cases}")
    col4.metric("Total Upcoming Hearings", f"{upcoming_hearings_total}")

    st.markdown("---")

    # --- NEW: Upcoming Hearings Section ---
    st.header("Upcoming Hearings (Next 14 Days)")
    
    # Define the date range
    today = pd.to_datetime('today').normalize()
    two_weeks_from_now = today + timedelta(days=14)

    # Filter for cases within the next 14 days
    upcoming_14_days_df = df_filtered[
        (df_filtered['next_hearing_date'] >= today) & 
        (df_filtered['next_hearing_date'] <= two_weeks_from_now)
    ].copy()

    # Sort by the hearing date
    upcoming_14_days_df = upcoming_14_days_df.sort_values(by='next_hearing_date')
    
    # Format the date for better readability
    upcoming_14_days_df['next_hearing_date'] = upcoming_14_days_df['next_hearing_date'].dt.strftime('%d-%b-%Y')


    with st.expander(f"View {len(upcoming_14_days_df)} cases with hearings in the next 14 days", expanded=True):
        if len(upcoming_14_days_df) > 0:
            # Display the relevant columns in a table
            st.dataframe(upcoming_14_days_df[[
                'case_title', 
                'supervisor_office', 
                'court_name', 
                'next_hearing_date'
            ]], use_container_width=True)
        else:
            st.info("No cases have hearings scheduled in the next 14 days based on the current filters.")

    st.markdown("---")


    # --- Visualizations ---
    st.header("Overall Visual Analytics")
    col1, col2 = st.columns(2)

    with col1:
        cases_by_supervisor = df_filtered['supervisor_office'].value_counts().reset_index()
        cases_by_supervisor.columns = ['Supervisor Office', 'Number of Cases']
        fig_supervisor = px.bar(
            cases_by_supervisor, x='Supervisor Office', y='Number of Cases',
            title='<b>Cases per Supervisor Office</b>',
            color_discrete_sequence=px.colors.qualitative.Pastel, template='plotly_white'
        )
        st.plotly_chart(fig_supervisor, use_container_width=True)

    with col2:
        status_counts = df_filtered['case_status'].value_counts().reset_index()
        status_counts.columns = ['Case Status', 'Count']
        fig_status = px.pie(
            status_counts, names='Case Status', values='Count',
            title='<b>Case Status Distribution</b>', hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_status.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_status, use_container_width=True)

    cases_by_court = df_filtered['court_name'].value_counts().reset_index()
    cases_by_court.columns = ['Court', 'Number of Cases']
    fig_court = px.bar(
        cases_by_court, x='Number of Cases', y='Court', orientation='h',
        title='<b>Cases by Court</b>',
        color_discrete_sequence=['#33A1C9'], template='plotly_white'
    )
    st.plotly_chart(fig_court, use_container_width=True)

    # --- Data Table ---
    st.markdown("---")
    st.header("Detailed Case Data")
    st.dataframe(df_filtered)
