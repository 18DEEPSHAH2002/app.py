import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Page Configuration ---
# Sets the title and icon that appear in the browser tab
st.set_page_config(
    page_title="Court Cases Dashboard",
    page_icon="⚖️",
    layout="wide",
)

# --- Data Loading and Cleaning ---
# Using st.cache_data tells Streamlit to only load the data once,
# which makes the app faster.
@st.cache_data
def load_data(path):
    """Loads and cleans the court case data from the specified CSV file."""
    try:
        # Load the data, skipping the first row which might be a title
        df = pd.read_csv(path, skiprows=1)

        # --- Data Cleaning and Preprocessing ---
        # Rename columns for easier access
        df.columns = [
            's_no', 'supervisor_office', 'branch_name', 'clerk', 'case_no',
            'case_title', 'case_status', 'status_comment', 'pending_stage',
            'court_name', 'dc_action_needed', 'dc_action_to_be_taken',
            'reply_by', 'reply_filed', 'next_hearing_date', 'case_detail',
            'court_directions', 'direction_details', 'compliance_of_direction',
            'status_reply_required', 'status_reply_filed', 'case_documents',
            'remarks', 'days_left'
        ]

        # Drop the first row which contains the original headers
        df = df.iloc[1:].reset_index(drop=True)

        # Drop rows where 's_no' is NaN, as they are likely empty
        df.dropna(subset=['s_no'], inplace=True)

        # Standardize 'case_status' for consistency
        df['case_status'] = df['case_status'].str.strip().str.title()
        df['case_status'] = df['case_status'].fillna('Not Specified')
        status_replacements = {
            'Pending': 'Pending',
            'Decided': 'Decided',
            'Dismissed': 'Decided',
            'Disposed': 'Decided',
        }
        df['case_status'] = df['case_status'].replace(status_replacements).fillna('Not Specified')

        # Clean and standardize 'court_name'
        df['court_name'] = df['court_name'].str.strip().str.title()
        df['court_name'] = df['court_name'].fillna('Not Specified')
        court_replacements = {
            'Punjab And Haryana High Court': 'High Court',
            'District Court Ludhiana': 'District Court',
            'Supreme Court Of India': 'Supreme Court'
        }
        df['court_name'] = df['court_name'].replace(court_replacements)

        # Convert 'next_hearing_date' to datetime objects for calculations
        df['next_hearing_date'] = pd.to_datetime(df['next_hearing_date'], errors='coerce')

        # Fill missing supervisor_office values
        df['supervisor_office'] = df['supervisor_office'].fillna('Not Assigned')

        return df
    except FileNotFoundError:
        # Show an error in the app if the data file is not found
        st.error(f"Error: The file '{path}' was not found in the GitHub repository.")
        return pd.DataFrame() # Return an empty DataFrame on error

# --- Main App Logic ---
# Define the path to your data file in the GitHub repository
FILE_PATH = 'Court Cases List DC Office Ludhiana.xlsx - Main Sheet.csv'
df = load_data(FILE_PATH)

# Only run the app if the data was loaded successfully
if not df.empty:
    # --- Page Title ---
    st.title("⚖️ Court Cases Analysis Dashboard")
    st.markdown("An interactive dashboard to monitor and analyze court cases for the DC Office, Ludhiana.")

    # --- Sidebar Filters ---
    st.sidebar.header("Dashboard Filters")

    # Filter by Supervisor Office
    supervisor_office = st.sidebar.multiselect(
        "Select Supervisor Office",
        options=df["supervisor_office"].unique(),
        default=df["supervisor_office"].unique()
    )

    # Filter by Case Status
    case_status = st.sidebar.multiselect(
        "Select Case Status",
        options=df["case_status"].unique(),
        default=df["case_status"].unique()
    )

    # Filter by Court Name
    court_name = st.sidebar.multiselect(
        "Select Court",
        options=df["court_name"].unique(),
        default=df["court_name"].unique()
    )

    # Filter the DataFrame based on the user's selections in the sidebar
    df_filtered = df.query(
        "supervisor_office == @supervisor_office & case_status == @case_status & court_name == @court_name"
    )

    # --- Key Metrics (KPIs) ---
    st.header("Key Metrics")
    total_cases = df_filtered.shape[0]
    pending_cases = df_filtered[df_filtered["case_status"] == "Pending"].shape[0]
    decided_cases = df_filtered[df_filtered["case_status"] == "Decided"].shape[0]
    # Calculate upcoming hearings by checking if the date is in the future
    upcoming_hearings = df_filtered[df_filtered['next_hearing_date'] > datetime.now()].shape[0]

    # Display the metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Cases", f"{total_cases}")
    col2.metric("Pending Cases", f"{pending_cases}")
    col3.metric("Decided Cases", f"{decided_cases}")
    col4.metric("Upcoming Hearings", f"{upcoming_hearings}")

    st.markdown("---")

    # --- Visualizations ---
    st.header("Visual Analytics")
    col1, col2 = st.columns(2)

    with col1:
        # Bar Chart: Cases by Supervisor Office
        cases_by_supervisor = df_filtered['supervisor_office'].value_counts().reset_index()
        cases_by_supervisor.columns = ['Supervisor Office', 'Number of Cases']
        fig_supervisor = px.bar(
            cases_by_supervisor,
            x='Supervisor Office',
            y='Number of Cases',
            title='<b>Cases per Supervisor Office</b>',
            color_discrete_sequence=px.colors.qualitative.Pastel,
            template='plotly_white'
        )
        st.plotly_chart(fig_supervisor, use_container_width=True)

    with col2:
        # Pie Chart: Cases by Status
        status_counts = df_filtered['case_status'].value_counts().reset_index()
        status_counts.columns = ['Case Status', 'Count']
        fig_status = px.pie(
            status_counts,
            names='Case Status',
            values='Count',
            title='<b>Case Status Distribution</b>',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_status.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_status, use_container_width=True)

    # Bar Chart: Cases by Court
    cases_by_court = df_filtered['court_name'].value_counts().reset_index()
    cases_by_court.columns = ['Court', 'Number of Cases']
    fig_court = px.bar(
        cases_by_court,
        x='Number of Cases',
        y='Court',
        orientation='h',
        title='<b>Cases by Court</b>',
        color_discrete_sequence=['#33A1C9'],
        template='plotly_white'
    )
    st.plotly_chart(fig_court, use_container_width=True)

    # --- Data Table ---
    st.markdown("---")
    st.header("Detailed Case Data")
    st.dataframe(df_filtered)

else:
    st.warning("Data could not be loaded. Please check that the file is in the repository and the path is correct.")
