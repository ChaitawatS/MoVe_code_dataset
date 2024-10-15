# -*- coding: utf-8 -*-
"""
Created on Wed Aug  3 15:31:43 2022

@author: User
"""

import pandas as pd
import numpy as np
import streamlit as st


#---------- (Start) Necessary functions for EM----------
@st.cache_data
def split_time(data,proportionDict,trackDict):
    time_sum = 0
    #total_all = {}
    
    if str(data['origin']) in list(trackDict.keys()):
        if str(data['cluster_label']) in list(trackDict.keys()):
            at_origin = trackDict[str(data['origin'])]
            at_des = trackDict[str(data['cluster_label'])]
            total = proportionDict[at_origin] + proportionDict[at_des]
    
            if data['track_move'] == at_origin and data['track_move_next'] == at_des:
                time_sum = data.loc['time_interval_hr']*(proportionDict[str(data['track_move'])]/total)
            if data['track_move'] == at_des and data['track_move_previous'] == at_origin:
                time_sum = data.loc['time_interval_hr']*(proportionDict[str(data['track_move'])]/total)
                
    return time_sum

@st.cache_data
def update_split(proportionDict,proportionTable):
    for k in proportionDict.keys():
        proportionDict[k] = proportionTable['%min'][k]


@st.cache_data
def iterative_split(data1,data2,data3,proportionDict,trackDict,iteration):
    list_proportion_dict = {}
    
    for j in proportionDict.keys():
        list_proportion_dict[j] = []
    
    
    for i in range(iteration):
        #print(i,proportionDict)
        
        for k in list_proportion_dict.keys():
            list_proportion_dict[k].append(proportionDict[k])
        
        data1['time_interval_hr_new'] = data1.apply(lambda a: split_time(a,proportionDict,trackDict),axis=1)
        
        df_concat = pd.concat([data1,data2],ignore_index=True)
        df_concat.drop(['track_move_next','track_move_previous'],axis=1,inplace=True)
        df_concat['timestamp'] = pd.to_datetime(df_concat['timestamp'])
        df_concat.sort_values(['user_id','timestamp'],inplace=True)
        df_concat.reset_index(inplace=True)
        
        df_time_spent = df_concat.groupby('track_move')['time_interval_hr_new'].sum().to_frame()
        df_time_spent['%min'] = (df_time_spent['time_interval_hr_new']/df_time_spent['time_interval_hr_new'].sum())*100
        
        update_split(proportionDict,df_time_spent)
        
    #df_list_proportion_dict = pd.DataFrame(list_proportion_dict)
    
    df_concat = pd.concat([df_concat,data3],ignore_index=True)
    df_concat['timestamp'] = pd.to_datetime(df_concat['timestamp'])
    df_concat.sort_values(['user_id','timestamp','label'],inplace=True)
    df_concat.drop(['label'],axis=1,inplace=True)
    df_concat.reset_index(inplace=True)
    df_concat['track_move'] = df_concat['track_move'].astype(str)
    
    #df_list_proportion_dict.to_csv('D:/data_kdbscan_test/conversion_table_iteration_{}.csv'.format(iteration))
    #df_concat.to_csv('D:/data_kdbscan_test/data_new_EM.csv',index = False)
    
    return df_concat

#---------- (END) Necessary functions for EM----------



