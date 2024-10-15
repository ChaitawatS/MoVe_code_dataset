# -*- coding: utf-8 -*-
"""
Created on Sun Nov 20 12:10:50 2022

@author: User
"""

# define class
import pandas as pd
import numpy as np
import random
import copy
import math
#import datetime
from numpy.random import choice
import glob
import os
import streamlit as st



#------------------- Mosquitoes -------------------#
def update_mosquitoes(hr,ind,date,cluster_detail_var,cluster_stage_var):
    
    for i in range(0,len(cluster_detail_var)):
        
        if cluster_detail_var[i].known_params == True:
            #------------------ Copies of previous day variables
            temp_ms = copy.copy(cluster_detail_var[i].mos_s) #math.ceil
            temp_ml = copy.copy(cluster_detail_var[i].mos_l)
            temp_hide_latent = copy.copy(cluster_detail_var[i].mos_latent)
            temp_mi = copy.copy(cluster_detail_var[i].mos_i)
            n_m = temp_ms + temp_mi + temp_hide_latent
            
            #------------------- Mosquitoes susceptible population increment (Current day)
            #----- Mosquitoes susceptible Birth -----
            cluster_detail_var[i].mos_s += (cluster_detail_var[i].mos_birth_rate[ind]/24)*n_m*(1-(n_m/cluster_detail_var[i].mos_carry_capacity))
            
            
            #------------------- Mosquitoes susceptible -> latent (Incubation) population
            if cluster_detail_var[i].population > 0:
                cluster_detail_var[i].mos_s -= (cluster_detail_var[i].prob_of_infect_to_mos[ind])*(cluster_detail_var[i].biting_rate[ind]/24)*(temp_ms)*((cluster_detail_var[i].patient+cluster_detail_var[i].patient_external)/cluster_detail_var[i].population)
                cluster_detail_var[i].mos_l += (cluster_detail_var[i].prob_of_infect_to_mos[ind])*(cluster_detail_var[i].biting_rate[ind]/24)*(temp_ms)*((cluster_detail_var[i].patient+cluster_detail_var[i].patient_external)/cluster_detail_var[i].population)
            
            
            #------------------- All mosquitoes turn hidden latent population and rest for ...(incubation peroid)... days
            cluster_detail_var[i].mos_l -= temp_ml
            cluster_detail_var[i].mos_latent += temp_ml
                    
            
            #------------------- Mosquitoes latent -> infected population, after ...(incubation peroid)... days
            delay = int(hr - (cluster_detail_var[i].extentic_incubation_period[ind]*24))
            
            if delay >= 0:
                cluster_detail_var[i].mos_latent -= cluster_stage_var[delay][i].mos_l          
                cluster_detail_var[i].mos_i += cluster_stage_var[delay][i].mos_l
                
                if cluster_detail_var[i].mos_latent < 0:
                    cluster_detail_var[i].mos_latent = 0
            
            
            #------------------- Mosquitoes susceptible population Death
            cluster_detail_var[i].mos_s -= (cluster_detail_var[i].mos_mortal_rate[ind]/24)*temp_ms
            
            #------------------- Mosquitoes latent (Incubation) population Death
            if delay >= 0:
                cluster_detail_var[i].mos_latent -= (cluster_detail_var[i].mos_mortal_rate[ind]/24)*cluster_stage_var[delay][i].mos_l
                
                if cluster_detail_var[i].mos_latent < 0:
                    cluster_detail_var[i].mos_latent = 0
              
            #------------------- Mosquitoes infected population Death
            cluster_detail_var[i].mos_i -= (cluster_detail_var[i].mos_mortal_rate[ind]/24)*temp_mi
                
            
            #------------------- Calculate risk of all areas in a day
            cluster_detail_var[i].mos_prevalence = (cluster_detail_var[i].mos_i)/((cluster_detail_var[i].mos_s) + (cluster_detail_var[i].mos_latent) + (cluster_detail_var[i].mos_i)) #math.ceil
            cluster_detail_var[i].area_risk = 1-(np.power(1-(cluster_detail_var[i].mos_prevalence*cluster_detail_var[i].prob_of_spread_to_human[ind]),cluster_detail_var[i].biting_rate[ind]/24))
        
        if cluster_detail_var[i].known_params == False:
            #----- if known_param is No-----
            cluster_detail_var[i].mos_s = cluster_detail_var[i].constant_sus[ind] #random.randrange(10,15)
            cluster_detail_var[i].mos_i = cluster_detail_var[i].constant_inf[ind]
            
            
            cluster_detail_var[i].mos_prevalence = (cluster_detail_var[i].mos_i)/(cluster_detail_var[i].mos_s + cluster_detail_var[i].mos_i)#math.ceil
            cluster_detail_var[i].area_risk = 1-(np.power(1-(cluster_detail_var[i].mos_prevalence*cluster_detail_var[i].prob_of_spread_to_human[ind]),cluster_detail_var[i].biting_rate[ind]/24))
    

