# -*- coding: utf-8 -*-
"""
Created on Sun Jul 10 14:13:46 2022

@author: User
"""

import streamlit as st
import pandas as pd
import ui_velocity_calculation
import kdbscan
import process_movement
import datetime

st.set_page_config(page_title='Page 3: Detecting stop_locations by clustering',layout="wide")

st.subheader("Detecting stoplocations by clustering")
####------------ Use all data ------------------####

expander = st.expander("Click to see the default data with no query")

try:
    data_merge = st.session_state['data']
    data_merge['timestamp'] = pd.to_datetime(data_merge['timestamp'])
    expander.dataframe(data_merge)
    expander.write(data_merge.shape)
except:
    st.error("No data uploaded. Please upload some data.")



####--------------- Use query data ------------------####

expander = st.expander("Click to see the queried data")

try:
    data_query = st.session_state['data_show']
    data_query['timestamp'] = pd.to_datetime(data_query['timestamp'])
    expander.dataframe(data_query)
    expander.write(data_query.shape)
except:
    st.error("No data uploaded. Please upload some data.")



st.subheader("Choose data with or without query")
data_ = st.radio("Choose data to work with", options = ["Data without query", "Data with query"])

try:
    
    if data_ == "Data without query":
        data_select = data_merge #st.session_state['data']
        
    else:
        data_select = data_query #st.session_state['data_show']
        
    
    data_select['timestamp'] = pd.to_datetime(data_select['timestamp'])
    
    row_n = data_select.shape[0]
    col_n = data_select.shape[1]
    st.write("You select: '{}' , with {} rows and {} columns".format(data_,row_n,col_n))
    st.write("Minimum timestamp: {}".format(data_select['timestamp'].min()))
    st.write("Maximum timestamp: {}".format(data_select['timestamp'].max()))
    
except:
    st.error("No data uploaded. Please upload some data.")


##### Velocity filtering ####
st.subheader("Filtering data based on velocity")
geo_process_style = st.radio("Select geoprocessing calculation", 
                             ["Projected distance calculation: UTM is required to project the coordinates",
                              "Harversine distance calculation"])
col1, col2 = st.columns(2)

if geo_process_style == "Harversine distance calculation":
    velo_threshold = col1.number_input("Insert velocity threshold (km/hr)", min_value = 0)
    define_utm_zone = None
else:
    velo_threshold = col1.number_input("Insert velocity threshold (km/hr)", min_value = 0)
    define_utm_zone = col2.number_input("Insert UTM zone for geoprocessing",value=47)
    

st.write("Velocity threshold: {} km/hr".format(velo_threshold))
velo_process = st.button("Process to query data with velocity")

st.subheader("Filtering data based on velocity")


expander_velo = st.expander("Show selected data", expanded = True)
d_select = expander_velo.radio("Data labeld with velocity",
                    ["All","Higher than the threshold","Lower than the threshold"])



try:
    
    if d_select == "All":
        st.session_state['data_velo_select'] = ui_velocity_calculation.ui_velocity(data_select,velo_threshold,velo_process,utm_zone=int(define_utm_zone))[2] #data_combine
        
    elif d_select == "Higher than the threshold":
        st.session_state['data_velo_select'] = ui_velocity_calculation.ui_velocity(data_select,velo_threshold,velo_process,utm_zone=int(define_utm_zone))[1] #data_velo
        
    else:
        st.session_state['data_velo_select'] = ui_velocity_calculation.ui_velocity(data_select,velo_threshold,velo_process,utm_zone=int(define_utm_zone))[0] #data_slow
        

    #expander_velo.daraframe(data_select)
    expander_velo.write(st.session_state['data_velo_select'].shape)
    expander_velo.write(st.session_state['data_velo_select'])

    csv = process_movement.convert_df(st.session_state['data_velo_select'])
    st.download_button(
         label="Download data as CSV",
         data=csv,
         file_name='df_{}.csv'.format(d_select),
         mime='text/csv',
     )
    
    
except:
    st.error("No data")
    #st.write("No data")
    #st.write(st.session_state['data_velo_select'].shape)
    #st.dataframe(st.session_state['data_velo_select'])

    

##### Clustering selection #####
st.subheader("Clustering to retrive locations")
clus_algo = st.radio("Select Clustering Algorithms", ["K-means++", "Traditional DBSCAN", "K-DBSCAN"])

st.session_state['data_tra_db']['cluster_label'] = 0
st.session_state['data_kdbscan']['cluster_label'] = 0
# =============================================================================
# ###---------- Initializing clustering data ----------------###
# #------ K-means++
# st.session_state['data_kMeans'] = pd.DataFrame(columns=['cluster_label','longitude','latitude','timestamp'])
# 
# #------ traditional DBSCAN
# st.session_state['data_tra_db'] = pd.DataFrame(columns=['cluster_label','longitude','latitude','timestamp'])
# st.session_state['data_tra_db']['cluster_label'] = 0
# 
# #------ K-DBSCAN
# st.session_state['data_kdbscan'] = pd.DataFrame(columns=['cluster_label','longitude','latitude','timestamp'])
# st.session_state['data_kdbscan']['cluster_label'] = 0
# 
# =============================================================================


