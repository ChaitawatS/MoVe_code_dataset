# -*- coding: utf-8 -*-
"""
Created on Thu Jul  7 11:26:26 2022

@author: User
"""
import streamlit as st
import pandas as pd



st.set_page_config("Page 1: Uploading data", None, layout = "wide")

st.title("Malaria Mobility Analysis")

st.header("1.Data uploading: Mobility file & Demographic file")
col1, col2 = st.columns([2,2])

df1 = col1.file_uploader("Choose a mobility file", type='csv')

def load_move_data(data):
    df_move = pd.read_csv(data)
    return df_move


if df1 is not None:
    df1_move = load_move_data(df1)
    expander1 = col1.expander("See the raw movement file")
    expander1.dataframe(df1_move)
    key1 = col1.selectbox("Key column of the movement data to merge",
                               df1_move.columns)



df2 = col2.file_uploader("Choose a demographical file", type='csv')

def load_demo_data(data):
    df_demo = pd.read_csv(data)
    return df_demo


if df2 is not None:
    df2_demo = load_demo_data(df2)
    expander2 = col2.expander("See the demographical file")
    expander2.dataframe(df2_demo)
    key2 = col2.selectbox("Key column of the demographical data to merge",
                               df2_demo.columns)




def merge_move_demo(data1,data2,left_key,right_key):
    data_new = data1.merge(data2,left_on = ['{}'.format(left_key)], right_on = ['{}'.format(right_key)])
    return data_new

st.subheader("Merge movement and demographic data")
click_merge = st.button("Merge data")


###---------- Initializing filtered data ----------------###
if 'data' not in st.session_state:
    st.session_state['data'] = pd.DataFrame()
    
if 'data_demo' not in st.session_state:
    st.session_state['data_demo'] = pd.DataFrame()
    
if 'data_show' not in st.session_state:
    st.session_state['data_show'] = pd.DataFrame()




###---------- Initializing clustering data ----------------###
#------ Velocity data_velo_select
if 'data_velo_select' not in st.session_state:
    st.session_state['data_velo_select'] = pd.DataFrame()

#------ K-means++
if 'data_kMeans' not in st.session_state:
    st.session_state['data_kMeans'] = pd.DataFrame(columns=['cluster_label','longitude','latitude','timestamp'])

#------ traditional DBSCAN
if 'data_tra_db' not in st.session_state:
    st.session_state['data_tra_db'] = pd.DataFrame(columns=['cluster_label','longitude','latitude','timestamp'])
    #st.session_state['data_tra_db']['cluster_label'] = 0

#------ K-DBSCAN
if 'data_kdbscan' not in st.session_state:
    st.session_state['data_kdbscan'] = pd.DataFrame(columns=['cluster_label','longitude','latitude','timestamp'])
    #st.session_state['data_kdbscan']['cluster_label'] = 0

#------------- Initialize data for EM algorithm --------------
if 'data_show_for_matrix' not in st.session_state:
    st.session_state['data_show_for_matrix'] = pd.DataFrame()

if 'raw_data_for_EM' not in st.session_state:
    st.session_state['raw_data_for_EM'] = pd.DataFrame()

if 'timeSpent_EM_byID' not in st.session_state:
    st.session_state['timeSpent_EM_byID'] = pd.DataFrame()

if 'timeSpent_summarize_df' not in st.session_state:
    st.session_state['timeSpent_summarize_df'] = pd.DataFrame()

if 'timeSpent_summarize_fig' not in st.session_state:
    st.session_state['timeSpent_summarize_fig'] = None


if 'transition_matrix' not in st.session_state:
    st.session_state['transition_matrix'] = pd.DataFrame()

if 'transition_record' not in st.session_state:
    st.session_state['transition_record'] = pd.DataFrame()

if 'clus_locations' not in st.session_state:
    st.session_state['clus_locations'] = pd.DataFrame()

#------------- Initialize simulation data --------------
#---------------------------------------
if 'travel_history' not in st.session_state:
    st.session_state.travel_history = pd.DataFrame(columns=["agentID","group","date","Hour","Season","start","destination","health_stage","individual_risk"])
    
if 'pop_track_df' not in st.session_state:
    st.session_state.pop_track_df = pd.DataFrame(columns=["Date","Hour","Season","Cluster","Healthy","Exposed","Infected","Recovery","M_Suscept","M_Incubate","M_Infected","Mosquitoes_prevalence","Area_Risk"])

if 'cluster_locations' not in st.session_state:
    st.session_state.cluster_locations = pd.DataFrame()
    
if "setting_file" not in st.session_state:
    st.session_state["setting_file"] = pd.DataFrame()

if "setting_pop_file" not in st.session_state:
    st.session_state['setting_pop_file'] = pd.DataFrame()

if "ex_setting_pop_file" not in st.session_state:
    st.session_state['ex_setting_pop_file'] = pd.DataFrame()

if "setting_Subpop_file" not in st.session_state:
    st.session_state['setting_Subpop_file'] = pd.DataFrame()

#------------- Initialize individual risk table --------------
if 'individual_show' not in st.session_state:
    st.session_state['individual_show'] = pd.DataFrame()
    
if 'prop_health_stage' not in st.session_state:
    st.session_state['prop_health_stage'] = pd.DataFrame()
#individual_show = individual_risk_calculation(filtered_cluster)
#prop_health_stage = health_stage_proportion(filtered_cluster)


if click_merge:
    try:
        df_merge = merge_move_demo(df1_move,df2_demo, key1, key2)
        
        if 'data' not in st.session_state:
            st.session_state['data'] = None
        
        if df_merge is not None:
            expander3 = st.expander("See the merged data")
            expander3.dataframe(df_merge)
            st.session_state['data'] = df_merge
        
        if 'data_demo' not in st.session_state:
            st.session_state['data_demo'] = None
        
        if df2_demo is not None:
            st.session_state['data_demo'] = df2_demo
    except:
        st.error("Data does not exist!!! Please check movement data or demographic data")