#------------- Mobility 1 --------------
#get transition matrices
@st.cache_data
def read_mobility_file(mobility_file):
    #travel = pd.read_json(mobility_file)
    travel = pd.read_csv(mobility_file)
    #travel = travel.sort_values('origin',ignore_index=True)
    travel['prob_matrix'] = travel['count']/travel.groupby(['origin'])['count'].transform('sum')
    travel_mat = travel[['origin','dest','count','prob_matrix']] #,'prob_matrix'
    return travel_mat


#define probility function and travel rules

def takeodds(probability): #funciton for taking the probility ex. roll for getting malaria
    return random.random() < probability


def route(agent,mobility_file):
    draw = [None]
    origin_lst_new = mobility_file['origin'].unique().tolist()
    
    if agent.cluster in origin_lst_new:
        item = agent.cluster
        de_lst = mobility_file[mobility_file['origin'] == item]['dest'].tolist()
        de_prob_lst = mobility_file[mobility_file['origin'] == item]['prob_matrix'].tolist()
        draw = choice(de_lst,1,True,de_prob_lst)
        return draw[0]


def travelOdds(agent,group,ind): # function for roll the odds of travel in each occupation ,group
    group_str = str(group)
    destination= None
    if group == group_str:
        if takeodds(1):
            return route(agent,agent.mobility_obj[ind])
        


#------------- Mobility 2 --------------
#create mobility funciton for agent
#@st.cache_data
def allocateAgent(agent,newcluster,cluster_detail,cluster_field): # function for agent (remove agent from old cluster and append to new cluster)
    cluster_detail[agent.cluster].population -=1
    cluster_detail[newcluster].population +=1
    if agent.health_stage == "Infected": #check for infected agent for updating in cluster detail
        cluster_detail[agent.cluster].patient -= 1
        cluster_detail[newcluster].patient +=1
    cluster_field[newcluster].append(agent)
    index = 999 #placeholder for finding the agnet id
    for i in range(0,len(cluster_field[agent.cluster])): #loop for find agent id in old cluster
        if(agent.id == cluster_field[agent.cluster][i].id):
            index = i
    cluster_field[agent.cluster].pop(index) #remove agent from old cluster
    cluster_field[newcluster][-1].cluster = newcluster #update the cluster number of traveling agent





#------------- Disease transmission machanism --------------
#create function for tracking timer( countdown incubating & infecting period) and changing agent state

def infectingOdds(_all_agent,cluster_detail_var,ind):
    for i in range(0,len(_all_agent)):
        if _all_agent[i].health_stage == "Healthy": # look for agent with susceptible stage
            #-----make it generalizable------#
            #-----the threshold can be get as an input per group------# (flexibility)
            #-----cluster_detail_var_var[i].prob_of_spread_to_human[ind]----# 1-(pow((1-cluster_detail_var_var[_all_agent[i].cluster].area_risk),random.randrange(3,6)))
            _all_agent[i].risk = cluster_detail_var[_all_agent[i].cluster].area_risk #[i]
            if takeodds(_all_agent[i].risk): # roll the odds with the risk of each agent, If true agent got infected > 0.02
                _all_agent[i].health_stage = "Exposed"
                _all_agent[i].risk = 1
                #cluster_detail_var_var[_all_agent[i].cluster].patient +=1
                

