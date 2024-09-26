import streamlit as st
import pandas as pd
import requests
import re
import plotly.express as px
import numpy as np
from datetime import timedelta

st.set_page_config(layout="wide")

geojson_url = 'https://france-geojson.gregoiredavid.fr/repo/departements.geojson'
departements_geojson = requests.get(geojson_url).json()

def convert_to_numeric(coord):
    if isinstance(coord, str):
        coord = coord.replace(',', '.')
        match = re.match(r"([\d\.]+)°\s*([NSEW])", coord.strip())
        if match:
            value, direction = match.groups()
            value = float(value)
            if direction in ['W', 'S']:
                value = -value
            return value
    return None

@st.cache_data(ttl=timedelta(days=7))
def load_data():
    clients_tessan = pd.read_csv("http://metabase.prod.tessan.cloud/public/question/ca36c84f-034f-4479-a421-bdbb18f78a3e.csv")
    clients_medadom = pd.read_csv("./data/medadom.csv")

    new_columns_medadom = {'Nom du magasin': 'Name', 'Enseigne':'Enseigne', 'Région': 'Region', 'Adresse': 'Address',
                           'Latitude': 'Latitude', 'Longitude':'Longitude'}
    clients_medadom.rename(columns=new_columns_medadom, inplace=True)

    clients_tessan['Longitude'] = clients_tessan['Longitude'].apply(convert_to_numeric)
    clients_tessan['Latitude'] = clients_tessan['Latitude'].apply(convert_to_numeric)

    return clients_tessan, clients_medadom

clients_tessan, clients_medadom = load_data()

clients_tessan['Color'] = '#0F352D'  
clients_medadom['Color'] = np.where(clients_medadom['Enseigne'] == 'Autre', 'red', 'blue')  

combined_data = pd.concat([clients_tessan[['Name', 'Address', 'Latitude', 'Longitude', 'Color']],
                           clients_medadom[['Name', 'Address', 'Latitude', 'Longitude', 'Color']]])


# Plot the data on a map using Plotly
fig = px.scatter_mapbox(combined_data,
                        lat='Latitude',
                        lon='Longitude',
                        hover_name='Name',
                        hover_data={'Address': True},
                        color='Color',
                        color_discrete_map={'#0F352D': '#0F352D', 'blue': 'blue', 'red': 'red'},
                        zoom=5,  # Set the zoom level appropriately for France
                        height=800,
                        size_max=8,  # Adjust point size to not be too big or too small
                        size=[3] * len(combined_data))  # Set a uniform size

# Update layout with France GeoJSON
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_zoom=5,
    mapbox_center={"lat": 46.603354, "lon": 1.888334},  # Center of France
    mapbox_layers=[{
        "source": departements_geojson,
        "type": "line",
        "color": "grey",
        "line": {"width": 1.5},
    }],
    margin={"r":0,"t":0,"l":0,"b":0},
    legend=dict(title="Device Source", itemsizing='constant')
)

# Custom legend (if needed)
st.write("""
<div style='display: flex; justify-content: space-between;'>
    <span style='color: #0F352D;'>● Dispositifs TESSAN</span>
    <span style='color: blue;'>● Dispositifs MEDADOM</span>
    <span style='color: red;'>● Dispositifs MEDADOM "Autre"</span>
</div>
""", unsafe_allow_html=True)

# Show the map
st.plotly_chart(fig, use_container_width=True)

