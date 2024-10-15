# -*- coding: utf-8 -*-
"""
Created on Sun Nov 20 12:02:03 2022

@author: User
"""

import streamlit as st
import model_envi
import sim_agent
import pandas as pd
import numpy as np
import datetime
import process_movement
import dashboard_main

st.set_page_config(page_title='Page 5: Markov simulation',layout="wide")

#----hide column of dataframe-----
hide_dataframe_row_index = """
            <style>
            .row_heading.level0 {display:none}
            .blank {display:none}
            </style>
            """


#------------- Global variables --------------

#------------- Define simulation date --------------
#---------------------------------------
st.header("Define simulation date and seasons")
sim_date = st.number_input("Enter simulation days: ",step = 1,min_value=1)

sim_hr = int(sim_date)*24

season = st.number_input("Enter number of season:",min_value=1,step=1)

date_range = [*range(sim_date)]


#--tracking season--
season_lst = []
lst_test = []
ss_item = []


#----- record days of each season ------
if season > 1:
    show_range = st.columns(season)
    for j in range(0,season):
        if j < season - 1:
            season_x_len = int(show_range[j].number_input("Enter the lenght (days) of season {}: ".format(j+1),min_value=1,step=1)) #int(input())
            ss_item.append(season_x_len)
            
        else:
            season_x_len = sim_date - sum(ss_item)
            show_range[season-1].number_input("Enter the lenght (days) of season {}: ".format(j+1),min_value=season_x_len,max_value=season_x_len,value=season_x_len)
            ss_item.append(season_x_len)
    
    
    start_ind = 0
    end_ind = 0
    for m in range(len(ss_item)):
        #----- indicate days in each season ------
        end_ind = start_ind + ss_item[m] #define the end index
        season_item = date_range[start_ind:end_ind]
        start_ind = end_ind #update the next start index
        season_lst.append(season_item)
        
        #show_range[m].write("")
#---------------------------------------


#---------------------------------------
st.header("Define clusters and upload locations")
col1, col2 = st.columns(2)



#------------- Upload clusters location --------------
st.subheader("Upload locations of the clusters")

cluster_location = col1.file_uploader("Choose a file", "csv", accept_multiple_files=False)

if cluster_location is not None:
    st.session_state['cluster_locations'] = process_movement.load_move_data(cluster_location)
    
    #fig = px.scatter_mapbox(st.session_state['cluster_locations'], lat = 'latitude', lon = 'longitude',color = "cluster_label", hover_name = "cluster_label")
    #fig.update_layout(mapbox_style = "open-street-map", margin={"r":10,"t":10,"l":10,"b":10})
    
else:
    st.session_state['cluster_locations'] = pd.DataFrame(data={'id':[0]})
    #st.session_state['cluster_locations']['id'] = 0

num_cluster = col2.number_input("Enter number of cluster:",min_value=st.session_state['cluster_locations'].shape[0],value=st.session_state['cluster_locations'].shape[0],max_value=st.session_state['cluster_locations'].shape[0])

loc_expander = st.expander("Show locations of cluster")
col_table, col_map = st.columns(2)


loc_expander.dataframe(st.session_state['cluster_locations'],use_container_width=True)

#--------------------------------------------------


# create array to keep all agent
all_agent = []

# create array to teack when all agent move
cluster_detail = []

#------------- Cluster part --------------
#---------------------------------------
# create array in each cluster to keep each agent status
# generating a simulated world



