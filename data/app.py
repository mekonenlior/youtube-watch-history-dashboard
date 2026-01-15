import json
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime
import os

st.title("My YouTube Watch History Dashboard")

# Load Data
DATA_FILE = "data/watch-history.json"

if not os.path.exists(DATA_FILE):
    st.error(f"Data file not found: {DATA_FILE}. Upload your watch-history.json from Google Takeout.")
    st.stop()

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

# Parse into DataFrame
records = []
for entry in raw_data:
    if 'titleUrl' not in entry or 'time' not in entry:
        continue  # skip invalid entries
    title = entry.get('title', '').replace('Watched ', '')
    url = entry['titleUrl']
    video_id = url.split('v=')[-1] if 'v=' in url else None
    timestamp = datetime.fromisoformat(entry['time'].replace('Z', '+00:00'))
    channel = entry.get('subtitles', [{}])[0].get('name', 'Unknown') if 'subtitles' in entry else 'Unknown'

    records.append({
        'title': title,
        'video_id': video_id,
        'channel': channel,
        'time': timestamp,
        'date': timestamp.date(),
        'hour': timestamp.hour,
        'weekday': timestamp.strftime('%A')
    })

df = pd.DataFrame(records)
df['time'] = pd.to_datetime(df['time'])  # ensure datetime

st.success(f"Loaded {len(df):,} watch entries!")

# Basic stats
col1, col2, col3 = st.columns(3)
col1.metric("Total Videos Watched", len(df))
col2.metric("Unique Channels", df['channel'].nunique())
col3.metric("Date Range", f"{df['date'].min().date()} → {df['date'].max().date()}")

# Top channels
top_channels = df['channel'].value_counts().head(15).reset_index()
fig_channels = px.bar(top_channels, x='count', y='channel', title="Top Channels", orientation='h')
st.plotly_chart(fig_channels)

# Views over time
df['month'] = df['time'].dt.to_period('M')
monthly = df.groupby('month').size().reset_index(name='count')
monthly['month'] = monthly['month'].astype(str)
fig_time = px.line(monthly, x='month', y='count', title="Monthly Watch Count")
st.plotly_chart(fig_time)

# Heatmap: hour vs weekday
heatmap_data = df.pivot_table(index='weekday', columns='hour', values='title', aggfunc='count', fill_value=0)
fig_heatmap = px.imshow(heatmap_data, title="Watch Heatmap (Weekday vs Hour)", color_continuous_scale='Blues')
st.plotly_chart(fig_heatmap)

# Bonus: Top videos (if no duplicates removed)
top_videos = df['title'].value_counts().head(10)
st.subheader("Most Repeated Videos")
st.dataframe(top_videos)