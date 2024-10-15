# -*- coding: utf-8 -*-
"""
Created on Thu Jul 21 20:28:37 2022

@author: User
"""

import streamlit as st
import pandas as pd
import velocity_calculation


def ui_velocity(data,velo_threshold,velo_process,utm_zone):
    #st.subheader("Filtering data based on velocity")
    
    data_process = pd.DataFrame()
    d_velo = pd.DataFrame()
    d_slow = pd.DataFrame()
    
    velo = velo_threshold*1000
    #data_process = velocity_calculation.preprocess_data(data)
    #data_process['velo_label'] = data_process.apply(lambda x: velocity_calculation.label_velocity(x, velo), axis = 1)
    
    if velo_process:
        
        if 'data_combine' not in st.session_state:
            st.session_state['data_combine'] = None
        else:
            data_process = velocity_calculation.preprocess_data(data,utm_zone)
            #data_process['velo_label'] = data_process.apply(lambda x: velocity_calculation.label_velocity(x, velo), axis = 1)
            st.session_state['data_combine'] = data_process
            data_process2 = st.session_state['data_combine']


        if 'data_velo' not in st.session_state:
            st.session_state['data_velo'] = None
        else:
            #Data with high velocity
            d_velo = data_process2[data_process2['velocity_mhr'] > velo]
            #data_process2[data_process2['velocity_mhr'] > velo]
            st.session_state['data_velo'] = d_velo


        if 'data_slow' not in st.session_state:
            st.session_state['data_slow'] = None
        else:
            #Data with low velocity
            d_slow = data_process2[(data_process2['velocity_mhr'] <= velo) | (data_process2['velocity_mhr'].isnull())]
            #data_process2[data_process2['velocity_mhr'] <= velo]
            st.session_state['data_slow'] = d_slow
            
        st.write("Done!!!")

    #if velo_process:

    return st.session_state['data_slow'], st.session_state['data_velo'], st.session_state['data_combine']