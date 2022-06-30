import math
from datetime import datetime
import openpyxl as opxl
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import model as ty

import os

# Create par

def create_inputs():
    ## Meteo inputs for tests

    # Simulations with different meteos

    G_list = [966]
    #G_list = [0]
    #G_list = [1000,1000]
    coeff_G_p_list = [0]
    #G_p_list = [0]
    u_list = [0,0.7,1.4,2.7]
    #u_list = [0]
    T_amb_list = [265,270,275,280,285,290,295,300,305]
    #T_amb_list = [280,300]

    #compt = 2

    T_f_in_list = [263,268,273,278,283,288,293,298,303,308,313,318,323]

    T_guess_list = [293]

    # TUV
    path = os.getcwd()
    cond = r'\220321_TUV_test_conditions.xlsx'
    fichier = path+cond
    condi = pd.read_excel(fichier,"Non insulated v4 TUV")
    condi.drop(index=condi.index[0], 
        axis=0, 
        inplace=True)

    return G_list,coeff_G_p_list,u_list,T_amb_list,T_f_in_list,T_guess_list,condi

def create_out():
    path = os.getcwd()
    pathout = path+'\\Outputs'
    exist = os.path.exists(pathout)

    if exist == False:
        os.makedirs(pathout)

    wbo = opxl.Workbook()
    return wbo

def create_par():
    par = {}

    ## Physics constants

    par["sigma"] = 1 # Stefan-Boltzmann constant

    ## PV

    par["eta_nom"] = 1 # nominal efficiency of PV panel

    par["Eff_T"] = 1
    par["T_ref"] = 25 # reference temperature, often 25°C

    par["Eff_G"] = 1
    par["G_ref"] = 1000 # reference irradiance, often 1000 W/m2

    #par["X_rad"] = 1
    par["X_corr"] = 1 

    ## Heat exchanger specs

    par["tube_conv"] = 1

    par["L_pan"] = 1
    par["w_pan"] = 1
    par["L_abs"] = 1
    par["w_abs"] = 1

    par["W"] = 1 # the width (x-direction) between adjacent fluid tubes
    par["Dext_tube"] = 1
    par["D_tube"] = 1 #
    par["l_c"] = 1
    par["l_B"] = 1
    par["L_af"] = 1  
    par["iota"] = 1
    par["N_meander"] = 1
    par["N_harp"] = 1 # number of identical tubes carrying fluid through the collector
    par["N_harp_actual"] = 1 # actual numer of identical tubes in parallel (harp geometry)
    par["L_riser"] = 1 # the length of the collector along the flow direction = L_riser in Excel

    par["D"] = 1

    par["insulated"] = 1

    ## Additionnal fins = ailettes

    par["ailette"] = 1

    par["geometry"] = 1

    par["fin_0"] = 1
    par["N_f0"] = 1
    par["L_f0"] = 1
    par["delta_f0"] = 1

    par["fin_1"] = 1
    par["N_f1"] = 1
    par["L_f1"] = 1
    par["delta_f1"] = 1
    par["delta_f1_int"] = 1
    par["coeff_f1"] = 1

    par["fin_2"] = 1
    par["N_f2"] = 1
    par["L_f2"] = 1
    par["delta_f2"] = 1

    par["fin_3"] = 1
    par["N_f3"] = 1
    par["L_f3"] = 1
    par["delta_f3"] = 1

    par["Heta"] = 1

    par["N_ail"] = 1
    par["DELTA_a"] = 1

    ## Thermal / radiance

    par["tau_alpha"] = 1 # transmittance-absorptance product for the solar collector
    par["eps"] = 1 # emissivity of the top surface of the collector (PV surface)

    # Geometry and thermal conductivities

    par["k_air"] = 1
    par["air_layer"] = 1

    par["k_abs"] = 1 # thermal conductivity of the plate material
    par["lambd_abs"] = 1 # thickness of the absorber plate

    par["lambd_riser"] = 1
    par["k_riser"] = 1

    par["k_ail"] = 1 # thermal conductivity of the fin
    par["lambd_ail"] = 1 # thickness of the fin

    par["k_insulation"] = 1
    par["e_insulation"] = 1

    par["h_top"] = 1
    par["a_htop"] = 1
    par["b_htop"] = 1 
    par["coeff_h_top"] = 1
    par["coeff_h_back"] = 1

    par["h_inner"] = 1

    # Ci-dessous les résistances du panneau sont calculées directement dans le fichier Inputs.xlsx

    par["R_TOP"] = 1 # instead of 1/h_outer in the document
    par["R_INTER"] = 1 # = R_1 = R_INTER = resistance to heat transfer from the PV cells to the absorber plate
    par["R_2"] = 1

    par["C_B"] = 1 # the conductance between the absorber plate and the bonded tube

    ## Initialisation d'une météo

    par["G_T0"] = 1 # total solar radiation (beam + diffuse) incident upon the collector surface = POA irradiance
    par["G_p"] = 1 # infra-red 
    par["coeff_G_p"] = 1
    par["T_sky"] = 1 # sky temperature for long-wave radiation calculations
    par["T_amb"] = 1 
    par["T_back"] = 1
    par["u"] = 1 # wind speed

    ## Fluid

    par["T_fluid_in0"] = 1
    par["C_p"] = 1 # specific heat of the fluid flowing through the PV/T collector
    par["m_dot"] = 1 # flow rate of fluid through the solar collector

    par["k_fluid"] = 1
    par["rho_fluid"] = 1
    par["mu_fluid"] = 1

    ## Installation

    par["theta"] = 1 # angle of incidence

    ## Type de test

    par["test"] = 1

    # Excel parameters

    list_parameters = []
    *list_parameters, = par

    print(list_parameters)

    path = os.getcwd()
    print(path)

    inp = r'\Inputs.xlsm'
    fichier_i = path+inp
    wbi = opxl.load_workbook(fichier_i,data_only=True)
    sheet_i = wbi["Main"]

    # Find parameters in Excel file Inputs.xlsx

    for i in range(len(list_parameters)):
        nom_var = list_parameters[i]
        cell = ty.find_cell_by_name(wbi,nom_var)
        valeur = sheet_i[cell].value
        
        par[nom_var]=valeur

    wbi.close()

    ### Computation of some parameters from inputs

    # Calculate A_G
    par["A_G"] = par["L_pan"]*par["w_pan"]

    # Calculate delta : demi-intervalle entre deux risers (extérieur à extérieur)
    # utilisé dans gamma_2_int et Q_abs_back
    par["delta"] = (par["W"]-par["Dext_tube"])/2
    # Calculate X_rad which depends on G_T0
    ty.X_rad(par)

    # Calculate the conductance between the absorber and the fluid through any riser
    ty.C_B(par)

    # Calculate h_fluid
    ty.h_fluid(par)

    # Add "longueur"
    par["longueur"] = par["L_abs"]

    return par