with st.form(key="Cluster_setting"):
    
    #------------Upload cluster setting------------

    cluster_setting = st.file_uploader("Choose a file for setting cluster", "csv", accept_multiple_files=False)

    if cluster_setting is not None:
        st.session_state['setting_file'] = process_movement.load_move_data(cluster_setting)
        st.session_state['setting_file'].set_index(['Cluster','VAR'],inplace=True)
        
        col_lst = st.session_state["setting_file"].columns.tolist()
        col_len = len(col_lst)
        
    else:
        st.session_state['setting_file'] = None
        
    
    if num_cluster is not None:
        cluster_field = [[] for i in range(0,num_cluster)]
        cluster_n = st.columns(num_cluster)
        
        
        for i in range(0,len(cluster_n)):
            
            #----- Initial value of parameters -----#
            mos_s_value = 100
            mos_l_value = 0
            mos_l_hidden_value = 0
            mos_i_value = 0
            
            biting_rate_value = 1.0
            extentic_incubation_period_value = 7
            prob_spread_to_human_value = 1.0
            prob_infect_to_mos_value = 1.0
            mos_birth_rate_value = 0.50
            mos_mortal_rate_value = 0.50
            constant_sus_value = 0
            constant_incub_value = 0
            constant_inf_value = 0
            
            
            #------ Global lists of parameters --------#
            lst_biting_rate = [] #unknown
            lst_prob_spread_to_human = [] #unknown
            lst_prob_infect_to_mos = []
            lst_extentic_incubation_period = []
            lst_mos_birth_rate = []
            lst_mos_mortal_rate = []
            lst_constant_sus = [] #unknown
            lst_constant_incub = [] #unknown
            lst_constant_inf = [] #unknown
            known_params = None
            patient_external_value = 0
            
            
            #------ mapping with the uploaded file -------#
            
            if season == 1:
                
                if st.session_state['setting_file'] is not None:
                    
                    
                    mos_s = st.session_state['setting_file'].loc[(i,'susceptible mos'),'ss1']
                    mos_l = st.session_state['setting_file'].loc[(i,'incubated mos'),'ss1']
                    mos_l_hidden = mos_l_hidden_value
                    mos_i = st.session_state['setting_file'].loc[(i,'infected mos'),'ss1']
                    
                    prob_spread_to_human = st.session_state['setting_file'].loc[(i,'prob_spread_to_human'),'ss1']
                    biting_rate = st.session_state['setting_file'].loc[(i,'biting_rate'),'ss1']
                    
                    if st.session_state['setting_file'].loc[(i,'unknown_area'),'ss1'] == 0:
                        known_params = True
                        
                        prob_infect_to_mos = st.session_state['setting_file'].loc[(i,'prob_infect_to_mos'),'ss1']
                        extentic_incubation_period = st.session_state['setting_file'].loc[(i,'extentic_incubation_period'),'ss1'] #random.randrange(6,10)
                        mos_birth_rate = st.session_state['setting_file'].loc[(i,'mos_birth_rate'),'ss1']
                        mos_mortal_rate = st.session_state['setting_file'].loc[(i,'mos_mortal_rate'),'ss1']
                        
                    if st.session_state['setting_file'].loc[(i,'unknown_area'),'ss1'] == 1:
                        known_params = False
                        
                        constant_sus_value = st.session_state['setting_file'].loc[(i,'constant_sus'),'ss1']
                        constant_inf_value = st.session_state['setting_file'].loc[(i,'constant_inf'),'ss1']
                        
                
                else:
                    mos_s = mos_s_value
                    mos_l = mos_l_value
                    mos_l_hidden = mos_l_hidden_value
                    mos_i = mos_i_value
                    
                    biting_rate = biting_rate_value
                    prob_spread_to_human = prob_spread_to_human_value
                    prob_infect_to_mos = prob_infect_to_mos_value
                    extentic_incubation_period = extentic_incubation_period_value
                    mos_birth_rate = mos_birth_rate_value
                    mos_mortal_rate = mos_mortal_rate_value
                    constant_sus = constant_sus_value
                    constant_inf = constant_inf_value
                
                
                lst_biting_rate.append(biting_rate) #.append()
                lst_prob_spread_to_human.append(prob_spread_to_human)
                lst_prob_infect_to_mos.append(prob_infect_to_mos)
                lst_extentic_incubation_period.append(extentic_incubation_period)
                lst_mos_birth_rate.append(mos_birth_rate)
                lst_mos_mortal_rate.append(mos_mortal_rate)
                lst_constant_sus.append(constant_sus_value)
                lst_constant_inf.append(constant_inf_value)
                
            else:
                
                lst_biting_rate_value = []
                lst_extentic_incubation_period_value = []
                lst_prob_spread_to_human_value = []
                lst_prob_infect_to_mos_value = []
                lst_mos_birth_rate_value = []
                lst_mos_mortal_rate_value = []
                lst_constant_sus_value = []
                lst_constant_incub_value = []
                lst_constant_inf_value = []
                
                if st.session_state['setting_file'] is not None:
                    
                    mos_s = st.session_state['setting_file'].loc[(i,'susceptible mos'),'ss1']
                    mos_l = st.session_state['setting_file'].loc[(i,'incubated mos'),'ss1']
                    mos_l_hidden = mos_l_hidden_value
                    mos_i = st.session_state['setting_file'].loc[(i,'infected mos'),'ss1']
                    
                    
                    for s in range(col_len):
                        col_name = col_lst[s]
                        
                        biting_rate_value = st.session_state["setting_file"].loc[(i,'biting_rate'),col_name]
                        prob_spread_to_human_value = st.session_state["setting_file"].loc[(i,'prob_spread_to_human'),col_name]                        
                        
                        if st.session_state['setting_file'].loc[(i,'unknown_area'),'ss1'] == 0:
                            known_params = True
                        
                            extentic_incubation_period_value = st.session_state['setting_file'].loc[(i,'extentic_incubation_period'),col_name]
                            prob_infect_to_mos_value = st.session_state["setting_file"].loc[(i,'prob_infect_to_mos'),col_name]
                            mos_birth_rate_value = st.session_state["setting_file"].loc[(i,'mos_birth_rate'),col_name]
                            mos_mortal_rate_value = st.session_state["setting_file"].loc[(i,'mos_mortal_rate'),col_name]
                        
                        if st.session_state['setting_file'].loc[(i,'unknown_area'),'ss1'] == 1:
                            known_params = False
                            constant_sus_value = st.session_state["setting_file"].loc[(i,'constant_sus'),col_name]
                            constant_inf_value = st.session_state["setting_file"].loc[(i,'constant_inf'),col_name]
                        
                        lst_biting_rate_value.append(biting_rate_value)
                        lst_extentic_incubation_period_value.append(extentic_incubation_period_value)
                        lst_prob_spread_to_human_value.append(prob_spread_to_human_value)
                        lst_prob_infect_to_mos_value.append(prob_infect_to_mos_value)
                        lst_mos_birth_rate_value.append(mos_birth_rate_value)
                        lst_mos_mortal_rate_value.append(mos_mortal_rate_value)
                        lst_constant_sus_value.append(constant_sus_value)
                        lst_constant_inf_value.append(constant_inf_value)
                        
                        
                    for m in range(season):
                        
                        #--------------------------------------------------#
                        prob_spread_to_human = lst_prob_spread_to_human_value[m]
                        prob_infect_to_mos = lst_prob_infect_to_mos_value[m]
                        biting_rate = lst_biting_rate_value[m]
                        extentic_incubation_period = lst_extentic_incubation_period_value[m] #random.randrange(6,10)
                        mos_birth_rate = lst_mos_birth_rate_value[m]
                        mos_mortal_rate = lst_mos_mortal_rate_value[m]
                        constant_sus = lst_constant_sus_value[m]
                        constant_inf = lst_constant_inf_value[m]
                        
        
                        lst_biting_rate.append(biting_rate)
                        lst_prob_spread_to_human.append(prob_spread_to_human)
                        lst_prob_infect_to_mos.append(prob_infect_to_mos)
                        lst_extentic_incubation_period.append(extentic_incubation_period)
                        lst_mos_birth_rate.append(mos_birth_rate)
                        lst_mos_mortal_rate.append(mos_mortal_rate)
                        lst_constant_sus.append(constant_sus)
                        lst_constant_inf.append(constant_inf)
                
                else:
                    mos_s = mos_s_value
                    mos_l = mos_l_value
                    mos_l_hidden = mos_l_hidden_value
                    mos_i = mos_i_value
                    
                    for m in range(season):
                    
                        biting_rate = biting_rate_value
                        prob_spread_to_human = prob_spread_to_human_value
                        prob_infect_to_mos = prob_infect_to_mos_value
                        extentic_incubation_period = extentic_incubation_period_value
                        mos_birth_rate = mos_birth_rate_value
                        mos_mortal_rate = mos_mortal_rate_value
                        constant_sus = constant_sus_value
                        constant_inf = constant_inf_value
                    
                        lst_biting_rate.append(biting_rate)
                        lst_prob_spread_to_human.append(prob_spread_to_human)
                        lst_prob_infect_to_mos.append(prob_infect_to_mos)
                        lst_extentic_incubation_period.append(extentic_incubation_period_value)
                        lst_mos_birth_rate.append(mos_birth_rate)
                        lst_mos_mortal_rate.append(mos_mortal_rate)
                        lst_constant_sus.append(constant_sus)
                        lst_constant_inf.append(constant_inf)
            
                
                
            cluster_detail.append(sim_agent.Cluster(i, prob_of_spread_to_human = lst_prob_spread_to_human,
                                                     prob_of_infect_to_mos = lst_prob_infect_to_mos, mos_birth_rate = lst_mos_birth_rate, mos_mortal_rate = lst_mos_mortal_rate,
                                                     extentic_incubation_period = lst_extentic_incubation_period, mos_carry_capacity = 50000, mos_s = mos_s, mos_l = mos_l, mos_latent = mos_l_hidden, mos_i = mos_i,biting_rate = lst_biting_rate,constant_sus = lst_constant_sus, constant_inf = lst_constant_inf,known_params=known_params,patient_external=patient_external_value))
                
    submit = st.form_submit_button("Submit cluster setting")
            