@st.cache_data
def prepare_movement(data, cluster_col, demo_col, date_freq):
    data.sort_values(['user_id','date'], inplace = True)
    data['origin'] = data.groupby('user_id')['{}'.format(cluster_col)].shift()
    data['origin'] = data['origin'].fillna(999)
    data['origin'] = data['origin'].astype(np.int64)
    
    data['time_interval_min'] = (data.groupby(['user_id'])['timestamp'].diff()/np.timedelta64(1,'m')).to_frame()
    data['time_interval_hr'] = data['time_interval_min']/60
    data.drop('time_interval_min',axis=1,inplace=True)
    
    df_move = data.loc[data['origin'] != 999].loc[data['cluster_label'] != data['origin']]
    df_stay = data.loc[data['origin'] != 999].loc[data['cluster_label'] == data['origin']]
    
    
    #working on the transition time
    df_move_repeat = pd.DataFrame(np.repeat(df_move.values,3,axis=0), columns=df_move.columns)
    df_move_repeat['label'] = df_move_repeat.groupby('id').cumcount()+1
    
    
    #-----reassign cluster------
    df_move_repeat['cluster_label_new'] = np.where(df_move_repeat['label'] == 1,df_move_repeat['origin'],df_move_repeat['cluster_label'])
    df_move_repeat['origin_new'] = np.where(df_move_repeat['label'] == 3,df_move_repeat['cluster_label'],df_move_repeat['origin'])
    df_move_repeat['track_move'] = df_move_repeat['origin_new'].astype(str) + '->' + df_move_repeat['cluster_label_new'].astype(str)
    df_move_repeat['track_move'] = df_move_repeat['track_move'].astype(str)
    
    df_move_repeat2 = df_move_repeat.loc[df_move_repeat['label'] != 2]
    df_move_repeat2_transition = df_move_repeat.loc[df_move_repeat['label'] == 2]
    
    
    df_move_repeat2.drop(['cluster_label_new','origin_new'],axis=1,inplace=True)
    df_move_repeat2_transition.drop(['cluster_label_new','origin_new'],axis=1,inplace=True)
    #df_move_repeat2_transition['time_interval_hr_new'] = df_move_repeat2_transition['time_interval_hr']
    df_move_repeat2_transition['time_interval_hr_new'] = 1
    

    df_move_repeat2['track_move_previous'] = df_move_repeat2.groupby(['id'])['track_move'].shift()
    df_move_repeat2['track_move_next'] = df_move_repeat2.groupby(['id'])['track_move'].shift(-1)
    
    df_stay['track_move'] = df_stay['origin'].astype(str) + '->' + df_stay['cluster_label'].astype(str)
    df_stay['track_move'] = df_stay['track_move'].astype(str)
    df_stay['time_interval_hr_new'] = df_stay['time_interval_hr']
    
    
    #--------Create an initial proportion of time spent---------
    lst_track = df_move_repeat2['track_move'].unique().tolist()
    lst_origin = df_move_repeat2['origin'].unique().tolist()
    
    proportion_dict = {}
    track_dict = {}
    #des_dict = {}
    
    # Initially assign proportion
    for i in lst_track:
        proportion_dict["{}".format(i)] = 50
    
    #Matching location and track move
    for i,j in zip(lst_origin,lst_track):
        split_track = j.split("-")
        if i == int(split_track[0]):
            track_dict["{}".format(i)] = j
    
    
    #------------- EM algorithm ----------------
    data_afterEM = iterative_split(df_move_repeat2,df_stay,df_move_repeat2_transition,proportion_dict,track_dict,10)
    
    #-------- Time spent ---------
    data_afterEM_byid = data_afterEM.loc[data_afterEM['track_move'].str[0].astype('int64') == data_afterEM['track_move'].str[3].astype('int64')]
    data_afterEM_byid = data_afterEM_byid.groupby(['user_id','track_move'])['time_interval_hr_new'].sum().reset_index()
    data_afterEM_byid['origin'] = data_afterEM_byid['track_move'].str[0].astype('int64')
    data_afterEM_byid['destination'] = data_afterEM_byid['track_move'].str[3].astype('int64')
    data_afterEM_byid.drop(['track_move'],axis=1,inplace=True)
    
    
    data_new = data_afterEM.groupby(['user_id',pd.Grouper(key = 'timestamp', freq = '{}'.format(date_freq)),'track_move'])['time_interval_hr_new'].sum() #pd.Grouper(key = 'timestamp', freq = '{}'.format(date_freq))
    data_new = pd.DataFrame(data_new).rename(columns={"time_interval_hr_new":"count_move"}).reset_index(level=['user_id','track_move','timestamp']) #,'timestamp' 
    
    #data_new = data_new.query("origin != cluster_label")
    #data_new['origin'] = data_new['origin'].astype(int)
    return [data_new, data_afterEM_byid]

