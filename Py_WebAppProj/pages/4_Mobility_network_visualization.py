# -*- coding: utf-8 -*-
"""
Created on Mon Jul 25 14:18:01 2022

@author: User
"""

import streamlit as st
import pandas as pd
import process_movement
import plotly.express as px
import numpy as np
import os
import datetime
import streamlit.components.v1 as components
#import requests

st.set_page_config(page_title='Page 4: Mobility network visualization',layout="wide")



st.header("Mobility network visualization")

col1, col2, col3 = st.columns(3)
### Result from K-means++ ###
with col1:
    if st.session_state['data_kMeans'].shape[0] == 0:
        st.error("No data from K-means ++ clustering")
        data_kmeans = pd.DataFrame(columns=['cluster_label','longitude','latitude','timestamp'])
    else:
        st.success("Data from K-means ++ exists")
        st.session_state['data_kMeans']['timestamp'] = pd.to_datetime(st.session_state['data_kMeans']['timestamp'])
        st.session_state['data_kMeans']['date'] = st.session_state['data_kMeans']['timestamp'].dt.date
        #data_kmeans = st.session_state['data_kMeans']


### Result from traditional DBSCAN ###
with col2:
    if st.session_state['data_tra_db'].shape[0] == 0:
        st.error("No data from traditional DBSCAN clustering")
        data_dbscan = pd.DataFrame(columns=['cluster_label','longitude','latitude','timestamp'])
    else:
        st.success("Data from traditinal DBSCAN exists")
        st.session_state['data_tra_db']['timestamp'] = pd.to_datetime(st.session_state['data_tra_db']['timestamp'])
        st.session_state['data_tra_db']['date'] = st.session_state['data_tra_db']['timestamp'].dt.date
        #data_dbscan = st.session_state['data_tra_db']
    

### Result from K-DBSCAN ###
with col3:
    if st.session_state['data_kdbscan'].shape[0] == 0:
        st.error("No data from K-DBSCAN clustering")
        data_kdbscan = pd.DataFrame(columns=['cluster_label','longitude','latitude','timestamp'])
    else:
        st.success("Data from K-DBSCAN exists")
        st.session_state['data_kdbscan']['timestamp'] = pd.to_datetime(st.session_state['data_kdbscan']['timestamp'])
        st.session_state['data_kdbscan']['date'] = st.session_state['data_kdbscan']['timestamp'].dt.date
        #data_kdbscan = st.session_state['data_kdbscan']



data_choice = st.radio("Select data to work with", ["K-means++", "Traditional DBSCAN", "K-DBSCAN"])
#st.session_state['data_show_for_matrix'] = pd.DataFrame(columns=['cluster_label','longitude','latitude','timestamp'])
if data_choice == "K-means++":
    st.session_state['data_show_for_matrix'] = st.session_state['data_kMeans']
    clus_col = 'cluster_label'
    st.write(st.session_state['data_show_for_matrix'].shape)
elif data_choice == "Traditional DBSCAN":
    st.session_state['data_show_for_matrix'] = st.session_state['data_tra_db']
    clus_col = 'cluster_label'
    st.write(st.session_state['data_show_for_matrix'].shape)
else:
    st.session_state['data_show_for_matrix'] = st.session_state['data_kdbscan']
    clus_col = 'cluster_label'
    st.write(st.session_state['data_show_for_matrix'].shape)
    
st.dataframe(st.session_state['data_show_for_matrix'])
base_map = st.radio("Select based map", ["open-street-map","stamen-terrain","carto-positron"])

if st.session_state['data_show_for_matrix'].shape[0] != 0:
    fig = px.scatter_mapbox(st.session_state['data_show_for_matrix'], lat = 'latitude', lon = 'longitude',
                            color = "cluster_label",hover_name = "cluster_label", hover_data = st.session_state['col_names'],color_continuous_scale='Rainbow')
    fig.update_layout(mapbox_style = base_map,margin={"r":10,"t":10,"l":10,"b":10})
    
    st.plotly_chart(fig, use_container_width = True)



#---------------- Extract column names --------------------#
data_demo = st.session_state['data_demo']
col_names = st.session_state['col_names']


st.session_state['col_names'] = data_demo.columns.tolist()
col_names = st.session_state['col_names']
#expander3 = st.expander("Select column names to query")

col_demo, col_date = st.columns(2)

### Prepare columns for filtering ###
select_lst = {}
query_lst = []

with col_demo:
    st.subheader("Select demographics")
    with st.form(key="demo_data_for_matrix"):
        
        for i, col in enumerate(col_names):
            choice = data_demo['{}'.format(col)].unique().tolist()
            choice.insert(0, None)
            select_demo = st.selectbox(label='{}'.format(col), options = choice, key=i)
                
            if select_demo is None:
                select_lst = select_lst
            else:
                select_lst["{}".format(col)] = "{}".format(select_demo)
        
        
        for k, v in select_lst.items():
            if k != "user_id":
                v = "'{}'".format(v)
            x = "{} == {}".format(k, v)
                
            query_lst.append(x)
            
        if len(query_lst) == 0:
            query = None
            st.write(query)
        else:
            query = " & ".join(query_lst)
            
        
        submit = st.form_submit_button("Submit demographics")
    
    
    expander1 = st.expander("Show selected demographics:",expanded=True)
    #st.subheader("Show selected demographics:")
    if len(select_lst) == 0:
        expander1.write("No filtered by demographics")
    else:
        for j,k in select_lst.items():
            expander1.write("Column: {}, value: {}".format(j,k))
    