#----------------------------------------------

    
res_clus = st.expander("Showing clusters info")
if len(cluster_detail) != 0:
    for i in range(len(cluster_detail)):
        res_clus.write(cluster_detail[i].show_cluster_detail())
else:
    res_clus.write("No data uploaded")



#------------- Agent part --------------
#---------------------------------------
st.header("Define Populations")
pop_choice = st.radio("Select method to define populations",["User interface", "Files uploading"], horizontal=True)


#define function for adding agent to each cluster
def agentCreator(cluster,size,health_stage,group,mobility_obj,timer=0):
    for j in range(0,size):
        all_agent.append(sim_agent.Agent(health_stage=health_stage,group=group,cluster=cluster,mobility_obj=mobility_obj,timer=timer))

        cluster_field[cluster].append(all_agent[-1])

        cluster_detail[cluster].population += 1
        if health_stage == "Infected":
            cluster_detail[cluster].patient += 1


def create_mobility_obj(season,popN,name):
    lst = []
    
    if season == 1:
        st.subheader("{} mobility file of season {}".format(name,1))
        mobility_obj = st.file_uploader("Choose a file", "csv", accept_multiple_files=False)
        if mobility_obj is not None:
            mobility_obj = model_envi.read_mobility_file(mobility_obj)
            lst.append(mobility_obj)
        
    else:
        for k in range(0,season):
            st.subheader("{} mobility file of season {}".format(name,k+1))
            mobility_obj = st.file_uploader("Choose a file {}:".format(str(popN)+str(k)), "csv", accept_multiple_files=False,key=(str(popN)+str(k)))
            if mobility_obj is not None:
                mobility_obj = model_envi.read_mobility_file(mobility_obj)
                lst.append(mobility_obj)
                
    return lst

