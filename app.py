import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import calendar

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
        return df
    except Exception as e:
        st.error(f"Error loading data from Google Sheet: {e}")
        st.error("Please make sure your Google Sheet is shared with 'Anyone with the link' as a 'Viewer'.")
        return pd.DataFrame()

def render_home_page(df):
    """Renders the Home page with overall metrics and the interactive calendar."""
    st.title("⚖️ Court Cases Analysis Dashboard")
    st.markdown("Welcome! This dashboard provides a complete overview and analysis of court cases for the DC Office, Ludhiana.")
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
        
        # --- Interactive Calendar on Home Page ---
        st.header("Interactive Hearing Calendar")
        if 'view_date' not in st.session_state:
            st.session_state.view_date = datetime.today()
        if 'selected_date' not in st.session_state:
            st.session_state.selected_date = None

        nav_cols = st.columns([1, 2, 1])
        if nav_cols[0].button("⬅️ Previous Month"):
            st.session_state.view_date -= timedelta(days=30)
        nav_cols[1].subheader(st.session_state.view_date.strftime("%B %Y"))
        if nav_cols[2].button("Next Month ➡️"):
            st.session_state.view_date += timedelta(days=30)

        year, month = st.session_state.view_date.year, st.session_state.view_date.month
        cal = calendar.monthcalendar(year, month)
        hearing_dates_in_month = set(df[
            (df['next_hearing_date'].dt.year == year) & (df['next_hearing_date'].dt.month == month)
        ]['next_hearing_date'].dt.date)

        day_cols = st.columns(7)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day_name in enumerate(days):
            day_cols[i].write(f"**{day_name}**")

        for week in cal:
            week_cols = st.columns(7)
            for i, day_num in enumerate(week):
                if day_num != 0:
                    current_date = datetime(year, month, day_num).date()
                    button_type = "primary" if current_date in hearing_dates_in_month else "secondary"
                    if week_cols[i].button(str(day_num), key=f"day_{year}_{month}_{day_num}", type=button_type, use_container_width=True):
                        st.session_state.selected_date = current_date
                else:
                    week_cols[i].write("")
        
        st.markdown("---")

        # --- Display cases for selected date ---
        if st.session_state.selected_date:
            st.subheader(f"Cases with Hearing on {st.session_state.selected_date.strftime('%d-%b-%Y')}")
            cases_on_date = df[df['next_hearing_date'].dt.date == st.session_state.selected_date]
            if not cases_on_date.empty:
                st.dataframe(cases_on_date[['case_no', 'case_title', 'supervisor_office', 'court_name']], use_container_width=True)
            else:
                st.info(f"No cases found with a hearing on {st.session_state.selected_date.strftime('%d-%b-%Y')}.")
    else:
        st.warning("Could not load data to display metrics.")