#---------------------- Date Query --------------------------------#
with col_date:
    st.subheader("Select time resolution")
    
    with st.form(key="select_time_resolution"):
        date_start = st.date_input("Date start",datetime.date(2019, 1, 1))
        date_end = st.date_input("Date end",datetime.date(2021, 1, 1))
        
        try:
            date_query = (st.session_state['data_show_for_matrix']['date'] >= date_start) & (st.session_state['data_show_for_matrix']['date'] <= date_end)
            
            #data_select = data_select.loc[date_query]
        except:
            st.error("No data uploaded. Please upload some data.")
        
        
        
        ### Work day & weekend query###
        bussinessDay_choice = st.radio("Select bussiness day/weekend", options = ["All", "Weekend", "Work day"])
        ### Work day & weekend query###
        try:
            if bussinessDay_choice == "All":
                dayofweek = None
            elif bussinessDay_choice == "Weekend":
                dayofweek = st.session_state['data_show_for_matrix']['dayofweek'] > 4
            else:
                dayofweek = st.session_state['data_show_for_matrix']['dayofweek'] <= 4
        except:
            pass
        
        
            
        
        select_time_resolution = st.selectbox("Time resolution", options = ['Hourly','Daily','Weekly','Monthly'])
        try:
            if select_time_resolution == "Daily":
                time_res = 'D'
            elif select_time_resolution == "Weekly":
                time_res = 'W'
            elif select_time_resolution == "Hourly":
                time_res = 'H'
            else:
                time_res = 'M'
        except:
            pass
    
        submit = st.form_submit_button("Submit time resolution")
    
    st.write("Date start: {}, Date end: {}".format(date_start,date_end))
    st.write("Working day: {}".format(bussinessDay_choice))
    st.write("Select time resolution: {}".format(select_time_resolution))


#query_combination_data = pd.DataFrame()

if len(query_lst) == 0:
    try:
        if dayofweek is None:
            st.session_state['data_show_for_matrix'] = st.session_state['data_show_for_matrix'].loc[date_query]
        else:
            st.session_state['data_show_for_matrix'] = st.session_state['data_show_for_matrix'].loc[date_query & dayofweek]
        #st.session_state['data_show_for_matrix'] = data_select
    except:
        st.error("No data uploaded. Please upload some data.")
    #st.write(date_time_query)
else:
    if dayofweek is None:
        st.session_state['data_show_for_matrix'] = st.session_state['data_show_for_matrix'].loc[date_query].query(query)
    else:
        st.session_state['data_show_for_matrix'] = st.session_state['data_show_for_matrix'].loc[date_query & dayofweek].query(query)
    #st.write(query_combination)


#st.dataframe(st.session_state['data_show_for_matrix'])


#------------------- Extract transition matrices and locations --------------------
press_clus, press_matrix = st.columns(2)

with press_clus:
    extract_cluster = st.button("Extract cluster",use_container_width=True)

with press_matrix:
    extract_button = st.button("Extract movement",use_container_width=True)

#with press_time:




#------------- Layout of extracting transition matrix ----------------#
show_cluster, show_matrix = st.columns(2)
#show_time = st.columns(1)


if extract_cluster:
    ### Cluster locations ###
    if data_choice == "K-means++":
        st.session_state['clus_locations'] = st.session_state['data_kMeans'].groupby('cluster_label')[['longitude','latitude']].mean().reset_index()
        
    elif data_choice == "Traditional DBSCAN":
        st.session_state['clus_locations'] = st.session_state['data_tra_db'].groupby('cluster_label')[['longitude','latitude']].mean().reset_index()
        
    else:
        st.session_state['clus_locations'] = st.session_state['data_kdbscan'].groupby('cluster_label')[['longitude','latitude']].mean().reset_index()
        

    st.session_state['clus_locations']['id'] = st.session_state['clus_locations']['cluster_label']
    cluster_locations = st.session_state['clus_locations']
    
    cluster_locations = process_movement.convert_df_json(st.session_state['clus_locations'])
    
    path_cluster = "D:\\Py_WebAppProj\\frontend\\cluster_loc" #\\cluster_loc
    file_name_cluster_loc = "cluster_loc_test.json"
    
    if cluster_locations is not None:
        with open(os.path.join(path_cluster,file_name_cluster_loc),"wb") as js:
            js.write(cluster_locations)