#------ Select method to set up populations --------#
if pop_choice == "User interface":
    n_group = st.number_input("Insert n of groups of populations for the system: ",min_value=1,max_value=10,step=1)  
    pop_n = st.columns(n_group)
    
    for i in range(0,int(n_group)):
        
        with pop_n[i]:
            with st.form(key="Population {}".format(i),clear_on_submit=False):
                st.subheader("Population {}".format(i+1))
                group_name = st.text_input("Define a name population {}: ".format(i+1))
                start_at = st.number_input("Define start location at cluster: ",min_value=st.session_state['cluster_locations']['id'].min(),max_value=st.session_state['cluster_locations']['id'].max(),step=1)
                agents_h_stage = st.selectbox("Define initial health stage: ",("Healthy","Exposed","Infected","Recovery"))
                initial_n = st.number_input("Define initial size: ",min_value=1)
                
                #------ Mobility file uploading -------#
                lst_mobility_obj = create_mobility_obj(season,i,group_name)
                
                
                #st.write("------Create a group of agents-----")
                st.write("------Done defining group agents -------")
                
                if len(lst_mobility_obj) > 0:
                    agentCreator(cluster=int(start_at), size=int(initial_n), health_stage=str(agents_h_stage), group=str(group_name.upper()), mobility_obj=lst_mobility_obj)
                
                submit = st.form_submit_button("Submit population")
            
    
    res_agent = st.expander("Showing clusters info")
    res_agent.write(len(all_agent))
    #for i in range(len(all_agent)):
    #    res_agent.write("participant {}, group {}, health status {}".format(all_agent[i].id,all_agent[i].group,all_agent[i].health_stage))
          
