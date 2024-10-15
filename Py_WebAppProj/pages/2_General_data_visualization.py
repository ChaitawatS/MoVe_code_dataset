# -*- coding: utf-8 -*-
"""
Created on Sat Jul  9 09:38:13 2022

@author: User
"""

import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

st.set_page_config(page_title='Page 2: General data visualization',layout="wide")

st.header("General data visualization")

########### All data visualiation (Default) ###############
#st.session_state['data'] = st.session_state['data']

try:
    expander = st.expander("Click to see the merged data")
    
    st.session_state['data']['timestamp'] = pd.to_datetime(st.session_state['data']['timestamp'])
    st.session_state['data']['date'] = st.session_state['data']['timestamp'].dt.date
    st.session_state['data']['time'] = st.session_state['data']['timestamp'].dt.time
    st.session_state['data']['dayofweek'] = st.session_state['data']['timestamp'].dt.dayofweek
    
    expander.dataframe(st.session_state['data'])
    expander.write(st.session_state['data'].shape)
except:
    st.error("No data uploaded. Please upload some data.")


col_demo, col_date = st.columns(2)


######## Process data with date and time ###########
with col_date:
    st.subheader("Select date time to query")
    with st.form(key="date_time"):
        ### Date Query ###
        date_start = st.date_input("Date start",datetime.date(2019, 1, 1))
        date_end = st.date_input("Date end",datetime.date(2021, 1, 1))
        
        try:
            date_query = (st.session_state['data']['date'] >= date_start) & (st.session_state['data']['date'] <= date_end)
            
            #date_time_query = st.session_state['data'].loc[date_query]
        except:
            st.error("No data uploaded. Please upload some data.")
        
        
        ### Time Query ###
        time_choice = st.radio("Select Day/Night", options = ["All", "Day", "Night"])
        try:
            if time_choice == "All":
                time_query = None
            elif time_choice == "Day":
                time_query = (st.session_state['data']['time'] >= datetime.time(6,0,0)) & (st.session_state['data']['time'] <= datetime.time(18,0,0))
            else:
                time_query = (st.session_state['data']['time'] >= datetime.time(18,1,0)) | (st.session_state['data']['time'] <= datetime.time(5,59,0))
        except:
            pass
        
        
        ### Work day & weekend query###
        bussinessDay_choice = st.radio("Select bussiness day/weekend", options = ["All", "Weekend", "Work day"])
        try:
            if bussinessDay_choice == "All":
                working_day = None
            elif bussinessDay_choice == "Weekend":
                working_day = (st.session_state['data']['dayofweek'] > 4)
            else:
                working_day = (st.session_state['data']['dayofweek'] <= 4)
        except:
            pass
        
        
        
            
        submit = st.form_submit_button("Submit date/time")

    
  
    expander2 = st.expander("Show selected date/time:",expanded=True)
    
    expander2.write("Start date: {}, end date: {}".format(date_start,date_end))
    expander2.write("Select work day/weekend: {}".format(bussinessDay_choice))
    expander2.write("Selected time of a day: {}".format(time_choice))




########### Process coluumn names from demographic data ###########
col_names = None
data_demo = pd.DataFrame()
query_lst = []
select_lst = {}


data_demo = st.session_state['data_demo']

##-------------------------------------------------##
if 'col_names' not in st.session_state:
    st.session_state['col_names'] = None
else:
    ### Extract column names ###
    st.session_state['col_names'] = data_demo.columns.tolist()
    col_names = st.session_state['col_names']
    #expander3 = st.expander("Select column names to query")
    #st.subheader("Select column names to query")
    
    ### Prepare columns for filtering ###
    with col_demo:
        st.subheader("Select demographics")
        with st.form(key="demo_data"):
            #select_lst = {}
            for i, col in enumerate(col_names):
                choice = data_demo['{}'.format(col)].unique().tolist()
                choice.insert(0, None)
                select = st.selectbox(label='{}'.format(col), options = choice, key=i)
                
                if select is None:
                    select_lst = select_lst
                else:
                    select_lst["{}".format(col)] = "{}".format(select)
        
            
            #query_lst = []
            for k, v in select_lst.items():
                if k != "user_id":
                    v = "'{}'".format(v)
                x = "{} == {}".format(k, v)
                query_lst.append(x)
            
            
            if len(query_lst) == 0:
                query = None
                #st.write(query)
                
            else:
                query = " & ".join(query_lst)
                #st.write(select_lst)
                #st.write(query)
                
            submit_demo = st.form_submit_button("Submit demographics")
    
    
        #---Show selected demographics
        expander1 = st.expander("Show selected demographics:",expanded=True)
        #st.subheader("Show selected demographics:")
        if len(select_lst) == 0:
            expander1.write("No filtered by demographics")
            expander1.write(query)
        else:
            for j,k in select_lst.items():
                expander1.write("Column: {}, value: {}".format(j,k))

#st.write(query)


######## Combine demographical & date and time query & show ###########
st.subheader("Show filtered data:")


if len(query_lst) != 0:
    try:
        if time_query is not None and working_day is not None:
            st.session_state['data_show'] = st.session_state['data'].loc[date_query & time_query & working_day].query(query)
                
        if working_day is None and time_query is not None:
            st.session_state['data_show'] = st.session_state['data'].loc[date_query & time_query].query(query)
    
        if time_query is None and working_day is not None:
            st.session_state['data_show'] = st.session_state['data'].loc[date_query & working_day].query(query)
                
        if time_query is None and working_day is None:
            st.session_state['data_show'] = st.session_state['data'].loc[date_query].query(query)
        
    except:
        st.error("No data uploaded. Please upload some data.")
    
else:
    ### Date & Time query only ###
    try:
        if time_query is not None and working_day is not None:
            st.session_state['data_show'] = st.session_state['data'].loc[date_query & time_query & working_day]
                
        if working_day is None and time_query is not None:
            st.session_state['data_show'] = st.session_state['data'].loc[date_query & time_query]
    
        if time_query is None and working_day is not None:
            st.session_state['data_show'] = st.session_state['data'].loc[date_query & working_day]
                
        if time_query is None and working_day is None:
            st.session_state['data_show'] = st.session_state['data'].loc[date_query]
        
    except:
        st.error("No data uploaded. Please upload some data.")
    


#expander2 = st.expander("")
if st.session_state['data_show'].shape[0] != 0:
    st.write(st.session_state['data_show'].shape)
    st.dataframe(st.session_state['data_show'].drop(['date','time'],axis=1)) #.drop(['date','time'],axis=1)
    






### Show data on a map by click ###
map_choice = st.radio("Select data to show on map", ["All data", "Data with query"])
base_map = st.radio("Select based map", ["open-street-map","stamen-terrain","carto-positron"])
show_button = st.button("Show data on map")

data_on_map = pd.DataFrame()
if map_choice == "All data":
    data_on_map = st.session_state['data']
else:
    data_on_map = st.session_state['data_show']

if show_button:
    
    if data_on_map.shape[0] != 0:
        fig = px.scatter_mapbox(data_on_map, lat = 'latitude', lon = 'longitude',
                                color = "user_id", hover_name = "user_id", hover_data = col_names,color_continuous_scale='Rainbow')
        fig.update_layout(mapbox_style = base_map, margin={"r":10,"t":10,"l":10,"b":10})
    
        st.plotly_chart(fig, use_container_width = True)
    else:
        st.error("No data uploaded")
else:
    st.error("No data uploaded")