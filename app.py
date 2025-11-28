import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Player Injury Impact Dashboard",
    page_icon="⚽",
    layout="wide"
)

# --- 1. DATA LOADING (LOOKS IN ROOT FOLDER) ---
@st.cache_data
def load_data():
    filename = 'player_injuries_impact.csv'
    
    # Check if file exists in current directory
    if not os.path.exists(filename):
        st.error(f"Error: The file '{filename}' was not found in the directory: {os.getcwd()}")
        st.stop()
        
    df = pd.read_csv(filename)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# --- 2. DATA CLEANING & PREPARATION (Per PDF Requirements) ---
# The PDF asks to clean data and calculate metrics.

# Convert Date columns to datetime objects
# The format in CSV is like "Nov 12, 2022"
df['Date of Injury'] = pd.to_datetime(df['Date of Injury'], errors='coerce')
df['Date of return'] = pd.to_datetime(df['Date of return'], errors='coerce')

# Calculate "Recovery Duration" in days (New Metric)
df['Recovery Duration'] = (df['Date of return'] - df['Date of Injury']).dt.days

# Handle Missing Values (Drop rows where crucial dates are missing for calculation)
df_clean = df.dropna(subset=['Recovery Duration', 'Team Name', 'Position'])

# Clean up Result columns for Impact Analysis
# We want to see how the team performed while the player was missing
missed_match_cols = [col for col in df.columns if 'missed_match_Result' in col]

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter Data")

# Filter by Team
teams = sorted(df_clean['Team Name'].unique())
selected_teams = st.sidebar.multiselect("Select Team(s)", teams, default=teams[:3])

# Filter by Position
positions = sorted(df_clean['Position'].unique())
selected_positions = st.sidebar.multiselect("Select Position(s)", positions, default=positions)

# Apply Filters
if selected_teams:
    df_filtered = df_clean[df_clean['Team Name'].isin(selected_teams)]
else:
    df_filtered = df_clean

if selected_positions:
    df_filtered = df_filtered[df_filtered['Position'].isin(selected_positions)]

# --- MAIN DASHBOARD ---
st.title("⚽ Player Injuries Impact Dashboard")
st.markdown("Analyzing the impact of player injuries on team performance and recovery trends.")

# --- TOP METRICS (KPIs) ---
total_injuries = len(df_filtered)
avg_recovery = df_filtered['Recovery Duration'].mean()
most_common_injury = df_filtered['Injury'].mode()[0] if not df_filtered.empty else "N/A"

col1, col2, col3 = st.columns(3)
col1.metric("Total Injuries Recorded", total_injuries)
col2.metric("Avg. Recovery Time", f"{avg_recovery:.1f} Days")
col3.metric("Most Common Injury", most_common_injury)

st.markdown("---")

# --- VISUALIZATIONS (5 Compulsory Charts adapted to Data) ---

col_chart1, col_chart2 = st.columns(2)

# Chart 1: Bar Chart - Injuries by Team
with col_chart1:
    st.subheader("1. Injury Count by Team")
    injuries_by_team = df_filtered['Team Name'].value_counts().reset_index()
    injuries_by_team.columns = ['Team Name', 'Count']
    fig1 = px.bar(injuries_by_team, x='Team Name', y='Count', color='Team Name', 
                  title="Total Injuries per Team")
    st.plotly_chart(fig1, use_container_width=True)

# Chart 2: Pie Chart - Distribution of Positions Injured
with col_chart2:
    st.subheader("2. Injuries by Position")
    fig2 = px.pie(df_filtered, names='Position', title="Distribution of Injuries by Player Position",
                  hole=0.4)
    st.plotly_chart(fig2, use_container_width=True)

col_chart3, col_chart4 = st.columns(2)

# Chart 3: Histogram - Recovery Time Distribution
with col_chart3:
    st.subheader("3. Recovery Time Analysis")
    fig3 = px.histogram(df_filtered, x="Recovery Duration", nbins=20, 
                        title="Distribution of Recovery Days",
                        color_discrete_sequence=['#FFA07A'])
    fig3.update_layout(xaxis_title="Days to Recover", yaxis_title="Number of Players")
    st.plotly_chart(fig3, use_container_width=True)

# Chart 4: Scatter Plot - Age vs Recovery Time
with col_chart4:
    st.subheader("4. Age vs. Recovery Duration")
    fig4 = px.scatter(df_filtered, x="Age", y="Recovery Duration", 
                      color="Injury", size="FIFA rating",
                      hover_data=['Name', 'Team Name'],
                      title="Does Age affect Recovery Time?")
    st.plotly_chart(fig4, use_container_width=True)

# Chart 5: Stacked Bar - Team Performance Without the Player (Impact Analysis)
st.subheader("5. Team Performance During Player Absence")
st.markdown("Aggregated results of matches missed by injured players.")

# Logic to aggregate win/loss/draw from the 'missed_match' columns
results_list = []
for col in missed_match_cols:
    results_list.extend(df_filtered[col].dropna().tolist())

if results_list:
    results_df = pd.DataFrame(results_list, columns=['Result'])
    # Clean up standard variations (e.g., ensuring lowercase consistency if needed)
    results_df['Result'] = results_df['Result'].str.lower()
    
    res_counts = results_df['Result'].value_counts().reset_index()
    res_counts.columns = ['Match Result', 'Count']
    
    fig5 = px.bar(res_counts, x='Match Result', y='Count', color='Match Result',
                  color_discrete_map={'win': 'green', 'lose': 'red', 'draw': 'gray'},
                  title="Total Match Outcomes While Selected Players Were Injured")
    st.plotly_chart(fig5, use_container_width=True)
else:
    st.info("No missed match data available for current selection.")

# --- DATA TABLE VIEW ---
with st.expander("View Raw Data"):
    st.dataframe(df_filtered)