def render_dashboard_page(df):
    """Renders the detailed dashboard with filters, charts, and data tables."""
    st.title("📊 Detailed Dashboard")
    
    # --- Sidebar Filters ---
    st.sidebar.header("Dashboard Filters")
    supervisor_office = st.sidebar.multiselect(
        "Select Supervisor Office", options=df["supervisor_office"].unique(), default=df["supervisor_office"].unique()
    )
    case_status = st.sidebar.multiselect(
        "Select Case Status", options=df["case_status"].unique(), default=df["case_status"].unique()
    )
    court_name_filter = st.sidebar.multiselect(
        "Select Court", options=df["court_name"].unique(), default=df["court_name"].unique()
    )
    
    df_filtered = df.query(
        "supervisor_office == @supervisor_office & case_status == @case_status & court_name == @court_name_filter"
    )

    # --- Main Page Content ---
    today = pd.to_datetime('today').normalize()
    
    # --- NEW: Interactive Drill-Down Chart ---
    st.header("Interactive Court Analytics")

    # Top-level chart: Cases by Court
    cases_by_court = df_filtered['court_name'].value_counts().reset_index()
    cases_by_court.columns = ['Court', 'Number of Cases']
    fig_court_main = px.bar(
        cases_by_court, 
        x='Court', 
        y='Number of Cases', 
        title='<b>Total Cases by Court</b>',
        color_discrete_sequence=['#33A1C9']
    )
    st.plotly_chart(fig_court_main, use_container_width=True)

    # Drill-down selection
    court_options = ['-- Select a court to see monthly breakdown --'] + list(cases_by_court['Court'])
    selected_court = st.selectbox("Select a Court to Drill Down", options=court_options)

    # Second-level chart: Monthly breakdown
    if selected_court != '-- Select a court to see monthly breakdown --':
        st.subheader(f"Monthly Case Distribution for: {selected_court}")
        
        monthly_df = df_filtered[df_filtered['court_name'] == selected_court].copy()
        monthly_df['month'] = monthly_df['next_hearing_date'].dt.to_period('M').astype(str)
        
        monthly_counts = monthly_df['month'].value_counts().sort_index().reset_index()
        monthly_counts.columns = ['Month', 'Number of Cases']
        
        fig_monthly = px.bar(
            monthly_counts,
            x='Month',
            y='Number of Cases',
            title=f"<b>Cases in {selected_court} by Month</b>"
        )
        st.plotly_chart(fig_monthly, use_container_width=True)

    st.markdown("---")
    
    st.header("Upcoming Hearings (Next 14 Days)")
    two_weeks_from_now = today + timedelta(days=14)
    upcoming_14_days_df = df_filtered[(df_filtered['next_hearing_date'] >= today) & (df_filtered['next_hearing_date'] <= two_weeks_from_now)].copy()
    upcoming_14_days_df = upcoming_14_days_df.sort_values(by='next_hearing_date')
    upcoming_14_days_df['next_hearing_date_formatted'] = upcoming_14_days_df['next_hearing_date'].dt.strftime('%d-%b-%Y')
    with st.expander(f"View {len(upcoming_14_days_df)} cases with hearings in the next 14 days", expanded=False):
        if not upcoming_14_days_df.empty:
            st.dataframe(upcoming_14_days_df[['case_no', 'case_title', 'supervisor_office', 'court_name', 'next_hearing_date_formatted']].rename(columns={'next_hearing_date_formatted': 'Next Hearing Date'}), use_container_width=True)
        else:
            st.info("No cases have hearings scheduled in the next 14 days.")

    st.header("Complete List of All Upcoming Hearings")
    all_upcoming_df = df_filtered[df_filtered['next_hearing_date'] >= today].copy()
    all_upcoming_df = all_upcoming_df.sort_values(by='next_hearing_date')
    all_upcoming_df['next_hearing_date_formatted'] = all_upcoming_df['next_hearing_date'].dt.strftime('%d-%b-%Y')
    with st.expander(f"View all {len(all_upcoming_df)} upcoming cases", expanded=False):
        if not all_upcoming_df.empty:
            st.dataframe(all_upcoming_df[['case_no', 'case_title', 'supervisor_office', 'court_name', 'next_hearing_date_formatted']].rename(columns={'next_hearing_date_formatted': 'Next Hearing Date'}), use_container_width=True)
        else:
            st.info("No upcoming hearings found.")

    st.markdown("---")
    st.header("Detailed Case Data")
    st.dataframe(df_filtered)

# --- App Entry Point ---
SHEET_ID = "1lmN_fpYqk63Zq8P1cJMtFD_5UpVbGYXvTa5hU1G6eLM" 
GID = "322810088"
df = load_data(SHEET_ID, GID)

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Detailed Dashboard"])

if page == "Home":
    render_home_page(df)
elif page == "Detailed Dashboard":
    if not df.empty:
        render_dashboard_page(df)
    else:
        st.warning("Could not load data. Please check the Google Sheet link and sharing permissions.")
