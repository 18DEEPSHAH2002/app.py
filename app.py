import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Task Analysis Dashboard",
    page_icon="📊",
    layout="wide",
)

# --- Data Loading and Caching ---
@st.cache_data
def load_data():
    """
    Loads data from the specified Google Sheet URL.
    The data is cached to improve performance.
    """
    # Construct the correct URL to download the Google Sheet as a CSV
    sheet_id = "14howESk1k414yH06e_hG8mCE0HYUcR5VFTnbro4IdiU"
    sheet_gid = "345729707"  # Specific GID for your sheet tab
    
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={sheet_gid}"
    
    try:
        # Read the data into a pandas DataFrame
        df = pd.read_csv(csv_url)
        
        # --- FIX 1: Strip leading/trailing whitespace from all column names ---
        df.columns = df.columns.str.strip()
        
        # --- FIX 2: Strip leading/trailing whitespace from the 'Priority' and 'Status' column values ---
        if 'Priority' in df.columns:
            df['Priority'] = df['Priority'].str.strip()
        if 'Status' in df.columns:
            df['Status'] = df['Status'].str.strip()
        
        # --- Data Cleaning and Preprocessing ---
        # Rename columns to be more script-friendly
        df.rename(columns={
            'Entry Date': 'Start Date',
            'Marked to Officer': 'Assign To'
        }, inplace=True)

        # Convert date columns to datetime objects, handling potential errors
        df['Start Date'] = pd.to_datetime(df['Start Date'], errors='coerce')
        
        # Drop rows where essential columns are missing
        df.dropna(subset=['Priority', 'Dealing Branch', 'Assign To', 'Start Date'], inplace=True)
        
        return df
    except Exception as e:
        st.error(f"Error loading data from Google Sheet: {e}. Please ensure the sheet is public ('Anyone with the link can view') and the GID is correct.")
        return pd.DataFrame() # Return an empty DataFrame on error

# --- Load Data ---
df = load_data()

# --- Sidebar for Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Incomplete Work Analysis"])