def infectingRecoveryOdds(_all_agent,cluster_detail_var,ind,recovery_rate):
    for i in range(0,len(_all_agent)):
        if _all_agent[i].health_stage == "Exposed":
            _all_agent[i].risk = 1 #[i] _all_agent[i]
            _all_agent[i].timer += 1
            if _all_agent[i].timer == 7*24:
                if takeodds(1):
                    _all_agent[i].health_stage = "Infected"
                    _all_agent[i].timer = 0
                    cluster_detail_var[_all_agent[i].cluster].patient +=1
                else:
                    _all_agent[i].timer = 1
        
        if _all_agent[i].health_stage == "Infected":
            #_all_agent[i].risk = 1-(pow((1-cluster_detail_var[_all_agent[i].cluster].area_risk),random.randrange(1,5)))
            _all_agent[i].risk = 1
            _all_agent[i].timer += 1
            if _all_agent[i].timer == 7*24: #7
                if takeodds(recovery_rate):
                    _all_agent[i].health_stage = "Recovery"
                    _all_agent[i].timer = 0
                    _all_agent[i].risk = 0
                    cluster_detail_var[_all_agent[i].cluster].patient -= 1 #tracking the nunber of patient in the cluster
                else:
                    #_all_agent[i].timer = 1
                    _all_agent[i].health_stage = "Death"
        
        if _all_agent[i].health_stage == "Recovery":
            _all_agent[i].timer += 1
            if _all_agent[i].timer == 80*24: #80
                _all_agent[i].health_stage = "Healthy"
                _all_agent[i].timer = 0
                #infectingOdds(_all_agent[i],cluster_detail_var,ind)
                #_all_agent[i].risk = 1-(pow((1-cluster_detail_var_var[_all_agent[i].cluster].area_risk),1))
                
        if _all_agent[i].health_stage == "Death":
            cluster_detail_var[_all_agent[i].cluster].patient -= 1
            cluster_detail_var[_all_agent[i].cluster].population -= 1
            #del _all_agent[i]


#------------- Tracking moving agents --------------
#create function for counting each healthstage of inputted group
#count_prop = []
def count_health_stage(agent_group):
    count_prop = []
    
    count_healthy = 0
    count_exposed = 0
    count_infect = 0
    count_recovery = 0
    for i in range(0,len(agent_group)):
        if agent_group[i].health_stage == "Healthy":
            count_healthy += 1
        elif agent_group[i].health_stage == "Exposed":
            count_exposed += 1
        elif agent_group[i].health_stage == "Infected":
            count_infect += 1
        elif agent_group[i].health_stage == "Recovery":
            count_recovery += 1
    count_prop.append([count_healthy,count_infect,count_recovery,count_exposed])

    return [count_healthy,count_infect,count_recovery,count_exposed]


def record_of_external_population(hr,file,destination_clus_idx,_cluster_detail,original_external_patient):
    
    des_clus = choice(destination_clus_idx,1,True)
    
    for i in range(file.shape[0]):
        
        recover_time = file.iloc[i,0] + 8
        
        if hr == file.iloc[i,0]:
            
            for y in range(len(_cluster_detail)):
                #--- Reset number of external patient and population every new month
                original_external_patient[y].population = original_external_patient[y].population - original_external_patient[y].patient_external
                original_external_patient[y].patient_external *= 0

            #--- Add the number at the destination
            original_external_patient[des_clus[0]].patient_external += file.iloc[i,2]
            original_external_patient[des_clus[0]].population += file.iloc[i,2]
            
        if hr == recover_time:
            for y in range(len(_cluster_detail)):
                #--- Reset number of external patient and population every new month
                original_external_patient[y].population = original_external_patient[y].population - original_external_patient[y].patient_external
                original_external_patient[y].patient_external *= 0
    