# Pre-processing and processing functions for parametric studies

def pre_proc(test):
    if test == "air_layer" or test == "air_layer_TUV":
        return np.linspace(0,0.005,20)
    elif test == "T_guess":
        return np.linspace(280,300,11)
    elif test == "L_f2" or test == "L_f2_TUV":
        return np.linspace(0,0.5,30)
    elif test == "coeff_h_top_TUV":
        return [0.9,1,1.05,1.1,1.15,1.2]
    elif test == "coeff_h_back_TUV":
        return np.linspace(1,2,21)
    elif test == "N_riser":
        return [3,6,9,12,15,18,21,24,30,40,50,60,80,100,120,140,160,180]
    elif test == "N_fins_per_EP":
        return [6,7,8,10,11,12,13,14,15,16,18,20,22]
    elif test == "coeff_h_top":
        return np.linspace(0.001,1,20)
    elif test == "b_htop":
        return np.linspace(1,5,6)
    elif test == "parametric_insulation":
        return np.linspace(0,0.1,21)
    elif test == "iota":
        return [0.,0.02,0.05,0.08,0.1,0.2,0.5,1]
    elif test == "D_tube":
        return [0.001,0.002,0.004,0.008,0.01,0.012,0.02,0.05]
    elif test == "k_riser":
        return [1,50,100,150,200,250,300,350,400]
    elif test == "L_f2":
        return np.linspace(0,0.6,10)
    elif test == "absorber":
        return [4,50,100,150,200,250,300,400]
    elif test == "e_abs":
        return np.linspace(0.00001,0.002,10)
    elif test == "a_htop_TUV":
        return [0.5,1,1.5,2,3,4,5,6,7,8,9,10]
    elif test == "N_f1_TUV":
        return [15,20,25,30,35,40,45,50,55,60,65,70,75,80,90,100,120,150]
    else:
        return []


def proc(par,test,i,test_list):
    if test == "air_layer" or test == "air_layer_TUV":
        ty.change_air_layer(par,test_list[i])
    elif test == "T_guess":
        T_guess_list = [test_list[i]]
    elif test == "L_f2" or test =="L_f2_TUV":
        par["L_f2"] = test_list[i]
    elif test == "coeff_h_top_TUV":
        par["coeff_h_top"] = test_list[i]
    elif test == "coeff_h_back_TUV":
        par["coeff_h_back"] = test_list[i]
    elif test == "N_riser":
        if par["geometry"]=="meander":
            par["N_meander"]=test_list[i]
            par["W"]=par["L_abs"]/test_list[i]
        elif par["geometry"] == "harp":
            par["N_harp"]=test_list[i]
            par["N_harp_actual"]=test_list[i]
            par["W"]=par["w_abs"]/test_list[i]

        par["l_i"]=par["W"]
        par["delta"] = (par["W"]-par["D_tube"])/2
        par["L_af"]=(par["W"]-par["l_B"])/2
    elif test == "N_fins_per_EP":
        ty.change_N_fins_per_EP(par,test_list[i])
    elif test == "coeff_h_top":
        par["coeff_h_top"] = test_list[i]
    elif test == "b_htop":
        ty.change_b_htop(par,test_list[i])
    elif test == "parametric_insulation":
        ty.change_ins(par,test_list[i])
    elif test == "iota":
        par["iota"] = test_list[i]
    elif test == "D_tube":
        par["D_tube"] = test_list[i]
        par["iota"] = test_list[i]
        ty.h_fluid(par)
    elif test == "k_riser":
        par["k_riser"] = test_list[i]
        ty.C_B(par)
    elif test == "L_f2":
        par["L_f2"] = test_list[i]
    elif test == "absorber":
        par["k_abs"]=test_list[i]
    elif test == "e_abs":
        par["lambd_abs"]=test_list[i]
    elif test == "a_htop_TUV":
        par["a_htop"] = test_list[i]
    elif test == "N_f1_TUV":
        par["N_f1"] = test_list[i]
        par["N_ail"] = test_list[i]
    else:
        pass