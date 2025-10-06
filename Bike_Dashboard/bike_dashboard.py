import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime
import os

# إعداد الصفحة
st.set_page_config(page_title="Bike Trips Dashboard", layout="wide")

# CSS مخصص لتحسين الشكل
st.markdown("""
<style>
.stMetric > div > div > div > div {
    background-color: #f0f2f6;
    padding: 10px;
    border-radius: 5px;
}
</style>
""", unsafe_allow_html=True)

# تحميل البيانات
@st.cache_data
def load_data(path):
    if not os.path.exists(path):
        st.error(f"File not found at {path}! Please check the file path.")
        return pd.DataFrame()
    try:
        cols = [
            'duration_sec', 'start_time', 'end_time', 'start_station_id', 'start_station_name',
            'start_station_latitude', 'start_station_longitude', 'end_station_id', 'end_station_name',
            'end_station_latitude', 'end_station_longitude', 'bike_id', 'user_type',
            'member_birth_year', 'member_gender', 'bike_share_for_all_trip'
        ]
        df = pd.read_csv(path, usecols=lambda x: x in cols, low_memory=False)
        
        # تحويل الأعمدة الرقمية فقط
        for col in ['duration_sec', 'member_birth_year', 'start_station_id', 'end_station_id']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # إنشاء duration_min و duration_hrs
        df['duration_min'] = df['duration_sec'] / 60.0
        df['duration_hrs'] = df['duration_min'] / 60.0
        
        # إنشاء member_age
        if 'member_birth_year' in df.columns:
            df['member_age'] = 2025 - df['member_birth_year']
            df['member_age'] = df['member_age'].clip(0, 100)  # تحديد نطاق العمر
        
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return pd.DataFrame()

# مسار الملف
file_path = r"D:\DEPI_F\try\clean_data.csv"
df = load_data(file_path)

# التحقق من البيانات
if df.empty:
    st.error("No data loaded. Please check the file and try again.")
    st.stop()

# فلاتر في الـ Sidebar
st.sidebar.header("Filters")
gender_filter = st.sidebar.multiselect("Gender", options=df['member_gender'].dropna().unique(), default=df['member_gender'].dropna().unique())
user_type_filter = st.sidebar.multiselect("User Type", options=df['user_type'].dropna().unique(), default=df['user_type'].dropna().unique())

# تطبيق الفلاتر
filtered_df = df.copy()
if gender_filter:
    filtered_df = filtered_df[filtered_df['member_gender'].isin(gender_filter)]
if user_type_filter:
    filtered_df = filtered_df[filtered_df['user_type'].isin(user_type_filter)]

# عنوان الداشبورد
st.markdown("""
## 🚲 Bike Trips Dashboard
Explore bike trip patterns, durations, user demographics, and station popularity. Use the sidebar filters to drill down.
""")

# Tabs للتنظيم
tab1, tab2 = st.tabs(["📊 Dashboard", "🔍 Raw Data"])