@st.cache_data
def table_of_all_movement(data,cluster_col):
    movement_each_id = {}
    #id_move = data.index.unique().tolist()
    id_move = data.user_id.unique().tolist()

    for i in id_move:
        #normalization = data.loc[i,:].groupby(['origin'])['count_move'].sum()
        a = data.loc[data['user_id'] == i]
        x = a.groupby(['track_move'])['count_move'].sum()
        x = x.reset_index()
        x['origin'] = x['track_move'].str[0].astype(str)
        x['cluster_label'] = x['track_move'].str[3].astype(str)
        
        movement_each_id[i] = x.reset_index()
    
    return movement_each_id

@st.cache_data
def do_movement_record(cluster_location,selected_id):
    #df_occ = df_demo.loc[demo_lst] #df_demo.loc[query] ,demo_lst
    #df_demo_2 = df_demo.reset_index()
    #lst = df_demo_2['user_id'].tolist()
    
    ### sum movement based on origin-destination
    new_lst = []
    for i in selected_id.keys():
        x = selected_id[i]
        new_lst.append(x)
    
    new_lst = pd.concat(new_lst)
    
    #------Probabilistic form conversion-----
    normalize_new_lst = new_lst.groupby(['origin'])['count_move'].sum()
    new_lst_2 = (new_lst.groupby(['origin','cluster_label'])['count_move'].sum()/normalize_new_lst)*100
    new_lst_2 = new_lst_2.reset_index(level=['origin','cluster_label']).rename(columns={'cluster_label':'destination'})
    
    #------Transition record-----
    new_lst_3 = new_lst.groupby(['origin','cluster_label'])['count_move'].sum()
    new_lst_3 = new_lst_3.reset_index(level=['origin','cluster_label']).rename(columns={'cluster_label':'destination'})
    new_lst_3 = new_lst_3.loc[new_lst_3['origin'] != new_lst_3['destination']]
    
    
    cluster_location['cluster_label'] = cluster_location['cluster_label'].astype(str)
    l = new_lst_2.merge(cluster_location,left_on='origin',right_on=['cluster_label'])
    l2 = l.merge(cluster_location,left_on='destination',right_on=['cluster_label'],suffixes=('_origin', '_destination'))
    l2 = l2.drop(['id_origin','id_destination'],axis=1)
    move_data = l2.drop(l2.filter(regex='cluster_label').columns, axis=1).rename(columns={'destination':'dest','count_move':'count',
                                                                         'longitude_origin':'start_lon','latitude_origin':'start_lat',
                                                                         'longitude_destination':'destination_lon','latitude_destination':'destination_lat'})
    #move_data = move_data.drop(['id_origin','id_destination'],axis=1)
    move_data = move_data.sort_values(by=['origin','dest'])
    
    l3 = new_lst_3.merge(cluster_location,left_on='origin',right_on=['cluster_label'])
    l3 = l3.merge(cluster_location,left_on='destination',right_on=['cluster_label'],suffixes=('_origin', '_destination'))
    l3 = l3.drop(['id_origin','id_destination'],axis=1)
    l3 = l3.drop(l3.filter(regex='cluster_label').columns, axis=1).rename(columns={'destination':'dest','count_move':'count',
                                                                         'longitude_origin':'start_lon','latitude_origin':'start_lat',
                                                                         'longitude_destination':'destination_lon','latitude_destination':'destination_lat'})
    l3 = l3.sort_values(by=['origin','dest'])

    return [move_data, l3]




@st.cache_data
def convert_df(df,idx=False):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=idx).encode('utf-8')

@st.cache_data
def convert_df_json(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_json(orient = 'records').encode('utf-8')

@st.cache_data
def load_move_data(data):
    df_move = pd.read_csv(data)
    return df_move