# --- Main Application ---
if page == "Dashboard":
    st.title("📊 Task Management Analysis Dashboard")
    st.markdown("---")

    if not df.empty:
        # --- Key Metrics ---
        st.header("Key Performance Indicators")

        # Filter data based on priority
        most_urgent_tasks = df[df['Priority'] == 'Most Urgent']
        medium_priority_tasks = df[df['Priority'] == 'Medium']
        
        # Calculate metrics
        total_tasks = len(df)
        num_most_urgent = len(most_urgent_tasks)
        num_medium_priority = len(medium_priority_tasks)

        # Display metrics in columns
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tasks", f"{total_tasks} 📝")
        col2.metric("Most Urgent Tasks", f"{num_most_urgent} 🔥")
        col3.metric("Medium Priority Tasks", f"{num_medium_priority} ⚠️")

        st.markdown("---")

        # --- Visualizations ---
        st.header("Task Distribution Analysis")

        # Create two columns for the graphs
        viz_col1, viz_col2 = st.columns(2)

        with viz_col1:
            st.subheader("Most Urgent Tasks by Dealing Branch")
            if not most_urgent_tasks.empty:
                urgent_by_branch = most_urgent_tasks['Dealing Branch'].value_counts().reset_index()
                urgent_by_branch.columns = ['Dealing Branch', 'Number of Tasks']
                fig1 = px.bar(urgent_by_branch, x='Dealing Branch', y='Number of Tasks', title='Most Urgent Tasks per Dealing Branch', color='Dealing Branch', text='Number of Tasks')
                fig1.update_traces(textposition='outside')
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.warning("No 'Most Urgent' tasks to display.")

            st.subheader("Medium Priority Tasks by Dealing Branch")
            if not medium_priority_tasks.empty:
                medium_by_branch = medium_priority_tasks['Dealing Branch'].value_counts().reset_index()
                medium_by_branch.columns = ['Dealing Branch', 'Number of Tasks']
                fig2 = px.bar(medium_by_branch, x='Dealing Branch', y='Number of Tasks', title='Medium Priority Tasks per Dealing Branch', color='Dealing Branch', text='Number of Tasks')
                fig2.update_traces(textposition='outside')
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("No 'Medium' priority tasks to display.")

        with viz_col2:
            st.subheader("Most Urgent Tasks by Officer")
            if not most_urgent_tasks.empty:
                urgent_by_officer = most_urgent_tasks['Assign To'].value_counts().reset_index()
                urgent_by_officer.columns = ['Officer', 'Number of Tasks']
                fig3 = px.bar(urgent_by_officer, x='Officer', y='Number of Tasks', title='Most Urgent Tasks per Officer', color='Officer', text='Number of Tasks')
                fig3.update_traces(textposition='outside')
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.warning("No 'Most Urgent' tasks to display.")

            st.subheader("Medium Priority Tasks by Officer")
            if not medium_priority_tasks.empty:
                medium_by_officer = medium_priority_tasks['Assign To'].value_counts().reset_index()
                medium_by_officer.columns = ['Officer', 'Number of Tasks']
                fig4 = px.bar(medium_by_officer, x='Officer', y='Number of Tasks', title='Medium Priority Tasks per Officer', color='Officer', text='Number of Tasks')
                fig4.update_traces(textposition='outside')
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.warning("No 'Medium' priority tasks to display.")

        st.markdown("---")

        # --- Pending Task Analysis ---
        st.header("Pending Task Analysis")
        
        today = datetime.now()
        if 'Status' in df.columns:
            pending_tasks = df[(df['Status'] != 'Completed') & (df['Start Date'] < today)]
        else:
            pending_tasks = df[df['Start Date'] < today]
            st.info("Note: 'Status' column not found. Pending tasks are calculated based on the 'Start Date'.")

        if not pending_tasks.empty:
            pending_col1, pending_col2 = st.columns(2)
            with pending_col1:
                st.subheader("Pending Tasks by Dealing Branch")
                pending_by_branch = pending_tasks['Dealing Branch'].value_counts().reset_index()
                pending_by_branch.columns = ['Dealing Branch', 'Number of Pending Tasks']
                fig5 = px.bar(pending_by_branch, x='Dealing Branch', y='Number of Pending Tasks', title='Pending Tasks per Dealing Branch', color='Dealing Branch', text='Number of Pending Tasks')
                fig5.update_traces(textposition='outside')
                st.plotly_chart(fig5, use_container_width=True)
            with pending_col2:
                st.subheader("Pending Tasks by Officer")
                pending_by_officer = pending_tasks['Assign To'].value_counts().reset_index()
                pending_by_officer.columns = ['Officer', 'Number of Pending Tasks']
                fig6 = px.bar(pending_by_officer, x='Officer', y='Number of Pending Tasks', title='Pending Tasks per Officer', color='Officer', text='Number of Pending Tasks')
                fig6.update_traces(textposition='outside')
                st.plotly_chart(fig6, use_container_width=True)
        else:
            st.info("Congratulations! There are no pending tasks.")
    else:
        st.warning("Could not load data. Please check the Google Sheet link and ensure its sharing permissions are set to 'Anyone with the link'.")

elif page == "Incomplete Work Analysis":
    st.title("📋 Incomplete Work Analysis")
    st.markdown("---")

    if not df.empty and 'Status' in df.columns:
        incomplete_tasks = df[df['Status'] != 'Completed'].copy()

        st.header("Filter Incomplete Tasks")
        
        # Create filters
        branches = ['All'] + sorted(incomplete_tasks['Dealing Branch'].unique().tolist())
        officers = ['All'] + sorted(incomplete_tasks['Assign To'].unique().tolist())
        
        col1, col2 = st.columns(2)
        with col1:
            selected_branch = st.selectbox("Filter by Dealing Branch", branches)
        with col2:
            selected_officer = st.selectbox("Filter by Officer", officers)
            
        # Apply filters
        filtered_df = incomplete_tasks.copy()
        if selected_branch != 'All':
            filtered_df = filtered_df[filtered_df['Dealing Branch'] == selected_branch]
        if selected_officer != 'All':
            filtered_df = filtered_df[filtered_df['Assign To'] == selected_officer]

        st.markdown("---")
        st.header(f"Found {len(filtered_df)} Incomplete Task(s)")

        if not filtered_df.empty:
            # Display the filtered tasks
            st.dataframe(filtered_df[['Assign To', 'Dealing Branch', 'Subject', 'File', 'Priority', 'Start Date']])
        else:
            st.info("No incomplete tasks match the current filter criteria.")

    elif 'Status' not in df.columns:
        st.error("The 'Status' column is required for this analysis but was not found in the data.")
    else:
        st.warning("Could not load data to perform analysis.")
