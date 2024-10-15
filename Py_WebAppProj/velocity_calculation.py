import streamlit as st
import pandas as pd
import numpy as np
import math
import pyproj


### Distance (m) calculation ####
@st.cache_data
def distance(data,lon_org,lat_org,lon,lat,utm_zone):
    #conversion to utm
    
    projection = pyproj.Proj(proj='utm', zone=utm_zone, ellps='WGS84')
    x_o, y_o = projection(data['{}'.format(lon_org)], data['{}'.format(lat_org)]) #from Origin
    x_d, y_d = projection(data['{}'.format(lon)], data['{}'.format(lat)])
    
    #Euclidean distance (m)
    distance_lat = y_d - y_o
    distance_lon = x_d - x_o
    
    #Euclidean distance (m)
    d_m = np.sqrt((distance_lat**2) + (distance_lon**2))
    
    return d_m


### Harversine distance (m) calculation ####
@st.cache_data
def harversine_distance(data,lon_org,lat_org,lon,lat):
    radius = 6371000 #earth radius in meter
    
    distance_lat = math.radians(data[lat] - data[lat_org])
    distance_lon = math.radians(data[lon] - data[lon_org])
    
    a = (math.sin(distance_lat/2)**2) + math.cos(math.radians(data[lat_org]))*math.cos(math.radians(data[lat]))*(math.sin(distance_lon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d_m = radius * c #Distance in meters
    
    return d_m


@st.cache_data
def preprocess_data(data,utm_zone):
    
    #id_lst = data['user_id'].unique().tolist()
    #ind_data = []
    data.sort_values(['user_id','timestamp'],inplace = True)
    
    data['latitude_origin'] = data.groupby('user_id')['latitude'].shift()
    data['longitude_origin'] = data.groupby('user_id')['longitude'].shift()
    data['timestamp_origin'] = data.groupby('user_id')['timestamp'].shift()
    
    #data['timestamp_origin'] = pd.to_datetime(data['timestamp_origin'])
    
    
    if utm_zone is not None:
        data_origin = data[data['latitude_origin'].isna()]
        
        data.drop(data[(data['latitude_origin'].isna()) & (data['timestamp_origin'].isna())].index, inplace=True)
       
        data['distance_meter'] = data.apply(lambda x: distance(x,'longitude_origin','latitude_origin','longitude','latitude',utm_zone),axis=1)

        
        data['delta_hr'] = data['timestamp'] - data['timestamp_origin']
        data['delta_hr'] = data['delta_hr'].apply(lambda x: x  / np.timedelta64(1,'h')) #.astype('int64')
        
        
        data['velocity_mhr'] = data['distance_meter'] / data['delta_hr']
        d = pd.concat([data,data_origin])
        d = d.sort_values(['user_id','timestamp'])
        d = d.drop(['latitude_origin','longitude_origin','timestamp_origin','distance_meter','delta_hr'],axis=1)
            
    else:
        data_origin = data[data['latitude_origin'].isna()]
        
        data.drop(data[(data['latitude_origin'].isna()) & (data['timestamp_origin'].isna())].index, inplace=True)
       
        data['distance_meter'] = data.apply(lambda x: harversine_distance(x,'longitude_origin','latitude_origin','longitude','latitude'),axis=1)

        
        data['delta_hr'] = data['timestamp'] - data['timestamp_origin']
        data['delta_hr'] = data['delta_hr'].apply(lambda x: x  / np.timedelta64(1,'h')) #.astype('int64')
        
        
        data['velocity_mhr'] = data['distance_meter'] / data['delta_hr']
        d = pd.concat([data,data_origin])
        d = d.sort_values(['user_id','timestamp'])
        d = d.drop(['latitude_origin','longitude_origin','timestamp_origin','distance_meter','delta_hr'],axis=1)
    
    #data_new = pd.concat(ind_data)

    return d




#@st.cache
def label_velocity(data, velo):
  ### velo km/h
  ### velo_km m/h because the projection is meter
  #velo_km = velo * 1000
  #dis_km = dis * 1000

  if data['velocity_mhr'] > velo:
    return 0
  else:
    if data['delta_hr'].isnull():
      return 0
    else:
      return 1





