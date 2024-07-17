import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import folium_static
from folium.plugins import HeatMap

# Load data
def load_data():
    crime_data = pd.read_csv('dataset/NYPD_Complaint_Data_Historic.csv')
    population_data = pd.read_csv('dataset/Population_by_Borough_NYC.csv')
    return crime_data, population_data

crime_data, population_data = load_data()

# Convert to datetime
crime_data['RPT_DT'] = pd.to_datetime(crime_data['RPT_DT'])

# Extract year from date
crime_data['Year'] = crime_data['RPT_DT'].dt.year

# Streamlit layout
st.set_page_config(layout='wide')  # Menyusun layout menjadi wide

# Sidebar untuk filter
st.sidebar.title('New York City Crimes and Population Dashboard')
st.sidebar.header('Filter Options')

# Widget filter berdasarkan jenis kejahatan
selected_crime_type = st.sidebar.selectbox('Select Crime Type', ['All'] + list(crime_data['OFNS_DESC'].unique()))

# Widget filter berdasarkan rentang tahun
years = sorted(crime_data['Year'].unique())
selected_year_range = st.sidebar.slider('Select Year Range', min_value=int(years[0]), max_value=int(years[-1]), value=(int(years[0]), int(years[-1])))

# Widget filter berdasarkan borough
selected_borough = st.sidebar.selectbox('Select Borough', ['All'] + list(crime_data['BORO_NM'].unique()))

# Set sample size to 200
sample_size = 200

# Filter data berdasarkan pilihan di sidebar
if selected_crime_type != 'All':
    crime_type_filter = crime_data['OFNS_DESC'] == selected_crime_type
else:
    crime_type_filter = pd.Series([True] * len(crime_data))

year_filter = (crime_data['Year'] >= selected_year_range[0]) & (crime_data['Year'] <= selected_year_range[1])

if selected_borough != 'All':
    borough_filter = crime_data['BORO_NM'] == selected_borough
else:
    borough_filter = pd.Series([True] * len(crime_data))

# Gabungkan semua kondisi filter
filtered_data = crime_data[crime_type_filter & year_filter & borough_filter]

# Streamlit layout
st.title('New York City Crimes and Population Dashboard')

# # Menampilkan data populasi berdasarkan borough di atas sejajar dengan Crime Type Distribution
# st.subheader('Population by Borough in NYC')
# st.write(population_data)

# Layout untuk visualisasi populasi dan jenis kejahatan
col_pop, col_crime = st.columns([1, 1])

with col_pop:
    st.subheader('Population Distribution by Borough')
    fig_population = px.bar(population_data, x='Borough', y='2020', title='Population Distribution by Borough in 2020', color='Borough', color_discrete_sequence=px.colors.sequential.Viridis)
    st.plotly_chart(fig_population)

if not filtered_data.empty:
    with col_crime:
        st.subheader('Crime Type Distribution')
        crime_type_counts = filtered_data['OFNS_DESC'].value_counts().nlargest(10).reset_index()
        crime_type_counts.columns = ['Crime Type', 'Number of Crimes']
        fig_crime_type = px.bar(crime_type_counts, x='Number of Crimes', y='Crime Type', title='Top 10 Crime Types', orientation='h', color='Crime Type', color_discrete_sequence=px.colors.sequential.Viridis)
        st.plotly_chart(fig_crime_type)

    # Layout untuk visualisasi peta dan grafik
    col1, col2 = st.columns([1, 1])  # Membagi layout menjadi dua kolom

    # Visualisasi peta lokasi kejahatan
    with col1:
        st.subheader('Crime Locations on Map')

        # Pilih subset data dan hapus NaN values berdasarkan filter jenis kejahatan
        subset_data = filtered_data.dropna(subset=['Latitude', 'Longitude'])

        # Tentukan ukuran sampel yang tidak melebihi ukuran dataset yang tersedia
        sample_size_actual = min(sample_size, len(subset_data))
        if sample_size_actual > 0:
            subset_data_sample = subset_data.sample(sample_size_actual)

            # Inisialisasi peta menggunakan folium
            m = folium.Map(location=[subset_data_sample['Latitude'].mean(), subset_data_sample['Longitude'].mean()], zoom_start=12)

            # Menambahkan markas pada peta berdasarkan filter jenis kejahatan
            for index, row in subset_data_sample.iterrows():
                folium.CircleMarker(
                    location=[row['Latitude'], row['Longitude']],
                    radius=5,
                    tooltip=row['OFNS_DESC'],
                    color='blue',
                    fill=True,
                    fill_color='blue'
                ).add_to(m)

            # Menampilkan peta di Streamlit
            st.markdown("The map below shows the locations of crimes based on the selected filters.")
            folium_static(m)

    # Visualisasi kejahatan berdasarkan borough dari waktu ke waktu menggunakan Altair
    with col2:
        st.subheader('Crime Trends by Borough')
        chart_type = st.selectbox('Select Chart Type', ['Bar Chart', 'Line Chart'], key='chart_type')

        crime_borough_yearly = filtered_data.groupby(['BORO_NM', filtered_data['RPT_DT'].dt.year])['CMPLNT_NUM'].count().reset_index()
        fig_borough_yearly = px.bar(crime_borough_yearly, x='RPT_DT', y='CMPLNT_NUM', color='BORO_NM', title='Crime Trends by Borough') if chart_type == 'Bar Chart' else px.line(crime_borough_yearly, x='RPT_DT', y='CMPLNT_NUM', color='BORO_NM', title='Crime Trends by Borough', markers=True)
        st.plotly_chart(fig_borough_yearly)

    # Visualisasi kejahatan berdasarkan borough
    col3, col4 = st.columns([1, 1])

    # Tambahkan pie chart di bawah Crime Trends by Borough
    with col3:
        st.subheader('Crime Percentage by Borough')
        crime_borough_counts = filtered_data['BORO_NM'].value_counts().reset_index()
        crime_borough_counts.columns = ['Borough', 'Number of Crimes']

        fig_pie = px.pie(crime_borough_counts, values='Number of Crimes', names='Borough', title='Crime Percentage by Borough', color_discrete_sequence=px.colors.sequential.Viridis)
        st.plotly_chart(fig_pie)

    # Visualisasi Heatmap kejahatan
    with col4:
        st.subheader('Crime Heatmap')
        if sample_size_actual > 0:
            m_heatmap = folium.Map(location=[subset_data_sample['Latitude'].mean(), subset_data_sample['Longitude'].mean()], zoom_start=12)
            HeatMap(data=subset_data_sample[['Latitude', 'Longitude']].values, radius=10).add_to(m_heatmap)
            folium_static(m_heatmap)
        else:
            st.write("No data available for the selected filters.")

else:
    st.write("Please select at least one filter option from the sidebar to display data.")