if extract_button:
    st.session_state['raw_data_for_EM'] = process_movement.prepare_movement(st.session_state['data_show_for_matrix'],clus_col,query,time_res)[0] #EM
    st.session_state['raw_data_for_EM']['date'] = st.session_state['raw_data_for_EM']['timestamp'].dt.date
    
    record_process = process_movement.table_of_all_movement(st.session_state['raw_data_for_EM'],clus_col)
    st.session_state['transition_matrix'] = process_movement.do_movement_record(st.session_state['clus_locations'],record_process)[0]
    
    st.session_state['transition_record'] = process_movement.do_movement_record(st.session_state['clus_locations'],record_process)[1]
    
    
    path_move = "D:\\Py_WebAppProj\\frontend\\travel_sum" #\\travel_sum
    file_name_move = "travel_summary_test.json"
    
    move_record_json = process_movement.convert_df_json(st.session_state['transition_record'])
    csv = process_movement.convert_df(st.session_state['raw_data_for_EM'],idx=False)
    
              
    st.download_button(
         label="Download raw data as CSV",
         data=csv,
         file_name='large_df_{}.csv'.format(data_choice),
         mime='text/csv',
     )
    
    if move_record_json is not None:
        with open(os.path.join(path_move,file_name_move),"wb") as js:
            js.write(move_record_json)
    #expand_demo = st.expander("Show movemnet by the select demographics")


extract_timeSpent = st.button("Show time spent",use_container_width=True)
if extract_timeSpent:
    st.session_state['timeSpent_EM_byID'] = process_movement.prepare_movement(st.session_state['data_show_for_matrix'],clus_col,query,time_res)[1]
    st.session_state['timeSpent_EM_byID']['days'] = np.ceil(st.session_state['timeSpent_EM_byID']['time_interval_hr_new']/24).apply(np.int64)
    
    st.session_state['timeSpent_summarize_df'] = st.session_state['timeSpent_EM_byID'].drop(['destination'],axis=1).rename(columns={"origin":"location"})
    st.session_state['timeSpent_summarize_df'] = st.session_state['timeSpent_summarize_df'].groupby(['location'],as_index=False)['days'].sum()
    st.session_state['timeSpent_summarize_df']['days_sum'] = st.session_state['timeSpent_summarize_df']['days'].sum()
    st.session_state['timeSpent_summarize_df']['avg_day'] = (st.session_state['timeSpent_summarize_df']['days']/st.session_state['timeSpent_summarize_df']['days_sum'])*100
    
    
    #-- Bar chart --#
    st.session_state['timeSpent_summarize_fig'] = px.bar(st.session_state['timeSpent_summarize_df'], x='location', y='avg_day', title ='Average time spent in days',
                                                         color_discrete_sequence=['#FFA07A'],text='avg_day',text_auto='.2f')
    
    #st.session_state['timeSpent_EM_byID'] = st.session_state['timeSpent_EM_byID'].groupby(['user_id','origin','cluster_label'])['time_interval_hr_new'].sum()
    


with show_cluster:
    with st.expander("Cluster locations",expanded=True):
        if st.session_state['clus_locations'].shape[1] != 0:
            st.dataframe(st.session_state['clus_locations'].drop(['id'],axis=1),use_container_width=True)
        else:
            st.dataframe(pd.DataFrame())
        
        csv = process_movement.convert_df(st.session_state['clus_locations'],idx=False)
        st.download_button(
             label="Download locations as CSV",
             data=csv,
             file_name='cluster_location_{}.csv'.format(datetime.datetime.now()),
             mime='text/csv',
         )


with show_matrix:
    
    with st.expander('Transition record',expanded=True):
        
        if st.session_state['transition_record'].shape[1] != 0:
            st.dataframe(st.session_state['transition_record'].drop(['start_lon','start_lat','destination_lon','destination_lat'],axis=1),use_container_width=True) #.drop(['start_lon','start_lat','destination_lon','destination_lat'],axis=1)
        else:
            st.dataframe(pd.DataFrame())
        
        csv_record = process_movement.convert_df(st.session_state['transition_record'],idx=False)
        csv_transition = process_movement.convert_df(st.session_state['transition_matrix'],idx=False)
        
        col1, col2 = st.columns(2)
        col1.download_button(
             label="Download transition record as CSV",
             data=csv_record,
             file_name='transition_record_{}.csv'.format(datetime.datetime.now()),
             mime='text/csv',
             use_container_width=True
         )
        col2.download_button(
             label="Download transition matrix as CSV",
             data=csv_transition,
             file_name='transition_matrix_{}.csv'.format(datetime.datetime.now()),
             mime='text/csv',
             use_container_width=True
         )


#with show_time:
with st.expander('Time spent', expanded = True):
    #if st.session_state['timeSpent_EM_byID'].shape[1] != 0:
    #st.dataframe(st.session_state['timeSpent_EM_byID'],use_container_width=True) #
    if st.session_state['timeSpent_summarize_fig'] is not None:
        st.plotly_chart(st.session_state['timeSpent_summarize_fig'],use_container_width=True)
        
    csv = process_movement.convert_df(st.session_state['timeSpent_summarize_df'],idx=False)
    st.download_button(
        label="Download time spent data as CSV",
        data=csv,
        file_name='timeSpent_{}.csv'.format(datetime.datetime.now()),
        mime='text/csv',
    )


#col_showData = st.columns()
#with col_showData:
st.header("Movement visualization")
show_viz = st.button("Show movement")
if show_viz:
    components.iframe("http://127.0.0.1:8080", height = 700)