with tab1:
    # KPIs
    st.subheader("Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Trips", value=len(filtered_df), delta=f"{len(filtered_df) - len(df):+}")
    with col2:
        avg_dur = filtered_df['duration_min'].mean() if 'duration_min' in filtered_df.columns else 0
        st.metric("Avg Duration (min)", value=f"{avg_dur:.2f}")
    with col3:
        active_bikes = filtered_df['bike_id'].nunique() if 'bike_id' in filtered_df.columns else 0
        st.metric("Active Users (Bikes)", value=active_bikes)
    with col4:
        popular_start = filtered_df['start_station_name'].mode().iloc[0] if 'start_station_name' in filtered_df.columns and not filtered_df['start_station_name'].mode().empty else "N/A"
        st.metric("Most Popular Station", value=popular_start)
    
    # Charts
    st.subheader("Visualizations")
    col_a, col_b = st.columns(2)
    
    # Pie Chart: Gender
    if 'member_gender' in filtered_df.columns:
        with col_a:
            st.subheader("Gender Distribution")
            gender_counts = filtered_df['member_gender'].value_counts().reset_index()
            gender_counts.columns = ['member_gender', 'count']
            fig_gender = px.pie(
                gender_counts,
                values='count',
                names='member_gender',
                title="Trips by Gender"
            )
            fig_gender.update_traces(textinfo='percent+value+label')  # إظهار الجنس والعدد والنسبة
            st.plotly_chart(fig_gender, use_container_width=True)
    
    # Pie Chart: User Type
    if 'user_type' in filtered_df.columns:
        with col_b:
            st.subheader("User Type Distribution")
            user_type_counts = filtered_df['user_type'].value_counts().reset_index()
            user_type_counts.columns = ['user_type', 'count']
            fig_user = px.pie(
                user_type_counts,
                values='count',
                names='user_type',
                title="Trips by User Type"
            )
            fig_user.update_traces(textinfo='percent+value')  # إظهار العدد والنسبة
            st.plotly_chart(fig_user, use_container_width=True)
    
    # Histogram: Age
    if 'member_age' in filtered_df.columns:
        st.subheader("Age Distribution")
        fig_age = px.histogram(filtered_df, x='member_age', nbins=30, title="Member Age Distribution", range_x=[0, 100])
        st.plotly_chart(fig_age, use_container_width=True)
    
    # Line Chart: Trip Duration Distribution by Gender
    if all(col in filtered_df.columns for col in ['duration_hrs', 'member_gender', 'user_type']):
        st.subheader("Trip Duration Distribution by Gender (<= 2 hrs)")
        df_filtered = filtered_df[filtered_df['duration_hrs'] <= 2]
        
        # إنشاء bins
        bins = np.linspace(0, 2, 51)  # 50 bins
        df_filtered['duration_bin'] = pd.cut(df_filtered['duration_hrs'], bins=bins, include_lowest=True)
        
        # تجميع حسب الجنس
        duration_gender = (
            df_filtered.groupby(['duration_bin', 'member_gender'])
            .size()
            .reset_index(name='count')
        )
        duration_gender['duration_mid'] = duration_gender['duration_bin'].apply(lambda x: x.mid)
        
        # إضافة تفاصيل user_type لكل bin و gender
        duration_user_type = (
            df_filtered.groupby(['duration_bin', 'member_gender', 'user_type'])
            .size()
            .reset_index(name='user_count')
        )
        duration_user_type = duration_user_type.pivot(index=['duration_bin', 'member_gender'], columns='user_type', values='user_count').fillna(0).reset_index()
        duration_gender = duration_gender.merge(duration_user_type, on=['duration_bin', 'member_gender'], how='left')
        
        # رسم الخطوط للجنس فقط
        fig_duration = px.line(
            duration_gender,
            x='duration_mid',
            y='count',
            color='member_gender',
            markers=True,
            title="Trip Duration Distribution by Gender (<= 2 hrs)",
            labels={'duration_mid': 'Trip Duration (hours)', 'count': 'Number of Trips', 'member_gender': 'Gender'},
            line_shape='linear',
            color_discrete_map={'Male': '#1f77b4', 'Female': '#ff7f0e', 'Other': '#2ca02c'},
            hover_data=duration_gender.columns[3:]  # إضافة تفاصيل user_type في الـ tooltip
        )
        
        fig_duration.update_layout(
            xaxis=dict(tick0=0, dtick=0.2),
            yaxis_title='Number of Trips',
            width=900,
            height=400
        )
        st.plotly_chart(fig_duration, use_container_width=True)
    
    # Stacked Bar Chart: Top 10 Start Stations by User Type
    if all(col in filtered_df.columns for col in ['start_station_name', 'user_type']):
        st.subheader("Top 10 Start Stations by Number of Users and User Type")
        station_user_counts = (
            filtered_df.groupby(['start_station_name', 'user_type'])
            .size()
            .reset_index(name='count')
        )
        # أخذ أكثر 10 محطات حسب إجمالي المستخدمين
        top_stations = (
            station_user_counts.groupby('start_station_name')['count']
            .sum()
            .nlargest(10)
            .reset_index()['start_station_name']
        )
        station_user_counts = station_user_counts[station_user_counts['start_station_name'].isin(top_stations)]
        
        fig_bar = px.bar(
            station_user_counts,
            x='start_station_name',
            y='count',
            color='user_type',
            text='count',
            title="Top 10 Start Stations by Number of Users and User Type",
            labels={'count': 'Number of Users', 'start_station_name': 'Start Station', 'user_type': 'User Type'},
            color_discrete_map={'Customer': '#ff7f0e', 'Subscriber': '#1f77b4'}
        )
        fig_bar.update_layout(
            xaxis_tickangle=-45,
            width=1000,
            height=600,
            yaxis_title="Number of Users",
            barmode='stack'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Map: Popular Start Stations
    if all(col in filtered_df.columns for col in ['start_station_name', 'start_station_latitude', 'start_station_longitude']):
        st.subheader("Popular Start Stations Map")
        station_counts = filtered_df['start_station_name'].value_counts().reset_index()
        station_counts.columns = ['start_station_name', 'count']
        station_coords = filtered_df[['start_station_name', 'start_station_latitude', 'start_station_longitude']].drop_duplicates()
        station_data = station_coords.merge(station_counts, on='start_station_name')
        station_data = station_data[station_data['start_station_latitude'].notna() & station_data['start_station_longitude'].notna()]
        if not station_data.empty:
            fig_map = px.scatter_mapbox(
                station_data,
                lat='start_station_latitude',
                lon='start_station_longitude',
                size='count',
                color='count',
                hover_name='start_station_name',
                hover_data={'count': True, 'start_station_latitude': False, 'start_station_longitude': False},
                mapbox_style="open-street-map",
                zoom=12,
                title="Start Stations (Size = Trip Count)",
                color_continuous_scale=px.colors.sequential.Plasma,
                size_max=30
            )
            fig_map.update_layout(
                mapbox=dict(
                    bearing=0,
                    pitch=0,
                    center=dict(
                        lat=station_data['start_station_latitude'].mean(),
                        lon=station_data['start_station_longitude'].mean()
                    )
                ),
                margin={"r":0, "t":50, "l":0, "b":0}
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("No valid coordinates for stations map.")

with tab2:
    # Raw Data Table
    st.subheader("Filtered Data Preview")
    preview_cols = ['start_time', 'duration_min', 'start_station_name', 'end_station_name', 'member_gender', 'user_type', 'member_age']
    st.dataframe(filtered_df[preview_cols].head(100), use_container_width=True)
    
    # Download Button
    @st.cache_data
    def convert_to_csv(df):
        return df.to_csv(index=False).encode('utf-8')
    
    csv = convert_to_csv(filtered_df[preview_cols])
    st.download_button(
        label="📥 Download Filtered Data (CSV)",
        data=csv,
        file_name=f'filtered_bike_trips_{datetime.now().strftime("%Y%m%d")}.csv',
        mime='text/csv'
    )

# Refresh Button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()