else:
    
    population_setting = st.file_uploader("Choose a file for setting population", "csv", accept_multiple_files=False)
    
    if population_setting is not None:
        st.session_state['setting_pop_file'] = process_movement.load_move_data(population_setting)
        
        #--- get population number ---#
        population_n = len(st.session_state['setting_pop_file']['Name'].unique().tolist())
        n_group = st.number_input("N of groups of populations for the system: ", min_value = population_n,value = population_n, max_value = population_n)  
        pop_n = st.columns(n_group)
        columns_lst = st.session_state['setting_pop_file'].columns.tolist()[3:]
        #st.write(st.session_state['setting_pop_file'])
        
        #--- get population setting ---#
        for i in range(population_n):
            group_name = st.session_state['setting_pop_file']['Name'].unique().tolist()[i]
            st.session_state['setting_Subpop_file'] = st.session_state['setting_pop_file'].loc[st.session_state['setting_pop_file']['Name'] == group_name]
            #st.write(group_name)
            
            with pop_n[i]:
                with st.form(key="Population {}".format(i),clear_on_submit=False):
                    #------ Mobility file uploading -------#
                    lst_mobility_obj = create_mobility_obj(season,i,group_name)
                    #st.write(st.session_state['setting_pop_file'])
                    st.session_state['setting_Subpop_file'].reset_index(inplace = True)
                    st.session_state['setting_Subpop_file'].drop('index',axis=1,inplace = True)
                    for n in range(st.session_state['setting_Subpop_file'].shape[0]):
                        filter_file = st.session_state['setting_Subpop_file'].loc[(st.session_state['setting_Subpop_file'].index == n)]
                        start_at = int(filter_file['start_loc'])
                        #st.write((n))
                        
                        for m in range(len(columns_lst)):
                            agents_h_stage = columns_lst[m]
                            initial_n = int(filter_file[agents_h_stage])
                            #st.write((initial_n))
                    
                            if len(lst_mobility_obj) > 0:
                                agentCreator(cluster = start_at, size = initial_n, health_stage=str(agents_h_stage), group=str(group_name.upper()), mobility_obj=lst_mobility_obj)
                    
                    submit_pop = st.form_submit_button("Submit population data")
                
    
        
    res_agent = st.expander("Showing clusters info")
    res_agent.write(len(all_agent))
        
#------------------- External populations --------------#
st.header("Define External Populations")
ex_pop_choice = st.radio("Does the simulation include external populations?",["Yes", "No"], horizontal=True,index=1)

if ex_pop_choice == "Yes":
    
    
    with st.form(key="External_population_setting"):
        
        ex_population_setting = st.file_uploader("Choose a file for setting external population", "csv", accept_multiple_files=False)
        
        if ex_population_setting is not None:
            #pass
            st.session_state['ex_setting_pop_file'] = process_movement.load_move_data(ex_population_setting)
            
            
            external_pop_activity = st.session_state['ex_setting_pop_file'] #st.session_state['ex_setting_pop_file']
            
            if len(cluster_detail) != 0:
                for i in range(len(cluster_detail)):
                    st.write(cluster_detail[i].known_params)
            
            if external_pop_activity is not None:
                st.write(external_pop_activity)
        
        submit_ex_pop = st.form_submit_button("Submit external population data")
        
    