if clus_algo == "K-means++":
    expander_KM = st.expander("Select to perform K-means++ clustering", expanded = True)
    k_user = expander_KM.number_input("Define K", min_value = 0, step = 1)
    k_button = expander_KM.button("Start")
    k_sil = 0
    k_DB = 0
    
    #if 'data_kMeans' not in st.session_state:
        
    #else:
    if k_button:
        result_kmeans = kdbscan.do_kMeans(st.session_state['data_velo_select'], k_user, 'longitude', 'latitude')
        st.session_state['data_kMeans'] = result_kmeans
        
        k_sil = kdbscan.do_silhouette_score(st.session_state['data_kMeans'],'cluster_label')
        k_DB = kdbscan.do_davies_bouldin_score(st.session_state['data_kMeans'],'cluster_label')
    
    expander_KM.dataframe(st.session_state['data_kMeans']['cluster_label'].value_counts())
    expander_KM.write("Davies Bouldin Score: {}".format(k_DB))
    expander_KM.write("Silhouette Score: {}".format(k_sil))
    
    csv = process_movement.convert_df(st.session_state['data_kMeans'],idx=False)
    st.download_button(
         label="Download data as CSV",
         data=csv,
         file_name='cluster_{}_{}.csv'.format(clus_algo,datetime.datetime.now()),
         mime='text/csv',
     )
    

if clus_algo == "Traditional DBSCAN":
    expander_DB1 = st.expander("Select to perform Traditional DBSCAN clustering", expanded = True)
    ep_user = expander_DB1.number_input("Define distance in km", min_value = 0.0, step = 0.1)
    min_user = expander_DB1.number_input("Define minimum data points", min_value = 0, step = 1)
    db_button = expander_DB1.button("Start")
    db_sil = 0
    db_DB = 0
    
    if db_button:
        result_tra_dbscan = kdbscan.do_DBSCAN(st.session_state['data_velo_select'], ep_user, min_user,'longitude', 'latitude')
        st.session_state['data_tra_db'] = result_tra_dbscan
        
        db_sil = kdbscan.do_silhouette_score(st.session_state['data_tra_db'],'cluster_label')
        db_DB = kdbscan.do_davies_bouldin_score(st.session_state['data_tra_db'],'cluster_label')
    
    expander_DB1.dataframe(st.session_state['data_tra_db']['cluster_label'].value_counts())
    expander_DB1.write("Davies Bouldin Score: {}".format(db_DB))
    expander_DB1.write("Silhouette Score: {}".format(db_sil))
    
    csv = process_movement.convert_df(st.session_state['data_tra_db'],idx=False)
    st.download_button(
         label="Download data as CSV",
         data=csv,
         file_name='cluster_{},_{}.csv'.format(clus_algo,datetime.datetime.now()),
         mime='text/csv',
     )
    

if clus_algo == "K-DBSCAN":
    expander_KDB = st.expander("Select to perform K-DBSCAN clustering", expanded = True)
    k_user_kdb = expander_KDB.number_input("Define K", min_value = 0, step = 1)
    ep_user_kdb = expander_KDB.number_input("Define distance in km", min_value = 0.0, step = 0.1)
    min_user_kdb = expander_KDB.number_input("Define minimum data points", min_value = 0, step = 1)
    kdb_button = expander_KDB.button("Start")
    kdb_sil = 0
    kdb_DB = 0
    
    if kdb_button:
        result_kbscan = kdbscan.do_KDBSCAN(st.session_state['data_velo_select'], k_user_kdb, ep_user_kdb, min_user_kdb,'longitude', 'latitude')
        st.session_state['data_kdbscan'] = result_kbscan
        
        kdb_sil = kdbscan.do_silhouette_score(st.session_state['data_kdbscan'],'cluster_label')
        kdb_DB = kdbscan.do_davies_bouldin_score(st.session_state['data_kdbscan'],'cluster_label')
            
    expander_KDB.dataframe(st.session_state['data_kdbscan']['cluster_label'].value_counts())
    expander_KDB.write("Davies Bouldin Score: {}".format(kdb_DB))
    expander_KDB.write("Silhouette Score: {}".format(kdb_sil))
    
    csv = process_movement.convert_df(st.session_state['data_kdbscan'],idx=False)
    st.download_button(
         label="Download data as CSV",
         data=csv,
         file_name='cluster_{}_{}.csv'.format(clus_algo,datetime.datetime.now()),
         mime='text/csv',
     )
