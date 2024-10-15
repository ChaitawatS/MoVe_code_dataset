# -*- coding: utf-8 -*-
"""
Created on Fri Nov 18 16:31:59 2022

@author: User
"""

import pandas as pd
import streamlit as st
import datetime

def filter_demo(col_names,data_demo,expander3):  
    
    ### Prepare columns for filtering ###
    select_lst = {}
    for i, col in enumerate(col_names):
        choice = data_demo['{}'.format(col)].unique().tolist()
        choice.insert(0, None)
        select = expander3.selectbox(label='{}'.format(col), options = choice, key=i)
        
        if select is None:
            select_lst = select_lst
        else:
            select_lst["{}".format(col)] = "{}".format(select)

    
    query_lst = []
    for k, v in select_lst.items():
        if k != "user_id":
            v = "'{}'".format(v)
        x = "{} == {}".format(k, v)
        
        query_lst.append(x)
    
    return query_lst


def filter_date_time(data_merge,expander4):
    ### Date Query ###
    date_start = expander4.date_input("Date start",datetime.date(2019, 1, 1))
    date_end = expander4.date_input("Date end",datetime.date(2021, 1, 1))

    try:
        date_query = (data_merge['date'] >= date_start) & (data_merge['date'] <= date_end)
    except:
        st.error("No data uploaded. Please upload some data.")



    ### TIme Query ###
    expander4.subheader("select Day/Night")
    time_choice = expander4.radio("Select time query", options = ["All", "Day", "Night"])
    if time_choice == "All":
        time_query = None
    elif time_choice == "Day":
        time_query = (data_merge['time'] >= datetime.time(6,0,0)) & (data_merge['time'] <= datetime.time(18,0,0))
    else:
        time_query = (data_merge['time'] >= datetime.time(18,1,0)) | (data_merge['time'] <= datetime.time(5,59,0))


    ### Date & Time query ###
    if time_query is None:
        try:
            date_time_query = data_merge.loc[date_query]
        except:
            st.error("No data uploaded. Please upload some data.")
    else:
        date_time_query = data_merge.loc[date_query & time_query]
    
    return date_time_query