else:
    st.write("External populations are not considered here.")

            

#-------------------------------------------------------#
#------------------- Main simulation -------------------#
start_simulation = st.button("Start simulation")


if start_simulation:
    
        
    st.session_state['pop_track_df'] = model_envi.main_simulation(cluster_detail, cluster_field, sim_hr, all_agent, season, season_lst, external_pop_activity)
    
    #-------- Combine locations of cluster ----------------------
    #st.session_state['pop_track_df'] = st.session_state['pop_track_df'].merge(st.session_state['cluster_locations'], left_on='Cluster',right_on='id',  how='left') #st.session_state['cluster_locations']
    #st.session_state['pop_track_df'] = st.session_state['pop_track_df'].drop(['id', 'cluster_label'], axis=1)
    
    #st.session_state['travel_history'].to_csv("D:/Py_WebAppProj/result/travel_history.csv",encoding='utf-8')
    st.session_state['pop_track_df'].to_csv("D:/Py_WebAppProj/result/cluster_detail.csv",encoding='utf-8')
    st.write("-----Done-------")

else:    
    #st.session_state['travel_history'] = pd.DataFrame(columns=["agentID","group","date","Hour","Season","start","destination","health_stage","individual_risk"])
    #st.session_state['pop_track_df'] = pd.DataFrame(columns=["date","Hour","Season","Cluster","Healthy","Exposed","Infected","Recovery","M_Suscept","M_Incubate","M_incubate_hidden","M_Infected","Mosquitoes_prevalence","Area_Risk"])
    
    st.write("-----Waiting for the simulation data-------")





try:
    #-----------------Download files-----------------------------
    col3, col4 = st.columns(2)
    timestamp = datetime.datetime.now()
    

    if st.session_state['pop_track_df'].shape[0] != 0:
    #if st.session_state['pop_track_df'] is not None:
        cluster_date = process_movement.convert_df(st.session_state['pop_track_df'])
        name_cluster_date = col4.text_input("Name of clusters file","cluster_detail")
        col4.download_button(label="Download human mobility as CSV",
                             data = cluster_date, #cluster_date  st.session_state['pop_track_df']
                             file_name='{}_{}.csv'.format(name_cluster_date,timestamp),
                             mime='text/csv')
except:
    st.write("No data")


        
#----------------- Simulation visualization -----------------------------

with st.form(key = 'visualization_input'):
    #--------------Visualization date slider ------------------
    try:
        if sim_date > 1:
            st.subheader("Choose date to show:")
            simulation_slider = st.slider("Simulation Date:",value=[1,sim_date],min_value=1,max_value=sim_date)
    except:
        st.write("No data")
    
    #--------------Visualization cluster selecter ------------------
    try:
        
        if st.session_state['cluster_locations'].shape[0] != 0:
            st.subheader("Choose cluster to show:")
            select_cluster = st.selectbox("Select cluster:", dashboard_main.get_list_of_cluster(st.session_state['cluster_locations']['cluster_label'].tolist()))
        
    except:
        st.write("No data")
    
    submit_viz = st.form_submit_button('Submit visualization input')
    if submit_viz:
        st.write("Start date:",simulation_slider[0], "End date:",simulation_slider[1])
        st.write("Cluster:",select_cluster)


with st.container():
    try:
        
        #viz = dashboard_main.dashboard_layout(st.session_state['pop_track_df'],st.session_state['cluster_locations'],simulation_slider, select_cluster)
        if submit_viz:
        #if (st.session_state['travel_history'].shape[0] != 0) and (st.session_state['pop_track_df'].shape[0] != 0):
            dashboard_main.dashboard_layout(st.session_state['pop_track_df'],st.session_state['cluster_locations'],simulation_slider, select_cluster)
    except:
        st.write('No data')
    
    
    
    

    




