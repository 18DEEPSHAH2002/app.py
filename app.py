import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Court Cases Dashboard",
    page_icon="⚖️",
    layout="wide",
)

# --- Data Loading and Cleaning from Google Sheets ---
@st.cache_data(ttl=600)
def load_data(sheet_id, gid="0"):
    """Loads and cleans data from a public Google Sheet."""
    try:
        url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}'
        df = pd.read_csv(url, skiprows=1)
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
        # Create month-year and date columns for easier grouping
        df['hearing_month'] = df['next_hearing_date'].dt.to_period('M').astype(str)
        df['hearing_date'] = df['next_hearing_date'].dt.strftime('%Y-%m-%d')
        return df
    except Exception as e:
        st.error(f"Error loading data from Google Sheet: {e}")
        st.error("Please make sure your Google Sheet is shared with 'Anyone with the link' as a 'Viewer'.")
        return pd.DataFrame()

# --- Main App ---
SHEET_ID = "1lmN_fpYqk63Zq8P1cJMtFD_5UpVbGYXvTa5hU1G6eLM" 
GID = "322810088"
df = load_data(SHEET_ID, GID)

# Initialize session state for selections
if 'selected_court' not in st.session_state:
    st.session_state.selected_court = None
if 'selected_month' not in st.session_state:
    st.session_state.selected_month = None
if 'selected_department' not in st.session_state:
    st.session_state.selected_department = None

st.title("⚖️ Court Cases Analysis Dashboard")
st.markdown("An interactive dashboard for the DC Office, Ludhiana, with multi-level case analysis.")
st.markdown("---")

if not df.empty:
    # --- Key Metrics ---
    st.header("Overall Key Metrics")
    total_cases = df.shape[0]
    pending_cases = df[df["case_status"] == "Pending"].shape[0]
    decided_cases = df[df["case_status"] == "Decided"].shape[0]
    upcoming_hearings_total = df[df['next_hearing_date'] > datetime.now()].shape[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Cases", f"{total_cases}")
    col2.metric("Pending Cases", f"{pending_cases}")
    col3.metric("Decided Cases", f"{decided_cases}")
    col4.metric("Total Upcoming Hearings", f"{upcoming_hearings_total}")
    st.markdown("---")

    # --- Interactive Drill-Down Section ---
    st.header("Interactive Case Analysis")

    # Level 1: Cases by Court
    st.subheader("Level 1: Case Distribution by Court")
    cases_by_court = df['court_name'].value_counts().reset_index()
    cases_by_court.columns = ['Court', 'Number of Cases']
    fig_court_main = px.bar(
        cases_by_court, 
        x='Court', 
        y='Number of Cases', 
        title='<b>Total Cases by Court</b>',
        color_discrete_sequence=px.colors.qualitative.Pastel1
    )
    st.plotly_chart(fig_court_main, use_container_width=True)

    # Create buttons for each court to enable drill-down
    st.write("Click a court to see the monthly breakdown:")
    court_cols = st.columns(len(cases_by_court))
    for i, court_name in enumerate(cases_by_court['Court']):
        if court_cols[i].button(court_name, key=f"court_{court_name}"):
            st.session_state.selected_court = court_name
            st.session_state.selected_month = None
            st.session_state.selected_department = None
    
    # Level 2: Monthly breakdown for a selected court
    if st.session_state.selected_court:
        st.markdown("---")
        st.subheader(f"Level 2: Monthly Breakdown for {st.session_state.selected_court}")

        monthly_df = df[df['court_name'] == st.session_state.selected_court].copy()
        monthly_counts = monthly_df['hearing_month'].value_counts().sort_index().reset_index()
        monthly_counts.columns = ['Month', 'Number of Cases']
        
        fig_monthly = px.bar(
            monthly_counts,
            x='Month',
            y='Number of Cases',
            title=f"<b>Monthly Case Distribution for {st.session_state.selected_court}</b>",
            color_discrete_sequence=px.colors.qualitative.Pastel2
        )
        st.plotly_chart(fig_monthly, use_container_width=True)
        
        st.write("Click a month to see the department breakdown:")
        month_cols = st.columns(min(len(monthly_counts), 12)) # Avoid too many columns
        for i, month_name in enumerate(monthly_counts['Month']):
            if month_cols[i % 12].button(month_name, key=f"month_{month_name}"):
                st.session_state.selected_month = month_name
                st.session_state.selected_department = None

        if st.button("Clear Court Selection"):
            st.session_state.selected_court = None
            st.session_state.selected_month = None
            st.session_state.selected_department = None


    # Level 3: Department breakdown for a selected month and court
    if st.session_state.selected_court and st.session_state.selected_month:
        st.markdown("---")
        st.subheader(f"Level 3: Department Breakdown for {st.session_state.selected_court} in {st.session_state.selected_month}")
        
        department_df = df[
            (df['court_name'] == st.session_state.selected_court) & 
            (df['hearing_month'] == st.session_state.selected_month)
        ].copy()
        department_counts = department_df['supervisor_office'].value_counts().reset_index()
        department_counts.columns = ['Department', 'Number of Cases']

        fig_department = px.bar(
            department_counts,
            x='Department',
            y='Number of Cases',
            title=f"<b>Department Cases in {st.session_state.selected_court} for {st.session_state.selected_month}</b>",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_department, use_container_width=True)

        st.write("Click a department to see the daily breakdown:")
        dept_cols = st.columns(min(len(department_counts), 8))
        for i, dept_name in enumerate(department_counts['Department']):
            if dept_cols[i % 8].button(dept_name, key=f"dept_{dept_name}"):
                st.session_state.selected_department = dept_name

        if st.button("Clear Month Selection"):
            st.session_state.selected_month = None
            st.session_state.selected_department = None

    # Level 4: Show daily breakdown graph for the selected department
    if st.session_state.selected_court and st.session_state.selected_month and st.session_state.selected_department:
        st.markdown("---")
        st.subheader(f"Level 4: Daily Case Distribution for {st.session_state.selected_department} in {st.session_state.selected_month}")

        # Filter data for the specific selections
        daily_df = df[
            (df['court_name'] == st.session_state.selected_court) &
            (df['hearing_month'] == st.session_state.selected_month) &
            (df['supervisor_office'] == st.session_state.selected_department)
        ].copy()

        # Group by date and count cases
        daily_counts = daily_df['hearing_date'].value_counts().sort_index().reset_index()
        daily_counts.columns = ['Date', 'Number of Cases']

        if not daily_counts.empty:
            fig_daily = px.bar(
                daily_counts,
                x='Date',
                y='Number of Cases',
                title=f"<b>Daily Cases for {st.session_state.selected_department} in {st.session_state.selected_month}</b>",
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            st.plotly_chart(fig_daily, use_container_width=True)
        else:
            st.info("No specific hearing dates found for this selection.")

        if st.button("Clear Department Selection"):
            st.session_state.selected_department = None

else:
    st.warning("Could not load data. Please check the Google Sheet link and sharing permissions.")