@st.cache_data
def main_simulation(_cluster_detail,_cluster_field,_sim_hr,_all_agent,_season,_season_lst,external_population):
    # create array to keep tracking each stage of simulation
    pop_track_df = pd.DataFrame(columns=["date","Hour","Season","Cluster","Healthy","Exposed","Infected","Recovery","M_Suscept","M_Incubate","M_incubate_hidden","M_Infected","Mosquitoes_prevalence","Area_Risk"])
    #stage=[]
    cluster_stage=[]
    #stage=[copy.deepcopy(_cluster_field)]
    cluster_stage=[copy.deepcopy(_cluster_detail)]
        
    
    pop_track_df_lst = []
    travel_history_lst = []
    
    #----- External population and patient
    destination_clus_idx = [0,1,3] #[_cluster_detail[y].cluster_number for y in range(len(_cluster_detail)) if _cluster_detail[y].known_params == True] #file.iloc[0,3:]
    original_external_patient = [_cluster_detail[y] for y in range(len(_cluster_detail))]

    #df = pd.DataFrame(columns=["date","Healthy","Exposed","Infected","Recovery"])

    #travel_history = pd.DataFrame(columns=["agentID","group","date","Hour","Season","start","destination","health_stage","individual_risk","timer","area_risk"])

    #update area risk of each cluster on first date
    for i in range(0,len(_cluster_detail)):
        _cluster_detail[i].area_risk = _cluster_detail[i].mos_i/(_cluster_detail[i].mos_s + _cluster_detail[i].mos_l + _cluster_detail[i].mos_i)

    #update health status of each agent on first date
    #infectingOdds()
    #infectingRecoveryOdds()

    #update detail of each cluster on first date
    for cluster in range(0,len(_cluster_field)):
        cluster_prop = count_health_stage(_cluster_field[cluster])
        pop_track_df = pd.concat([pop_track_df,pd.DataFrame.from_records([{"date":0,"Hour":0,"Season":0,"Cluster": cluster,"Healthy":cluster_prop[0],"Exposed":cluster_prop[3],"Infected":cluster_prop[1],"Recovery":cluster_prop[2],
                                                                           "total_pop":_cluster_detail[cluster].population,"total_patient":_cluster_detail[cluster].patient,"External_infected":_cluster_detail[cluster].patient_external,
                                                                           "M_Suscept":_cluster_detail[cluster].mos_s,"M_Incubate":_cluster_detail[cluster].mos_l,"M_incubate_hidden":_cluster_detail[cluster].mos_latent,"M_Infected":_cluster_detail[cluster].mos_i,
                                                                           "Mosquitoes_prevalence":_cluster_detail[cluster].mos_prevalence,"Area_Risk":_cluster_detail[cluster].area_risk}])],ignore_index=True)
    
    
    date = 0
    ind = 0
    #date_to_autoSave = math.floor((_sim_hr/24)/4)
        
    for hr in range(0,_sim_hr): # start simulation
    
        #define array for traveller
        #traveller = []
        #count prop from all of Cluster
        #count_health = count_health_stage(_all_agent)
        
        #df = pd.concat([df, pd.DataFrame.from_records([{"date":date,"Hour":hr,"Season":ind,"Healthy":count_health[0],"Exposed":count_health[3],"Infected":count_health[1],"Recovery":count_health[2]}])], ignore_index=True)
        
        
        #----Add seasonality-----
        if hr == 0:
            date = 0
            if _season == 1:
                ind = 0
                #item = lst_test[ind]
            else:
                for s in range(len(_season_lst)):
                    if date in _season_lst[s]:
                        ind = s
                        #item = lst_test[ind]
            st.write("day: {}, season: {}".format(date+1,ind+1))
        
        
        else:
           if hr%24 == 0:
               date += 1
               if _season == 1:
                   ind = 0
                   #item = lst_test[ind]
               else:
                   for s in range(len(_season_lst)):
                       if date in _season_lst[s]:
                           ind = s
                           #item = lst_test[ind]
               st.write("day: {}, season: {}".format(date+1,ind+1))
               
        
        
        #-------Update Agents Health status & mosquetoes stage--------------------------------------
        record_of_external_population(date,external_population,destination_clus_idx,_cluster_detail,original_external_patient)
        update_mosquitoes(hr,ind,date,_cluster_detail,cluster_stage) #,known_params
        infectingOdds(_all_agent,_cluster_detail,ind) #infectingOdds()
        infectingRecoveryOdds(_all_agent,_cluster_detail,ind,recovery_rate=1) #infectingRecoveryOdds()
        
        
        
        #-------loop for tracking the cluster status on each date of simulation-----------
        for cluster in range(0,len(_cluster_field)):
            cluster_prop = count_health_stage(_cluster_field[cluster])
            pop_track_df_data = {"date":date+1,"Hour":hr+1,"Season":ind+1,"Cluster": cluster,
                                 "Healthy":cluster_prop[0],"Exposed":cluster_prop[3],"Infected":cluster_prop[1],"Recovery":cluster_prop[2],
                                 "total_pop":_cluster_detail[cluster].population,"total_patient":_cluster_detail[cluster].patient,"External_infected":_cluster_detail[cluster].patient_external,
                                 "M_Suscept":_cluster_detail[cluster].mos_s,"M_Incubate":_cluster_detail[cluster].mos_l,"M_incubate_hidden":_cluster_detail[cluster].mos_latent,"M_Infected":_cluster_detail[cluster].mos_i,
                                 "M_Birth_rate":_cluster_detail[cluster].mos_birth_rate[ind],"M_Death_rate":_cluster_detail[cluster].mos_mortal_rate[ind],
                                 "Mosquitoes_prevalence":_cluster_detail[cluster].mos_prevalence,"Area_Risk":_cluster_detail[cluster].area_risk}
            
            pop_track_df_lst.append(pop_track_df_data)
            
        #------ Auto-save ------#
        if hr == 0:
            continue
        if hr%24 == 23:
            pop_test = pd.DataFrame.from_records(pop_track_df_lst)
            #pop_test.to_csv("D:/Py_WebAppProj/result/by_date/clusters/cluster_detail_day{}.csv".format(date),encoding='utf-8')
            pop_test.to_csv("D:/Py_WebAppProj/result/by_date/clusters/cluster_detail_day{}.csv".format(date),encoding='utf-8') #---- continue smulaton -----#
            pop_track_df_lst.clear()
        
        
        #-------Movement with Markov process--------------------------------------  
        #loop all agent to make them decide whether to travel to somewhere
        for i in range(0,len(_all_agent)):
            destination = travelOdds(_all_agent[i],_all_agent[i].group,ind)
            travel_history_data = {"agentID":_all_agent[i].id,"group":_all_agent[i].group,
                                   "date":date+1,"Hour":hr+1,"Season":ind+1,"start":_all_agent[i].cluster,"destination":destination,
                                   "health_stage": _all_agent[i].health_stage,"individual_risk":_all_agent[i].risk,
                                   "timer":_all_agent[i].timer,"area_risk":_cluster_detail[_all_agent[i].cluster].area_risk}
            
            travel_history_lst.append(travel_history_data)
                            
            
            #infectingOdds()
            #infectingRecoveryOdds()
            allocateAgent(_all_agent[i],destination,_cluster_detail,_cluster_field)
        
        #------ Auto-save ------#
        if hr == 0:
            continue
        if hr%24 == 23:
            travel_test = pd.DataFrame.from_records(travel_history_lst)
            #travel_test.to_csv("D:/Py_WebAppProj/result/by_date/travels/travel_history_day{}.csv".format(date),encoding='utf-8')
            travel_test.to_csv("D:/Py_WebAppProj/result/by_date/travels/travel_history_day{}.csv".format(date),encoding='utf-8') #---- continue smulaton -----#
            travel_history_lst.clear()
            
                    
            
            
        #update_pop_track_df(pop_track_df)
        #infectingOdds()
        #infectingRecoveryOdds()        
        #st.write("day: {}, season: {}".format(date+1,ind+1))
                
        
        cluster_stage.append(copy.deepcopy(_cluster_detail))
        #stage.append(copy.deepcopy(_cluster_field))
        #----------- End of simulation----------#
    
    
    
    #------ All file save-------#
    #--- Clusters ---#
    #path_cluster = r"D:\Py_WebAppProj\result\by_date\clusters\*.csv"
    path_cluster = r"D:\Py_WebAppProj\result\by_date\clusters\*.csv"
    allDay_cluster = glob.glob(path_cluster)
    cluster_lst = []
    
    for file_clus in allDay_cluster:
        df_c = pd.read_csv(file_clus)
        cluster_lst.append(df_c)
        
    pop = pd.concat(cluster_lst,ignore_index=True) #pd.DataFrame.from_records(cluster_lst)
        
    
    
    pop_track_df = pop #pd.concat([pop_track_df, pop],ignore_index=True)
    
    
    return pop_track_df
