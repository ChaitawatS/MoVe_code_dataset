# -*- coding: utf-8 -*-
"""
Created on Sat Jul 22 00:08:29 2023

@author: User
"""
import random


class Agent:
    __slots__ = ("id","health_stage","cluster","group","risk","mobility_obj","timer","mobility_threshold","destination")
    #init constructor
    class_counter= 0
    def __init__(self,health_stage,cluster,group,mobility_obj,timer=0):
        self.id= Agent.class_counter
        self.health_stage = health_stage
        self.cluster = cluster
        self.group = group
        self.risk = 0.0
        self.timer = timer
        self.destination = None
        self.mobility_threshold = 0.0
        self.mobility_obj = mobility_obj #path of mobility matrices (files)
        Agent.class_counter+=1
    
    def show_agent_detail(self):
        #---Just to show an individual's detail---#
        return "Individuals from group {} with the expected risk of {}".format(self.group, self.risk)
    


class Cluster:
    __slots__ = ("cluster_number","area_risk","mos_prevalence","population","patient","patient_external","mos_cycle","prob_of_spread_to_human","prob_of_infect_to_mos","extentic_incubation_period","mos_birth_rate","mos_mortal_rate","mos_carry_capacity","mos_s","mos_l","mos_latent","mos_i","biting_rate","constant_sus","constant_inf","known_params")
    
    def __init__(self,cluster_number,prob_of_spread_to_human,prob_of_infect_to_mos,extentic_incubation_period,mos_birth_rate,mos_mortal_rate,mos_carry_capacity,mos_s,mos_l,mos_latent,mos_i,biting_rate,constant_sus,constant_inf,known_params,patient_external):
        self.cluster_number = cluster_number
        self.area_risk = 0.0
        self.mos_prevalence = 0.0
        self.mos_s = mos_s
        self.mos_l = mos_l
        self.mos_latent = 0
        self.mos_i = mos_i
        self.population = 0
        self.patient = 0
        self.patient_external = patient_external
        self.biting_rate = biting_rate
        self.extentic_incubation_period = extentic_incubation_period #10-18 daysrandom.randrange(5,8)
        self.mos_cycle = random.randrange(11,14) #<14days
        self.prob_of_spread_to_human = prob_of_spread_to_human #probility of infecting malaria from mosquitoes to human
        self.prob_of_infect_to_mos = prob_of_infect_to_mos #probility of infecting malaria from human to mosquitoes (flexible)
        self.mos_birth_rate = mos_birth_rate #mosquitoes birth rate (flexible)
        self.mos_mortal_rate = mos_mortal_rate #mosquitoes mortality rate (flexible)
        self.mos_carry_capacity = 50000 #mosquitoes capacity of the area
        self.known_params = known_params
        self.constant_sus = constant_sus
        self.constant_inf = constant_inf
        #--------Seasonal effect?
    
    def show_cluster_detail(self):
        #---Just to show each cluster's detail---#
        return "Cluster number: {}, known parameter?: {}, suscept mos: {}, infected mos: {}, probability of transmitting disease to human: {}, probability of transmitting disease to mosquito:{}, biting rate:{}".format(self.cluster_number,self.known_params,self.mos_s,self.mos_i,self.prob_of_spread_to_human,self.prob_of_infect_to_mos,self.biting_rate)

