# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 16:45:36 2023

@author: User
"""
import streamlit as st
import plotly.express as px
import pandas as pd
import datetime
import glob
import process_movement



#st.set_page_config(layout="wide")

#------------- Functions part -----------------
def filter_date(data,date):
    filtered_data = data[(data.date >= date[0]) & (data.date <= date[1])]
    return filtered_data

def filter_date_individual(data,date):
    filtered_data = data[(data.date >= date[0]) & (data.date <= date[1])]
    return filtered_data

def to_summarize_data_by_cluster(data):
    summarized_data = data.groupby(['Cluster'],as_index=False).agg({'Healthy': 'mean',"Infected":'mean',"M_Suscept":"mean", "M_Incubate":"mean","M_incubate_hidden":"mean","M_Infected": "mean","Mosquitoes_prevalence":"mean","Area_Risk":"mean"})
    return summarized_data

def to_summarize_by_date_by_cluster(data):
    data_sum = data.groupby(['date','Cluster'],as_index=False).agg({'Healthy': 'mean',"Infected":'mean',"M_Suscept":"mean", "M_Incubate":"mean","M_incubate_hidden":"mean","M_Infected": "mean","Mosquitoes_prevalence":"mean","Area_Risk":"mean"})
    return data_sum

def filter_cluster(data,cluster):
    if not cluster == "All":
        data_new = data.loc[data['Cluster'] == cluster]
    else:
        data_new = data
        
    return data_new

def filter_cluster_individual(data,cluster):
    if not cluster == "All":        
        data_new = data.loc[data['start'] == cluster]
        data_new = data_new.loc[data_new['start'].astype('int64') == data_new['destination'].astype('int64')]
    else:
        data_new = data.loc[data['start'].astype('int64') == data['destination'].astype('int64')]
        
    return data_new


def get_list_of_cluster(lst_unq):
    cluster_list = ["All"]
    
    for i in lst_unq:
        cluster_list.append(i)
        
    return cluster_list


def create_route_table(date):
    
    path_travel = r"D:\Py_WebAppProj\result\by_date\travels\*.csv"
    allDay_cluster = glob.glob(path_travel) #os.path.join(path_cluster , "/*.csv")
    cluster_lst = []
    
    for file_clus in allDay_cluster:
        df = pd.read_csv(file_clus)
        
        #----- Select Cluster -----#
        #df_by_cluster = filter_cluster_individual(df,cluster)
        
        #----- Select day ------#
        df_c = filter_date_individual(df,date)
        
        df_c = df_c.loc[df_c['start'].astype('int64') != df_c['destination'].astype('int64')]
        
        cluster_lst.append(df_c)
        
    data_prop = pd.concat(cluster_lst,ignore_index=True)
    
    route_df = data_prop.groupby(['group','date','start','destination'])['health_stage'].value_counts().unstack(fill_value=0).reset_index()
    route_df["Route"] =  route_df['start'].astype(str) + '->' + route_df['destination'].astype(str)
    
    return route_df


def individual_risk_calculation(cluster,date):
    
    path_travel = r"D:\Py_WebAppProj\result\by_date\travels\*.csv"
    allDay_cluster = glob.glob(path_travel) #os.path.join(path_cluster , "/*.csv")
    individual_lst = []
    
    for file_clus in allDay_cluster:
        df = pd.read_csv(file_clus)
        
        #----- Select Cluster -----#
        df_by_cluster = filter_cluster_individual(df,cluster)
        
        #----- Select day ------#
        df_c = filter_date_individual(df_by_cluster,date)
        
        data_indi = df_c.loc[df_c['health_stage'] == "Healthy"]
        #------Hourly risk (negation)------
        data_indi.loc[:,'negation_individual_risk'] = data_indi['individual_risk'].apply(lambda x: 1 - x)
        
        #------Aggregate to get the individual risk of an individual for all trips-------
        #-------(product of negation)-----
        data_indi_agg = data_indi.groupby(['agentID','group','date','start'])['negation_individual_risk'].prod().to_frame().rename(columns={"negation_individual_risk":"product_negation_individual_risk"}).reset_index()

        #------ 1-(product of negation)------
        data_indi_agg.loc[:,'1-product_negation_individual_risk'] = data_indi_agg['product_negation_individual_risk'].apply(lambda x: 1 - x)
        
        individual_lst.append(data_indi_agg)
        
    data_prop = pd.concat(individual_lst,ignore_index=True)
    

    data_prop.rename(columns={'1-product_negation_individual_risk':'daily_indi_risk'},inplace=True)
    data_prop.drop(['product_negation_individual_risk'],axis=1,inplace=True)
    
    return data_prop


def prevalence_proportion(cluster,date):
    
    path_travel = r"D:\Py_WebAppProj\result\by_date\travels\*.csv"
    allDay_cluster = glob.glob(path_travel) #os.path.join(path_cluster , "/*.csv")
    cluster_lst = []
    
    for file_clus in allDay_cluster:
        df = pd.read_csv(file_clus)
        
        #----- Select Cluster -----#
        df_by_cluster = filter_cluster_individual(df,cluster)
        
        #----- Select day ------#
        df_c = filter_date_individual(df_by_cluster,date)
        
        data_prop_day = df_c.groupby(['group'])['health_stage'].value_counts().to_frame().rename(columns={"health_stage":"health_stage_count"}).reset_index()
                
        cluster_lst.append(data_prop_day)
        
    data_prop = pd.concat(cluster_lst,ignore_index=True)
    
    data_prop = data_prop.groupby(['group','health_stage'])['health_stage_count'].sum().to_frame().reset_index()
    data_prop_total = data_prop.groupby(['group']).sum().reset_index().rename(columns={'health_stage_count':'health_stage_total'})

    data_prop = data_prop.merge(data_prop_total,how='left',on='group')
    data_prop['health_stage_percent'] = (data_prop['health_stage_count']/data_prop['health_stage_total'])*100
    data_prop.sort_values(by=['group','health_stage_percent'],ascending=False,inplace=True)
    data_prop.sort_values(by=['group'],inplace=True)
    
    return data_prop





#-------------- Dashboard layout part -----------------

def dashboard_layout(data_cluster,data_location,simulation_slider,select_cluster):
    
    
    cluster_detail = data_cluster #st.session_state['pop_track_df']
    cluster_locations = data_location #st.session_state['cluster_locations']

    #------------- Create mobility table -----------------

    #cluster_detail["population"] = cluster_detail[["Healthy","Exposed","Infected","Recovery"]].sum(axis=1)
    route_df = create_route_table(simulation_slider)
    
    
    #base_map = st.radio("Select based map", ["open-street-map","stamen-terrain","carto-positron"])
    col1, col2 = st.columns(2,gap="medium")
    col3, col4 = st.tabs(['Susceptible Human','Infected Human'])
    col5, col5_5, col6 = st.tabs(['Susceptible mosquitoes','Incubated hidden','Infected mosquitoes'])
    
    col7, col8 = st.tabs(['Average individual risk','Proportion of health status'])
    #risk_table_expander = st.expander("Individual risk and proportion of health status")
    
    
    #---------------- Processing data ----------------
    filtered_cluster = filter_date(cluster_detail,simulation_slider)
    #st.dataframe(filtered_cluster)
    #st.write(filtered_cluster.columns.tolist())
    
    by_cluster  = filter_cluster(filtered_cluster,select_cluster)
    by_date_cluster = to_summarize_by_date_by_cluster(by_cluster)
    filter_travel = filter_date(route_df[['group','date','Route','Healthy','Infected']],simulation_slider) #------ 1.data_travel -> route_df -----#
    summarized_data = to_summarize_data_by_cluster(by_cluster)
    summarized_data = summarized_data.merge(cluster_locations, left_on='Cluster',right_on='id',  how='left')
    
    
    #---------------- Processing individual risk table ----------------
    st.session_state['individual_show'] = individual_risk_calculation(select_cluster,simulation_slider) #---- individual_risk_calculation_test
    st.session_state['prop_health_stage'] = prevalence_proportion(select_cluster,simulation_slider)
    
    indiviudal_date = st.session_state['individual_show'].groupby(['group'],as_index=False)['daily_indi_risk'].mean()
    indiviudal_date_fig = px.bar(indiviudal_date, x='group', y='daily_indi_risk', color='group',title ='Average individual risk by groups')
    health_status_fig = px.histogram(st.session_state['prop_health_stage'], x='group', y='health_stage_percent', color='health_stage', 
                                     barmode='group', text_auto='.2s', title='Proportion of health status by groups')
    
    individual = process_movement.convert_df(st.session_state['individual_show'])
    proportion_health = process_movement.convert_df(st.session_state['prop_health_stage'])
    
    #st.write(summarized_data)
    
    #---------------- Map visualization ----------------
    fig = px.scatter_mapbox(summarized_data, lat = 'latitude', lon = 'longitude', size = "Mosquitoes_prevalence",
                            color = "Cluster", hover_name = "Cluster", hover_data=["M_Suscept","M_Infected","Area_Risk","Mosquitoes_prevalence"],color_continuous_scale='Rainbow')
    fig.update_layout(mapbox_style = 'open-street-map',margin={"r":10,"t":10,"l":10,"b":10}) #mapbox_style = base_map,
    
    show_map = col1.plotly_chart(fig, use_container_width = True)
    
    #filter_route_detail = new_route_df.groupby(['Route'],as_index=False).agg({'Healthy': 'sum',"Infected":'sum'})
    
    #----------------------------------------------
    risk_fig = px.line(by_date_cluster, x='date', y='Area_Risk', color='Cluster', markers=True ,title= "Cluster Risk overview")
    
    #----------------------------------------------
    m_inf_fig = px.line(by_date_cluster, x='date', y='M_Infected', color='Cluster', markers=True, title="Population of Infected mosquitoes overview")
    
    #----------------------------------------------
    m_sus_fig = px.line(by_date_cluster, x='date', y='M_Suscept', color='Cluster', markers=True, title="Population of Susceptible mosquitoes overview")
    
    #----------------------------------------------
    m_incu_fig = px.line(by_date_cluster, x='date', y='M_incubate_hidden', color='Cluster', markers=True, title="Population of Incubated mosquitoes overview")

    #----------------------------------------------
    h_sus_fig = px.line(by_date_cluster, x='date', y='Healthy', color='Cluster', markers=True, title= "Susceptible Human agents on each cluster")

    #----------------------------------------------
    #h_inc_fig = px.line(filtered_cluster, x='date', y='Exposed', color='Cluster', markers=True,title= "Exposed Agent on each cluster" ) ,h_inc_fig

    #----------------------------------------------
    h_inf_fig = px.line(by_date_cluster, x='date', y='Infected', color='Cluster', markers=True, title= "Infected Human agents on each cluster")
    
    #risk_table = st.expander() model_envi.convert_df()
    
    table1 = col7.plotly_chart(indiviudal_date_fig,use_container_width=True), col7.download_button("Individual risk data", data = individual,
                                                                                       file_name = "Individual_date{}_to{}_{}.csv".format(simulation_slider[0],simulation_slider[1],datetime.datetime.now()))
    table2 = col8.plotly_chart(health_status_fig,use_container_width=True), col8.download_button("Proportion of health status data", data = proportion_health,
                                                                                       file_name = "Proportion_of_population_date{}_to{}.csv".format(simulation_slider[0],simulation_slider[1]))
    
    viz_all = show_map, col2.write("Show travel routes"),col2.dataframe(filter_travel,use_container_width=True),col4.plotly_chart(h_inf_fig,use_container_width=True),col3.plotly_chart(h_sus_fig,use_container_width=True), 
    col5.plotly_chart(m_sus_fig,use_container_width=True), col5_5.plotly_chart(m_incu_fig,use_container_width=True), col6.plotly_chart(m_inf_fig,use_container_width=True), st.plotly_chart(risk_fig,use_container_width=True),table1,table2
    
    return  viz_all

