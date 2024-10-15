#!/usr/bin/env python
# coding: utf-8



import pandas as pd
pd.options.mode.chained_assignment = None

import numpy as np
np.seterr(divide='ignore', invalid='ignore')
from scipy.spatial.distance import pdist, squareform ## For distance matrix calculation ##


from sklearn.cluster import DBSCAN
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.metrics import davies_bouldin_score

import streamlit as st
import pyproj
import math



    
### Distance (m) calculation ####
@st.cache_data
def distance(data,lon_org,lat_org,lon,lat,time_zone=47):
    #conversion to utm
    
    projection = pyproj.Proj(proj='utm', zone=time_zone, ellps='WGS84')
    x_o, y_o = projection(data['{}'.format(lon_org)], data['{}'.format(lat_org)]) #from Origin
    x_d, y_d = projection(data['{}'.format(lon)], data['{}'.format(lat)])
    
    #Euclidean distance (m)
    distance_lat = y_d - y_o
    distance_lon = x_d - x_o
    
    #Euclidean distance (m)
    d_m = np.sqrt((distance_lat**2) + (distance_lon**2))
    
    return d_m


### Harversine distance (m) calculation ####
@st.cache_data
def harversine_distance(data,lon_org,lat_org,lon,lat):
    radius = 6371000 #earth radius in meter
    
    distance_lat = math.radians(data[lat] - data[lat_org])
    distance_lon = math.radians(data[lon] - data[lon_org])
    
    a = (math.sin(distance_lat/2)**2) + math.cos(math.radians(data[lat_org]))*math.cos(math.radians(data[lat]))*(math.sin(distance_lon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d_m = radius * c #Distance in meters
    
    return d_m


### Get Max distance(Meter -> Kilometer) within each K-means group ###
def get_max_distance(data,dis1,dis2):
    max_dis = max(data['{}'.format(dis1)],data['{}'.format(dis2)])
    return max_dis


### Get distance(Meter -> Kilometer) between means of the K-means group ### (distance matrix form) ###
def get_distance_matrix(data,lon,lat):
    projection = pyproj.Proj(proj='utm', zone=47, ellps='WGS84')
  
    x, y = projection(data['{}'.format(lon)], data['{}'.format(lat)])
  
    data['{}'.format(lon)] = x
    data['{}'.format(lat)] = y
    dist_matrix = pdist(data, metric='euclidean')
    dist_matrix = squareform(dist_matrix)
        
    return pd.DataFrame(dist_matrix)


### Calculate distance between K-means clusters (dist_K_ij) ###
### Distance between K-means clusters' means (dist_meanK_ij) ###
### Distance between mean of K-means cluster and the furthest point (dist_Maxwithin_i) ###

### dist_K_ij = dist_meanK_ij - (dist_Maxwithin_i + dist_Maxwithin_j) ###


def dist_Kmeans_singleLink(data1,col1,data2):
    lenght_index = data1.shape[0]

  ## Index & Calculated distance
    lst_dist = []
    
    for i in range(lenght_index):
        for j in range(lenght_index):
            if i != j:
        ### Distance between mean of K-means cluster and the furthest point (dist_Maxwithin_i) |  (dist_Maxwithin_j) ###
                dist_within_furtherest = data1.loc[i,'{}'.format(col1)] + data1.loc[j,'{}'.format(col1)]

        ### Distance between K-means clusters' means (dist_meanK_ij) ###
                dist_between_mean = data2.loc[i,j]

        ### Single-link distance between K-means (absolute value in case of negative results) ###
                dist_singleLink = dist_between_mean - dist_within_furtherest #np.absolute()

        ## Index i implies K-means group i + 1
        ## Index j implies K-means group j + 1
                lst_dist.append([[i,j],dist_singleLink])

    return lst_dist



### Grouping K-means clusters to merge ###
### Threshold to merge is ep (km) ###
def merge_Kmeans_group(lst,user_ep):
    mg = []
    non_mg = []

    for i in lst:
    ## ep came from DBSCAN ##
        if i[1] <= user_ep:
              mg.append(i[0])
        else:
              non_mg.append(i[0])
    return mg, non_mg



### Check unique pair ###
### or its palidrome pair ###
### This is because squareform matrix provides duplicated pairs which makes [0,2] and [2,0] are different ###
def get_unique_pair(lst):
    unq_lst = []
    for i in lst:
        j = i[::-1]
        if j not in unq_lst:
            unq_lst.append(i)

    return unq_lst



### dist_D_ij = dist_meanD_ij - (dist_Maxwithin_i + dist_Maxwithin_j) ###
def dist_dbscan_singleLink(data,max_dist_d1,max_dist_d2,dist_means):

    dist_within_furtherest = data['{}'.format(max_dist_d1)] + data['{}'.format(max_dist_d2)]

    dist_between_means = data['{}'.format(dist_means)]

    dist_singleLink = dist_between_means - dist_within_furtherest #np.absolute()

    return dist_singleLink



### Map group to the original data ###
def search_label_group(data,col,dict_lookup):
    for group, element in dict_lookup.items():
        if data['{}'.format(col)] in element:
            return group


### Group based on reachability ###
def group_reachability(lst):
    l = lst.values.tolist()
    out = []

    while len(l) > 0:
        first, *rest = l
        first = set(first)

        lf = -1
        while len(first) > lf:
            lf = len(first)

            rest2 = []
            for r in rest:
                if len(first.intersection(set(r))) > 0:
                    first |= set(r)
                else:
                    rest2.append(r)     
            rest = rest2

        out.append(first)
        l = rest
    return out



### Group based on reachability 2 ###
def group_reachability_label(lst):
    lookup_kdbscan = {}
    group_len = len(lst)

    for x in range(group_len):
        lookup_kdbscan['{}'.format(x)] = []
        for y in lst[x]:
            lookup_kdbscan['{}'.format(x)].append(y)

    return lookup_kdbscan


#### K-means++ ####
@st.cache_data
def do_kMeans(data, k, col_lon, col_lat):
    ### KMeans model & parameters ###
    kmean_model = KMeans(n_clusters = k, init = 'k-means++', max_iter = 300)
    
    ### Get coordinat ###
    data_corr_kmeans = data[['{}'.format(col_lon), '{}'.format(col_lat)]]
    data_corr_kmeans = data_corr_kmeans.values.astype('float32')
    data_corr_kmeans
    
    
    ### Perform KMeans ###
    kmean_model.fit(np.radians(data_corr_kmeans))
    cluster_labels_kmeans = kmean_model.labels_
    data['cluster_label'] = pd.Series(cluster_labels_kmeans,index = data.index)
    
    return data


#### Conventional DBSCAN ####
@st.cache_data
def do_DBSCAN(data, ep, min_sam, col_lon, col_lat):
    
    ## This is traditional DBSCAN ##
    #Prepare DBSCAN model & parameters
    km_radius = 6371.0088
    ep = ep
    min_sam = min_sam
    epsilon = ep / km_radius #Radian in km
    db_model = DBSCAN(eps = epsilon, min_samples = min_sam)
    
    ### Prepare to perform DBSCAN ###
    data_matrix_temp = data[['{}'.format(col_lon), '{}'.format(col_lat)]]
    data_matrix_temp = data_matrix_temp.values.astype('float32')
    
    ### Perform DBSCAN and assign cluster in each group ###
    db_model.fit(np.radians(data_matrix_temp))
    cluster_labels = db_model.labels_
    data['cluster_label'] = pd.Series(cluster_labels,index=data.index)
    
    return data

#@st.cache
def do_hierachical():
    pass

#### Main KDBSCAN ####
@st.cache_data
def do_KDBSCAN(data, k, ep, min_sam, col_lon, col_lat):
    
    if k <= 1:
        df_all = do_DBSCAN(data, ep, min_sam, col_lon, col_lat)
        #df_all.rename(columns = {'cluster_label_dbscan':'kdbscan_group'}, inplace=True)
    else:
        ### KMeans model & parameters ###
        kmean_model = KMeans(n_clusters = k, init = 'k-means++', max_iter = 300)
        
        #Prepare DBSCAN model & parameters
        km_radius = 6371.0088
        ep = ep
        min_sam = min_sam
        epsilon = ep / km_radius #Radian in km
        db_model = DBSCAN(eps = epsilon, min_samples = min_sam) #Min samples j points
        
        ### Get coordinat ###
        data_corr_kmeans = data[['{}'.format(col_lon), '{}'.format(col_lat)]]
        data_corr_kmeans = data_corr_kmeans.values.astype('float32')
        data_corr_kmeans
        
        
        ### Perform KMeans ###
        kmean_model.fit(np.radians(data_corr_kmeans))
        cluster_labels_kmeans = kmean_model.labels_
        data['cluster_labelkmean'] = pd.Series(cluster_labels_kmeans,index = data.index)
       
        
        #DBSCAN each group of K-means
        df_lst = []
        
        for i in range(k):
            ### Extract data by K-mean cluster's results ###
            d = data.loc[data['cluster_labelkmean'] == i]
          
              ### Prepare to perform DBSCAN ###
            data_matrix_temp = d[['{}'.format(col_lon), '{}'.format(col_lat)]]
            data_matrix_temp = data_matrix_temp.values.astype('float32')
          
              ### Perform DBSCAN and assign cluster in each group ###
            db_model.fit(np.radians(data_matrix_temp))
            cluster_labels = db_model.labels_
            d['cluster_label_dbscan'] = pd.Series(cluster_labels,index=d.index)
          
            df_lst.append(d)
        
        df_all = pd.concat(df_lst)
    
    
        #######
        ### Step 1 (mergeing borders): Measure the distance between groups from K-means ###
        #######
        
        ### Create data containing Max distance within each K-means group ###
        mean_lst = []
        
        
        for i in range(k):
          ### Extract data by K-mean cluster's results ###
            d_s1 = df_all.loc[df_all['cluster_labelkmean'] == i]
        
        
          ## Get the furtherest locations (Max-Min) of each K-means group ##
            d_latMax = d_s1.groupby('cluster_labelkmean')['latitude'].max().to_frame()
            d_latMin = d_s1.groupby('cluster_labelkmean')['latitude'].min().to_frame()
        
            d_lonMax = d_s1.groupby('cluster_labelkmean')['longitude'].max().to_frame()
            d_lonMin = d_s1.groupby('cluster_labelkmean')['longitude'].min().to_frame()
            d_MaxLoc = d_lonMax.merge(d_latMax,on=['cluster_labelkmean'])
        
              ## Calculate Mean location of each K-means group ##
            d_latMean = d_s1.groupby('cluster_labelkmean')['latitude'].mean().to_frame().reset_index()
            d_lonMean = d_s1.groupby('cluster_labelkmean')['longitude'].mean().to_frame().reset_index()
            d_MeanLoc = d_lonMean.merge(d_latMean,on=['cluster_labelkmean'])
        
          ## Merge Mean, Min and Max location ##
            d_MeanLoc = d_MeanLoc.merge(d_MaxLoc,on=['cluster_labelkmean'],suffixes=['','_max'])
            d_MeanLoc = d_MeanLoc.merge(d_lonMin,on=['cluster_labelkmean'],suffixes=['','_min'])
            d_MeanLoc = d_MeanLoc.merge(d_latMin,on=['cluster_labelkmean'],suffixes=['','_min'])
        
            mean_lst.append(d_MeanLoc)
        
        mean_all = pd.concat(mean_lst)
        mean_all.reset_index(inplace=True)
        
        
        ### Get distance within clusters of each K-means ###
        mean_all['distanceWithin_mean_Max_m'] = mean_all.apply(lambda x: distance(x,'longitude','latitude','longitude_max','latitude_max'),axis=1)
        mean_all['distanceWithin_mean_Min_m'] = mean_all.apply(lambda x: distance(x,'longitude','latitude','longitude_min','latitude_min'),axis=1)
    
        ### Get Max distance(Meter -> Kilometer) within each K-means group ###
        mean_all['MaxWithinDistance_m'] = mean_all.apply(lambda x: get_max_distance(x,'distanceWithin_mean_Max_m','distanceWithin_mean_Min_m'),axis = 1)
        
        ### Convert to km ###
        mean_all['MaxWithinDistance_km'] = mean_all['MaxWithinDistance_m']/1000
        mean_all.drop(['index','longitude_max','latitude_max','longitude_min','latitude_min','distanceWithin_mean_Max_m','distanceWithin_mean_Min_m','MaxWithinDistance_m'],axis=1,inplace=True)
    
    
        ### Get distance(Meter -> Kilometer) between means of the K-means group ### (distance matrix form) ###
        mean_all_loc = mean_all[['longitude','latitude']] #.values.astype('float32')
        x = get_distance_matrix(mean_all_loc,'longitude','latitude')
        
        ### Convert to km ###
        x = x/1000
    
    
        ### Calculate distance between K-means clusters (dist_K_ij) ###
        ### Distance between K-means clusters' means (dist_meanK_ij) ###
        ### Distance between mean of K-means cluster and the furthest point (dist_Maxwithin_i) ###
        
        ### dist_K_ij = dist_meanK_ij - (dist_Maxwithin_i + dist_Maxwithin_j) ###
        ### Note that a list of the indecies is in Permutation style ### (index[0,1] != index[1,0]) ###
        
        distance_betweenKMeans_km = dist_Kmeans_singleLink(mean_all,'MaxWithinDistance_km',x)
    
        ### Grouping K-means clusters to merge ###
        ### Threshold to merge is ep (km) ###
        merge_index, pruned_index = merge_Kmeans_group(distance_betweenKMeans_km,ep)
    
    
        ### Check unique pair ###
        ### or its palidrome pair ###
        ### This is because squareform matrix provides duplicated pairs which makes [0,2] and [2,0] are different ###
    
        ## This size of the new list will be reduced by half ##
        unique_merge_index = get_unique_pair(merge_index)
        
        if len(unique_merge_index) == 0:
            ### Case: no K clusters are close to each other ###
            #######
            ### Step 2 (mergeing borders): Investigate if clusters of DBSCAN in 2 different K-means group where they have the distance less than "ep" can be merged ###
            #######
            kmean_lst = []
            for i in range(k):
                mean_lst_dk = []
                d_k = df_all.loc[df_all['cluster_labelkmean'] == i]
                dk_lst_dbscan = d_k['cluster_label_dbscan'].unique().tolist()
                for j in dk_lst_dbscan:
                    d_k_dbscan = d_k.loc[d_k['cluster_label_dbscan'] == j]
                
                    ## Get the furtherest locations (Max-Min) of each DBSCAN group ##
                    dk_latMax = d_k_dbscan.groupby('cluster_label_dbscan')['latitude'].max().to_frame()
                    dk_latMin = d_k_dbscan.groupby('cluster_label_dbscan')['latitude'].min().to_frame()
            
                    dk_lonMax = d_k_dbscan.groupby('cluster_label_dbscan')['longitude'].max().to_frame()
                    dk_lonMin = d_k_dbscan.groupby('cluster_label_dbscan')['longitude'].min().to_frame()
                    dk_MaxLoc = dk_lonMax.merge(dk_latMax,on=['cluster_label_dbscan'])
            
                    ## Calculate Mean location of each DBSCAN group ##
                    dk_latMean = d_k_dbscan.groupby('cluster_label_dbscan')['latitude'].mean().to_frame().reset_index()
                    dk_lonMean = d_k_dbscan.groupby('cluster_label_dbscan')['longitude'].mean().to_frame().reset_index()
                    dk_MeanLoc = dk_lonMean.merge(dk_latMean,on=['cluster_label_dbscan'])
            
                    ## Merge Mean, Min and Max location ##
                    dk_MeanLoc = dk_MeanLoc.merge(dk_MaxLoc,on=['cluster_label_dbscan'],suffixes=['','_max'])
                    dk_MeanLoc = dk_MeanLoc.merge(dk_lonMin,on=['cluster_label_dbscan'],suffixes=['','_min'])
                    dk_MeanLoc = dk_MeanLoc.merge(dk_latMin,on=['cluster_label_dbscan'],suffixes=['','_min'])
                    dk_MeanLoc['cluster_labelkmean'] = i
                    
                    ## Calculate distance between mean point and furtherest point ##
                    dk_MeanLoc['distanceWithin_mean_Max_m'] = dk_MeanLoc.apply(lambda x: distance(x,'longitude','latitude','longitude_max','latitude_max'),axis=1)
                    dk_MeanLoc['distanceWithin_mean_Min_m'] = dk_MeanLoc.apply(lambda x: distance(x,'longitude','latitude','longitude_min','latitude_min'),axis=1)
                    ## Get the max distance between mean point and furtherest point ##
                    dk_MeanLoc['MaxWithinDistance_m'] = dk_MeanLoc.apply(lambda x: get_max_distance(x,'distanceWithin_mean_Max_m','distanceWithin_mean_Min_m'),axis = 1)
                    ### Convert to km ###
                    dk_MeanLoc['MaxWithinDistance_km'] = dk_MeanLoc['MaxWithinDistance_m']/1000
                    dk_MeanLoc.drop(['longitude_max','latitude_max','longitude_min','latitude_min',
                                 'distanceWithin_mean_Max_m','distanceWithin_mean_Min_m','MaxWithinDistance_m'],axis=1,inplace=True)
                    
                    mean_lst_dk.append(dk_MeanLoc)
                    pruined_dk = pd.concat(mean_lst_dk)
                    
                new_data_dk = pruined_dk.merge(pruined_dk,how = "cross", suffixes=['_d1','_d2'])
                ### Drop comparison of each row if dbscan labels are duplicated ###
                new_data_dk = new_data_dk.drop(new_data_dk[(new_data_dk['cluster_label_dbscan_d1'].values == new_data_dk['cluster_label_dbscan_d2'].values)].index)
                    
            ### Calculate distance between DBSCAN clusters (dist_D_ij) from different K-means groups ###
            ### Distance between mean of each DBSCAN cluster and the furthest point (dist_Maxwithin_i) ###
            new_data_dk['dist_btw_mean'] = new_data_dk.apply(lambda x: distance(x,'longitude_d1','latitude_d1','longitude_d2','latitude_d2'),axis=1)
            new_data_dk['dist_btw_mean'] = new_data_dk['dist_btw_mean']/1000
    
            new_data_dk['dist_dbscan_singleLink'] = new_data_dk.apply(lambda x: dist_dbscan_singleLink(x,'MaxWithinDistance_km_d1','MaxWithinDistance_km_d2','dist_btw_mean'), axis = 1)

            new_data_dk.drop(['longitude_d1','latitude_d1','MaxWithinDistance_km_d1',
                                  'longitude_d2','latitude_d2','MaxWithinDistance_km_d2','dist_btw_mean'],axis = 1, inplace = True)
    
            kmean_lst.append(new_data_dk)
            pruined_dk_2 = pd.concat(kmean_lst)
            pruined_dk_2.reset_index(inplace=True)
                
            ### Grouping DBSCAN clusters to merge ###
            ### Threshold to merge is ep (km) ###
            pruined_dk_2['index_d1'] = pruined_dk_2['cluster_labelkmean_d1'].astype(str) + ' - ' + pruined_dk_2['cluster_label_dbscan_d1'].astype(str)
            pruined_dk_2['index_d2'] = pruined_dk_2['cluster_labelkmean_d2'].astype(str) + ' - ' + pruined_dk_2['cluster_label_dbscan_d2'].astype(str)
            pruined_dk_2 = pruined_dk_2[['index_d1','index_d2']]
            
            ### Group based on reachability ###
            out = group_reachability(pruined_dk_2)
            
            ### Group based on reachability 2 ###
            res2 = group_reachability_label(out)
            
            ### Map group to the original data ###
            df_all['kmean_dbscan_label'] = df_all['cluster_labelkmean'].astype(str) + ' - ' + df_all['cluster_label_dbscan'].astype(str)
            df_all['cluster_label'] = df_all.apply(lambda x: search_label_group(x,'kmean_dbscan_label',res2),axis = 1)
            df_all['cluster_label'] = df_all['cluster_label'].fillna('-1')
            #df_all['cluster_label'] = pd.to_numeric(df_all['cluster_label'],downcast='integer')
            df_all.drop(['cluster_labelkmean','cluster_label_dbscan','kmean_dbscan_label'], axis = 1,inplace = True)
            
        
        else:
            #######
            ### Step 2 (mergeing borders): Investigate if clusters of DBSCAN in 2 different K-means group where they have the distance less than "ep" can be merged ###
            #######
            
            ## Use the same idea from step 1, but this time focus on DBSCAN in each group of unique_merge_index ##
            
            mean_lst_total = []
            
            for i in unique_merge_index:
                first_ind = i[0]
                second_ind = i[1]
            
                  ## From the likely merging groups of K-means, get DBSCAN of each group ##
                  ## First index of DBSCAN ##
                mean_lst_d1 = []
                d1 = df_all.loc[df_all['cluster_labelkmean'] == first_ind]
                d1_lst_dbscan = d1['cluster_label_dbscan'].unique().tolist()
                for j in d1_lst_dbscan:
                    d1_dbscan = d1.loc[d1['cluster_label_dbscan'] == j]
            
                    ## Get the furtherest locations (Max-Min) of each DBSCAN group ##
                    d1_latMax = d1_dbscan.groupby('cluster_label_dbscan')['latitude'].max().to_frame()
                    d1_latMin = d1_dbscan.groupby('cluster_label_dbscan')['latitude'].min().to_frame()
            
                    d1_lonMax = d1_dbscan.groupby('cluster_label_dbscan')['longitude'].max().to_frame()
                    d1_lonMin = d1_dbscan.groupby('cluster_label_dbscan')['longitude'].min().to_frame()
                    d1_MaxLoc = d1_lonMax.merge(d1_latMax,on=['cluster_label_dbscan'])
            
                    ## Calculate Mean location of each DBSCAN group ##
                    d1_latMean = d1_dbscan.groupby('cluster_label_dbscan')['latitude'].mean().to_frame().reset_index()
                    d1_lonMean = d1_dbscan.groupby('cluster_label_dbscan')['longitude'].mean().to_frame().reset_index()
                    d1_MeanLoc = d1_lonMean.merge(d1_latMean,on=['cluster_label_dbscan'])
            
                    ## Merge Mean, Min and Max location ##
                    d1_MeanLoc = d1_MeanLoc.merge(d1_MaxLoc,on=['cluster_label_dbscan'],suffixes=['','_max'])
                    d1_MeanLoc = d1_MeanLoc.merge(d1_lonMin,on=['cluster_label_dbscan'],suffixes=['','_min'])
                    d1_MeanLoc = d1_MeanLoc.merge(d1_latMin,on=['cluster_label_dbscan'],suffixes=['','_min'])
                    d1_MeanLoc['cluster_labelkmean'] = first_ind
            
                    ## Calculate distance between mean point and furtherest point ##
                    d1_MeanLoc['distanceWithin_mean_Max_m'] = d1_MeanLoc.apply(lambda x: distance(x,'longitude','latitude','longitude_max','latitude_max'),axis=1)
                    d1_MeanLoc['distanceWithin_mean_Min_m'] = d1_MeanLoc.apply(lambda x: distance(x,'longitude','latitude','longitude_min','latitude_min'),axis=1)
                    ## Get the max distance between mean point and furtherest point ##
                    d1_MeanLoc['MaxWithinDistance_m'] = d1_MeanLoc.apply(lambda x: get_max_distance(x,'distanceWithin_mean_Max_m','distanceWithin_mean_Min_m'),axis = 1)
                    ### Convert to km ###
                    d1_MeanLoc['MaxWithinDistance_km'] = d1_MeanLoc['MaxWithinDistance_m']/1000
                    d1_MeanLoc.drop(['longitude_max','latitude_max','longitude_min','latitude_min',
                                      'distanceWithin_mean_Max_m','distanceWithin_mean_Min_m','MaxWithinDistance_m'],axis=1,inplace=True)
                    mean_lst_d1.append(d1_MeanLoc)
                    mean_all_d1 = pd.concat(mean_lst_d1)
                    mean_all_d1.reset_index(inplace=True)
            
            
                  ## Second index of DBSCAN ##
                mean_lst_d2 = []
                d2 = df_all.loc[df_all['cluster_labelkmean'] == second_ind]
                d2_lst_dbscan = d2['cluster_label_dbscan'].unique().tolist()
                for m in d2_lst_dbscan:
                    d2_dbscan = d2.loc[d2['cluster_label_dbscan'] == m]
            
                    ## Get the furtherest locations (Max-Min) of each DBSCAN group ##
                    d2_latMax = d2_dbscan.groupby('cluster_label_dbscan')['latitude'].max().to_frame()
                    d2_latMin = d2_dbscan.groupby('cluster_label_dbscan')['latitude'].min().to_frame()
            
                    d2_lonMax = d2_dbscan.groupby('cluster_label_dbscan')['longitude'].max().to_frame()
                    d2_lonMin = d2_dbscan.groupby('cluster_label_dbscan')['longitude'].min().to_frame()
                    d2_MaxLoc = d2_lonMax.merge(d2_latMax,on=['cluster_label_dbscan'])
            
                    ## Calculate Mean location of each DBSCAN group ##
                    d2_latMean = d2_dbscan.groupby('cluster_label_dbscan')['latitude'].mean().to_frame().reset_index()
                    d2_lonMean = d2_dbscan.groupby('cluster_label_dbscan')['longitude'].mean().to_frame().reset_index()
                    d2_MeanLoc = d2_lonMean.merge(d2_latMean,on=['cluster_label_dbscan'])
            
                    ## Merge Mean, Min and Max location ##
                    d2_MeanLoc = d2_MeanLoc.merge(d2_MaxLoc,on=['cluster_label_dbscan'],suffixes=['','_max'])
                    d2_MeanLoc = d2_MeanLoc.merge(d2_lonMin,on=['cluster_label_dbscan'],suffixes=['','_min'])
                    d2_MeanLoc = d2_MeanLoc.merge(d2_latMin,on=['cluster_label_dbscan'],suffixes=['','_min'])
                    d2_MeanLoc['cluster_labelkmean'] = second_ind
            
                    ## Calculate distance between mean point and furtherest point ##
                    d2_MeanLoc['distanceWithin_mean_Max_m'] = d2_MeanLoc.apply(lambda x: distance(x,'longitude','latitude','longitude_max','latitude_max'),axis=1)
                    d2_MeanLoc['distanceWithin_mean_Min_m'] = d2_MeanLoc.apply(lambda x: distance(x,'longitude','latitude','longitude_min','latitude_min'),axis=1)
                    ## Get the max distance between mean point and furtherest point ##
                    d2_MeanLoc['MaxWithinDistance_m'] = d2_MeanLoc.apply(lambda x: get_max_distance(x,'distanceWithin_mean_Max_m','distanceWithin_mean_Min_m'),axis = 1)
                    ### Convert to km ###
                    d2_MeanLoc['MaxWithinDistance_km'] = d2_MeanLoc['MaxWithinDistance_m']/1000
                    d2_MeanLoc.drop(['longitude_max','latitude_max','longitude_min','latitude_min',
                                     'distanceWithin_mean_Max_m','distanceWithin_mean_Min_m','MaxWithinDistance_m'],axis=1,inplace=True)
                    mean_lst_d2.append(d2_MeanLoc)
                    mean_all_d2 = pd.concat(mean_lst_d2)
                    mean_all_d2.reset_index(inplace=True)
            
                  ## Merge to get all data (Cartician product style) ##
                new_data = mean_all_d1.merge(mean_all_d2, how = "cross", suffixes=['_d1','_d2'])
                mean_lst_total.append(new_data)
            
            
            mean_all_total = pd.concat(mean_lst_total)
            mean_all_total.reset_index(inplace=True)
            mean_all_total.drop(['index','index_d1','index_d2'],axis=1, inplace=True)
        
        
            ### Calculate distance between DBSCAN clusters (dist_D_ij) from different K-means groups ###
            ### Distance between mean of each DBSCAN cluster and the furthest point (dist_Maxwithin_i) ###
            mean_all_total['dist_btw_mean'] = mean_all_total.apply(lambda x: distance(x,'longitude_d1','latitude_d1','longitude_d2','latitude_d2'),axis=1)
            mean_all_total['dist_btw_mean'] = mean_all_total['dist_btw_mean']/1000
        
        
            ### dist_D_ij = dist_meanD_ij - (dist_Maxwithin_i + dist_Maxwithin_j) ###
            mean_all_total['dist_dbscan_singleLink'] = mean_all_total.apply(lambda x: dist_dbscan_singleLink(x,'MaxWithinDistance_km_d1',
                                                                                                             'MaxWithinDistance_km_d2',
                                                                                                             'dist_btw_mean'), axis = 1)
            
            mean_all_total.drop(['longitude_d1','latitude_d1','MaxWithinDistance_km_d1',
                                 'longitude_d2','latitude_d2','MaxWithinDistance_km_d2','dist_btw_mean'],axis = 1, inplace = True)
        
        
            ### Threshold to merge is ep (km) ###
            mean_all_total = mean_all_total.loc[mean_all_total['dist_dbscan_singleLink'] <= ep]
            mean_all_total.reset_index(inplace=True)
            mean_all_total
        
        
            ### Grouping DBSCAN clusters to merge ###
            ### Threshold to merge is ep (km) ###
            mean_all_total['index_d1'] = mean_all_total['cluster_labelkmean_d1'].astype(str) + ' - ' + mean_all_total['cluster_label_dbscan_d1'].astype(str)
            mean_all_total['index_d2'] = mean_all_total['cluster_labelkmean_d2'].astype(str) + ' - ' + mean_all_total['cluster_label_dbscan_d2'].astype(str)
            mean_all_total = mean_all_total[['index_d1','index_d2']]
            mean_all_total
        
            ### Group based on reachability ###
            out = group_reachability(mean_all_total)
        
        
            ### Group based on reachability 2 ###
            res = group_reachability_label(out)

        
            ### Map group to the original data ###
            df_all['kmean_dbscan_label'] = df_all['cluster_labelkmean'].astype(str) + ' - ' + df_all['cluster_label_dbscan'].astype(str)
            df_all['cluster_label'] = df_all.apply(lambda x: search_label_group(x,'kmean_dbscan_label',res),axis = 1)
            df_all['cluster_label'] = df_all['cluster_label'].fillna('-1')
            #df_all['cluster_label'] = pd.to_numeric(df_all['cluster_label'],downcast='integer')
            df_all.drop(['cluster_labelkmean','cluster_label_dbscan','kmean_dbscan_label'], axis = 1,inplace = True)
        
    
    return df_all



#### Clustering matrices ####
## Sillihoutte Score ##
def do_silhouette_score(data,col_cluster):
    data = data.loc[data['{}'.format(col_cluster)] != '-1']
    
    data_validate = data[['longitude', 'latitude']]
    data_validate = np.radians(data_validate)
    data_validate_label = data['{}'.format(col_cluster)]
    
    score = 0
    if len(data_validate_label.unique().tolist()) != 1:
        score = silhouette_score(data_validate,data_validate_label)
    else:
        score = score
    
    return score

## Davis-Bouldin Index ##
def do_davies_bouldin_score(data,col_cluster):
    data = data.loc[data['{}'.format(col_cluster)] != '-1']
    
    data_validate = data[['longitude', 'latitude']]
    data_validate = np.radians(data_validate)
    data_validate_label = data['{}'.format(col_cluster)]
    
    score = 0
    if len(data_validate_label.unique().tolist()) != 1:
        score = davies_bouldin_score(data_validate,data_validate_label)
    else:
        score = score
    
    return score

