import math
import copy
import pandas as pd
import numpy as np
import heat_transfer as bht
import ht


# %run C:\Users\BU05\Documents\Modele1D_Type560\Type560.py

# Parameters

# "sigma", "eta_nom","Eff_T","T_ref","Eff_G","G_ref","X_rad","X_corr","W","D_tube","N_harp",
# "L_riser","tau_alpha","eps","k_abs","lambd_abs","h_fluid","R_TOP","R_INTER","R_B","C_B","G",
# "Gp","T_sky","T_amb","T_back","T_fluid_in0","C_p","m_dot","theta"

# Function for Excel
# Search a cell by its nom_variable and return a string like "B3"
def find_cell_by_name(wb,nom_variable):
    my_range = wb.defined_names[nom_variable]
    ch = my_range.value
    ch2 = ch.split("!")[1]
    ch3 = ch2.replace("$","")
    return ch3
    
# Does not depend on T_PV
def X_rad(parameters):
    Eff_G = parameters["Eff_G"]
    G_ref = parameters["G_ref"]
    G_T = parameters["G"]

    X = 1+Eff_G*(G_T-G_ref)
    parameters["X_rad"]=X

## Relationship between wind and R_TOP
# Modify the dictionary par by updating the wind speed
# To complete from Excel file
def change_u(par,wind_speed):
    par["u"] = wind_speed
    
    a_w = par["a_htop"]
    b_w = par["b_htop"]

    new_h_wind = a_w*wind_speed+b_w

    par["h_top"]=new_h_wind
    par["R_T"]= par["R_TOP"] + 1/par["h_top"]

# return tanh or 1/tanh
def tanh_or_inverse(arg):
    return math.tanh(arg)

def h_fluid(parameters):
    D_tube = parameters["D_tube"]
    m_dot = parameters["m_dot"]
    N_harp_actual = parameters["N_harp_actual"]

    k_fluid = parameters["k_fluid"]
    rho_fluid = parameters["rho_fluid"]
    mu_fluid = parameters["mu_fluid"]

    flow_rate_per_riser = (m_dot/N_harp_actual)/rho_fluid # en m3/s
    tube_section = math.pi*(D_tube/2)**2

    fluid_speed = flow_rate_per_riser/tube_section

    Re = (rho_fluid*fluid_speed*D_tube)/mu_fluid

    Pr_fluid = 7.

    if Re<2000:
        Nu_fluid = 0.7*0.023*(Re**0.8)*(Pr_fluid**0.4)
    else:
        Nu_fluid = 0.023*(Re**0.8)*(Pr_fluid**0.4)

    parameters["h_fluid"] = (k_fluid/D_tube)*Nu_fluid

def C_B(parameters):
    lambd_riser_plate = parameters["lambd_riser_plate"]
    l_c = parameters["l_c"]
    k_riser = parameters["k_riser"]

    parameters["C_B"] = (l_c*k_riser)/lambd_riser_plate

def h_top(parameters,var):
    T_PV = var["T_PV"]
    T_amb = parameters["T_amb"]

    h_free = parameters["coeff_h_top_free"]*bht.top_h_simple(T_PV,T_amb,parameters["theta"],parameters["L_abs"])

    if parameters["orientation"]=="portrait":
        longueur = parameters["L_pan"]
    else:
        longueur = parameters["w_pan"]

    h_forced = parameters["coeff_h_top_forced"]*bht.h_top_forced(T_PV,T_amb,parameters["u"],longueur)

    parameters["h_top"] = (h_free**3 + h_forced**3)**(1/3)


def h_back(parameters,var):
    if var["T_abs_mean"]==None:
        print('T_abs_mean = None in h_back()')
        return 3.
    elif parameters["fin_0"] >= 1 or parameters["fin_1"] >= 1 or parameters["fin_2"] >= 1:
        if parameters["geometry"]=="harp":
            D_4 = parameters["D"]
            parameters["h_back"] = parameters["coeff_h_back"]*bht.back_h_fins(var["T_abs_mean"],parameters["T_back"],parameters["theta"],parameters["longueur"],D_4,parameters["Heta"])

        else:
            D = parameters["D"]
            parameters["h_back"] = parameters["coeff_h_back"]*bht.back_h_fins(var["T_abs_mean"],parameters["T_back"],parameters["theta"],parameters["longueur"],D,parameters["Heta"])
    else:
        # theta est l'inclinaison du panneau par rapport à l'horizontale
        T_ref = var["T_abs_mean"]
        if parameters["insulated"] == 1:
            R_2 = parameters["R_2"]
            h_back = parameters["h_back"]
            # T_back = parameters["T_back"]

            T_ref = T_ref + (R_2/(R_2+1/h_back))

        res = parameters["coeff_h_back"]*bht.back_h_simple(T_ref,parameters["T_back"],parameters["theta"],parameters["longueur"])

        if res == None:
            print('res = None in h_back()')
            print('longueur',parameters["longueur"])
            print('T_abs',var["T_abs_mean"])
            print('theta',parameters["theta"])
            print('T_back',parameters["T_back"])
            print('h_back_calculated',res)

        parameters["h_back"] = res

# que pour les géométries avec ailettes (non isolées)
def h_back_mean(parameters,var):
    if parameters["geometry"] == "harp":
        D_4 = parameters["D"]
        old_h_back = parameters["h_back"]
        new_h_back = parameters["coeff_h_back"]*bht.back_h_fins(var["T_abs_mean"],parameters["T_back"],parameters["theta"],parameters["longueur"],D_4,parameters["Heta"])
        if abs(new_h_back - old_h_back) > 0.1:
            parameters["h_back"] = (old_h_back+new_h_back)/2
        else:
            pass

    else:
        D = parameters["D"]
        old_h_back = parameters["h_back"]
        if parameters["N_ail"]<= 24:
            new_h_back = parameters["coeff_h_back"]*bht.back_h_simple(var["T_abs_mean"],parameters["T_back"],parameters["theta"],parameters["longueur"])
        else:
            new_h_back = parameters["coeff_h_back"]*bht.back_h_fins(var["T_abs_mean"],parameters["T_back"],parameters["theta"],parameters["longueur"],D,parameters["Heta"])
        if abs(new_h_back - old_h_back) > 0.1:
            parameters["h_back"] = (old_h_back+new_h_back)/2
        else:
            pass

    # parameters["h_back"] = 3. # test sur l'influence du h_back

def h_rad_back(parameters, var):

    eps = parameters["eps_he"]
    sigma = parameters["sigma"]
    T_back = parameters["T_amb"] # hypothèse T_amb = T_back

    T_abs_mean = var["T_abs_mean"]

    h = eps*sigma*(T_abs_mean+T_back)*(T_abs_mean**2+T_back**2)
    parameters["h_rad_back"]=h


# Pour les ailettes, on ne prend pas en compte la composante radiative h_rad_back

def Biot(lambd,k,h,delta):
    return ((lambd*h)/k)*(1+lambd/delta)

def Bi_f0(parameters):
    parameters["Bi_f0"] = Biot(parameters["lambd_ail"],parameters["k_ail"],parameters["h_back"],parameters["delta_f0"])

def Bi_f1(parameters):
    parameters["Bi_f1"] = Biot(parameters["lambd_ail"],parameters["k_ail"],parameters["h_back"],parameters["delta_f1"])

def Bi_f2(parameters):
    parameters["Bi_f1"] = Biot(parameters["lambd_ail"],parameters["k_ail"],parameters["h_back"],parameters["delta_f2"])

def Bi_f3(parameters):
    parameters["Bi_f3"] = Biot(parameters["lambd_ail"],parameters["k_ail"],parameters["h_back"],parameters["delta_f3"])

##### Variables

## PV production

# Radiation heat transfer coefficient using equation 560.3
def h_rad(parameters, var):
    
    eps = parameters["eps"]
    sigma = parameters["sigma"]
    T_sky = parameters["T_sky"]

    T_PV = var["T_PV"]

    h = eps*sigma*(T_PV+T_sky)*(T_PV**2+T_sky**2)
    var["h_rad"]=h
    #var["h_rad"]=0.00001

# Depends on T_PV
def X_celltemp(parameters,var):
    Eff_T = parameters["Eff_T"]
    T_ref = parameters["T_ref"]


    T_PV = var["T_PV"]

    X = 1+Eff_T*(T_PV-T_ref)

    var["X_celltemp"]=X

def eta_PV(parameters, var):
    
    eta_nom = parameters["eta_nom"]
    G = parameters["G"]
    X_rad = parameters["X_rad"]
    X_corr = parameters["X_corr"]

    #T_PV = var["T_PV"]
    X_celltemp = var["X_celltemp"]

    eta = eta_nom*X_celltemp*X_rad*X_corr
    var["eta_PV"] = eta
    #var["eta_PV"] = 0.15


# net absorbed solar radiation (total absorbed - PV power production)
def S(parameters, var):
    tau_alpha = parameters["tau_alpha"]
    G = parameters["G"]

    #T_PV = var["T_PV"]
    eta_PV = var["eta_PV"]

    S = tau_alpha*G*(1-eta_PV)

    var["S"] = S

def Fp(parameters, var):
    R_INTER = parameters["R_INTER"]
    R_T = parameters["R_TOP"]+1/parameters["h_top"]

    #T_PV = var["T_PV"]
    h_rad = var["h_rad"]

    Fp = 1/(h_rad*R_INTER+R_INTER/R_T+1)
    var["Fp"] = Fp

# Vrai gamma
def gamma(parameters):
    alpha = parameters["alpha_ail"]
    beta = parameters["beta_ail"]
    a = parameters["lambd_ail"]
    L_a = parameters["Heta"]

    arg = (alpha*L_a)/a
    numerateur = (alpha/a)*math.sinh(arg) + ((beta*alpha)/a)*math.cosh(arg)
    denominateur = math.cosh(arg) + beta*math.sinh(arg)

    gamma = (numerateur/denominateur)
    parameters["gamma"] = gamma

def gamma_0_int(parameters):

    Bi = parameters["Bi_f0"]
    a = parameters["lambd_ail"]
    delta = parameters["delta_f0"]

    alpha = math.sqrt(2*Bi)
    beta = math.sqrt(Bi/2)*(1/(1+a/delta))

    L_a = parameters["L_f0"]
    N_ail = parameters["N_f0"]
    k = parameters["k_ail"]

    L_riser = parameters["L_riser"]

    arg = (alpha*L_a)/a
    numerateur = (alpha/a)*math.sinh(arg) + ((beta*alpha)/a)*math.cosh(arg)
    denominateur = math.cosh(arg) + beta*math.sinh(arg)

    delta = parameters["delta_f0"]

    gamma = k*(numerateur/denominateur)*((a*N_ail*delta)/L_riser)

    parameters["gamma_0_int"] = gamma

def gamma_1_int(parameters):

    k = parameters["k_ail"]
    Bi = parameters["Bi_f1"]
    L_a = parameters["L_f1"]
    a = parameters["lambd_ail"]
    delta = parameters["delta_f1_int"]
    N_ail = parameters["N_f1"]

    L_riser = parameters["L_riser"]

    gamma = 2*k*((a*N_ail*delta)/L_riser)*math.tanh(math.sqrt(2*Bi)*(L_a/a))*(math.sqrt(2*Bi)/a)

    parameters["gamma_1_int"] = parameters["coeff_f1"]*gamma

def gamma_2_int(parameters):

    Bi = parameters["Bi_f2"]
    a = parameters["lambd_ail"]
    delta = parameters["delta_f2"]

    alpha = math.sqrt(2*Bi)
    beta = math.sqrt(Bi/2)*(1/(1+a/delta))

    L_a = parameters["L_f2"]
    N_ail = parameters["N_f2"]
    k = parameters["k_ail"]

    L_riser = parameters["L_riser"]

    arg = (alpha*L_a)/a
    numerateur = (alpha/a)*math.sinh(arg) + ((beta*alpha)/a)*math.cosh(arg)
    denominateur = math.cosh(arg) + beta*math.sinh(arg)

    delta_f2 = parameters["delta_f2"]
    delta = parameters["delta"]
    
    gamma_int = k*(numerateur/denominateur)*((a*N_ail*delta_f2)/(L_riser*delta))

    parameters["gamma_2_int"] = gamma_int

def j(parameters,var):
    R_INTER = parameters["R_INTER"]
    R_B = parameters["R_2"] + 1/(parameters["h_back"]+parameters["h_rad_back"])

    Fprime = var["Fp"]
    
    j = 1/(R_INTER*Fprime)+1/(R_B*Fprime)-1/R_INTER

    if parameters["fin_2"] == 1:

        gamma_int = parameters["gamma_2_int"]

        j += (gamma_int)/Fprime

    var["j"] = j

def b(parameters, var):
    T_sky = parameters["T_sky"]
    T_amb = parameters["T_amb"]
    R_T = parameters["R_TOP"]+1/parameters["h_top"]
    T_back = parameters["T_back"]
    R_B = parameters["R_2"] + 1/(parameters["h_back"]+parameters["h_rad_back"])

    h_rad = var["h_rad"]
    S = var["S"]
    Fprime = var["Fp"]

    b = S+h_rad*T_sky+T_amb/R_T+T_back/(R_B*Fprime)

    if parameters["fin_2"]==1:
        gamma_int = parameters["gamma_2_int"]

        b += (gamma_int*T_back)/Fprime

    var["b"] = b

def m(parameters, var):
    lambd_abs = parameters["lambd_abs"]
    k_abs = parameters["k_abs"]

    Fprime = var["Fp"]

    j = var["j"]

    m = math.sqrt((Fprime*j)/(k_abs*lambd_abs))

    var["m"] = m   

# Need the absorber's fin base temperature T_B - function not used
def qp_fin(parameters, var):
    lambd_abs = parameters["lambd_abs"]
    k_abs = parameters["k_abs"]

    L_af = parameters["L_af"]

    #T_PV = var["T_PV"]
    T_B = var["T_Base_mean"]

    j = var["j"]
    b = var["b"]

    m = var["m"]
    
    q = k_abs*lambd_abs*m*((b/j)-T_B)*tanh_or_inverse(m*L_af)
    var["qp_fin"] = q

def KTE(parameters, var):
    lambd_abs = parameters["lambd_abs"]
    k_abs = parameters["k_abs"]
    W = parameters["W"]
    L_af = parameters["L_af"]
    D_tube = parameters["D_tube"]
    l_B = parameters["l_B"]
    l_c = parameters["l_c"]
    p_int_tube = parameters["p_int_tube"]
    p_ext_tube = parameters["p_ext_tube"]

    R_INTER = parameters["R_INTER"]
    R_T = parameters["R_TOP"]+1/parameters["h_top"]
    R_B = parameters["R_2"] + 1/(parameters["h_back"]+parameters["h_rad_back"])
    h_fluid = parameters["h_fluid"]

    T_sky = parameters["T_sky"]
    T_amb = parameters["T_amb"]
    T_back = parameters["T_back"]

    C_B = parameters["C_B"]

    #T_PV = var["T_PV"]
    h_rad = var["h_rad"]
    S = var["S"]
    Fprime = var["Fp"]

    j = var["j"]
    b = var["b"]
    m = var["m"] 
    
    iota = parameters["iota"]

    #print(var)

    chi = 1/(h_fluid*p_int_tube)+1/C_B

    K = -D_tube*Fprime*((l_c/D_tube)*(h_rad+1/R_T)+(iota/D_tube)/(R_B*Fprime))-2*k_abs*lambd_abs*m*tanh_or_inverse(m*L_af)
    T = 1+D_tube*Fprime*chi*((l_c/D_tube)*(h_rad+1/R_T)+(iota/D_tube)/(R_B*Fprime))+2*k_abs*lambd_abs*m*tanh_or_inverse(m*L_af)*chi
    E = D_tube*Fprime*((l_c/D_tube)*(S+h_rad*T_sky+T_amb/R_T)+((iota/D_tube)*T_back)/(R_B*Fprime))+2*k_abs*lambd_abs*m*tanh_or_inverse(m*L_af)*(b/j)

    if parameters["fin_3"]==1:

        # Fins
        a = parameters["lambd_ail"]
        N = parameters["N_f3"]

        L_riser = parameters["L_riser"]
        Bi = parameters["Bi_f3"]
        L_vf = parameters["L_f3"]
        k_ail = parameters["k_ail"]

        D1 = (l_B*a*N)/L_riser
        D2 = l_B*(L_riser-N*a)/L_riser
        #D2=0
        alpha = (2*Bi)**(1/2)

        integ = (p_ext_tube*a*N)/2
        A = (-k_ail*alpha*math.cosh(alpha*L_vf/a))/(a*math.sinh(alpha*L_vf/a)) * (integ/L_riser)

        chiet = chi-(1/A)
        #chiet = chi

        K = math.cosh(alpha*L_vf/a)*(-D1*Fprime*(h_rad+1/R_T)+(-D2*Fprime)*(1/(R_B*Fprime)))-2*k_abs*lambd_abs*m*tanh_or_inverse(m*L_af)
        T = math.cosh(alpha*L_vf/a)*(1+chiet*(D1*Fprime*(h_rad+1/R_T)+(D2*Fprime)*(1/(R_B*Fprime)))+2*k_abs*lambd_abs*m*tanh_or_inverse(m*L_af)*chiet)
        E = math.cosh(alpha*L_vf/a)*(D1*Fprime*(S+h_rad*T_sky+T_amb/R_T)+(D2*Fprime)*(T_back/(R_B*Fprime))+2*k_abs*lambd_abs*m*tanh_or_inverse(m*L_af)*(b/j))

    var["Ka"] = K
    var["Th"] = T
    var["Ep"] = E

def ab_f(parameters, var):
    N_harp = parameters["N_harp"]
    L_riser = parameters["L_riser"]
    m_dot = parameters["m_dot"]
    C_p = parameters["C_p"]

    R_tube = parameters["lambd_riser_back"]/parameters["k_riser"]
    R_2 = parameters["R_2"]
    h_back = 1/(parameters["h_back"]+parameters["h_rad_back"])

    w_tube = parameters["w_tube"]
    p_int_tube = parameters["p_int_tube"]
    p_ext_tube = parameters["p_ext_tube"]

    T_back = parameters["T_back"]
    
    if h_back == None:
        print("h_back")
        print(var["T_abs_mean"])
        h_back = 3.

    K = var["Ka"]
    T = var["Th"]
    E = var["Ep"]

    a = (N_harp/(m_dot*C_p))*(K/T)
    b = (N_harp/(m_dot*C_p))*(E/T)

    if parameters["fin_0"] == 1:
        gamma_0_int = parameters["gamma_0_int"]
    else:
        gamma_0_int = 0

    if parameters["fin_1"] == 1:
        gamma_1_int = parameters["gamma_1_int"]
        # print(gamma_1_int)
    else:
        gamma_1_int = 0
        

    k = parameters["k_ail"]
    C_B_f = (p_ext_tube*parameters["k_riser"])/parameters["lambd_riser_back"]
    h_fluid = parameters["h_fluid"]

    chi = 1/(h_fluid*p_int_tube)+1/C_B_f

    gamma_back = p_ext_tube/(R_2+1/h_back)

    zeta = (gamma_back + gamma_1_int + gamma_0_int)/(1+chi*(gamma_back+gamma_1_int+gamma_0_int))
    # print(zeta)

    a += (-N_harp/(m_dot*C_p))*zeta
    b += (N_harp/(m_dot*C_p))*zeta*T_back

    parameters["a_f"] = a
    parameters["b_f"] = b

# Eq. 560.36
def T_fluid_out(parameters, T_fluid_in,var):

    a = parameters["a_f"]
    b = parameters["b_f"]

    L_riser = parameters["L_riser"]

    res = (T_fluid_in+(b/a))*math.exp(a*L_riser) - b/a
    var["T_fluid_out"] = res

# Eq. 560.38
def qp_fluid(parameters,T_fluid_in,var):
    
    N_harp = parameters["N_harp"]
    L = parameters["L_riser"]
    m_dot = parameters["m_dot"]
    C_p = parameters["C_p"]    
    
    T_f_out = var["T_fluid_out"]
    res = (m_dot*C_p*(T_f_out-T_fluid_in))/(L*N_harp)

    var["qp_fluid"] = res

# Eq. 560.40
def T_fluid_mean(parameters,T_fluid_in,var):

    L_riser = parameters["L_riser"]

    h_back = parameters["h_back"]
    if h_back == None:
        print(var["T_abs_mean"])
        h_back = 3.

    a = parameters["a_f"]
    b = parameters["b_f"]

    res = ((T_fluid_in+(b/a))/(a*L_riser))*math.exp(a*L_riser) - (T_fluid_in+(b/a))/(a*L_riser) - b/a
    var["T_fluid_mean"] = res

# Eq. 560.28 -> calculate the mean base temperature
def T_Base_mean(parameters, var): #T_fluid has already been used for q_f_p and T_f_mean calculations

    h_fluid = parameters["h_fluid"]
    C_B = parameters["C_B"]
    p_int_tube = parameters["p_int_tube"]

    q_f_p = var["qp_fluid"]
    T_f_mean = var["T_fluid_mean"]

    res = (1/(h_fluid*p_int_tube)+1/C_B)*q_f_p + T_f_mean
    var["T_Base_mean"] = res

# Eq. 560.42 -> calculate the mean fin temperature
def T_fin_mean(parameters,var):

    lambd_abs = parameters["lambd_abs"]
    k_abs = parameters["k_abs"]
    W = parameters["W"]

    L_af = parameters["L_af"]

    R_T = parameters["R_TOP"] + 1/parameters["h_top"]
    R_B = parameters["R_2"] + 1/(parameters["h_back"]+parameters["h_rad_back"])
    h_fluid = parameters["h_fluid"]

    T_sky = parameters["T_sky"]
    T_amb = parameters["T_amb"]
    T_back = parameters["T_back"]

    h_rad = var["h_rad"]
    S = var["S"]
    Fprime = var["Fp"]

    j = var["j"]
    m = var["m"]

    T_B_mean = var["T_Base_mean"]

    first_term = (S+h_rad*T_sky+T_amb/R_T+T_back/(R_B*Fprime))/j

    second_term = (T_B_mean-first_term)*tanh_or_inverse(m*L_af)/(m*L_af)

    res = first_term + second_term
    var["T_fin_mean"] = res

# Eq. 560.43 -> calculate the mean absorber temperature
def T_abs_mean(parameters,var):

    W = parameters["W"]
    l_B = parameters["l_B"]
    L_af = parameters["L_af"]

    T_Base_mean = var["T_Base_mean"]
    T_fin_mean = var["T_fin_mean"]

    res = (l_B*T_Base_mean+(L_af*2)*T_fin_mean)/W
    var["T_abs_mean"] = res

# Eq. 560.1 -> calculte the mean PV surface temperature
def T_PV_mean(parameters,var):

    R_INTER = parameters["R_INTER"]
    R_T = parameters["R_TOP"] + 1/parameters["h_top"]
    h_fluid = parameters["h_fluid"]

    T_sky = parameters["T_sky"]
    T_amb = parameters["T_amb"]
    
    h_rad = var["h_rad"]
    S = var["S"]

    T_abs_mean = var["T_abs_mean"]

    res = (1/(1/R_T+h_rad+1/R_INTER))*(S+T_amb/R_T+h_rad*T_sky+(T_abs_mean/R_INTER))

    var["T_PV0"] = var["T_PV"]
    var["T_PV"] = res

def T_PV_meanB(parameters,var):

    R_INTER = parameters["R_INTER"]
    R_T = parameters["R_TOP"] + 1/parameters["h_top"]
    h_fluid = parameters["h_fluid"]

    T_sky = parameters["T_sky"]
    T_amb = parameters["T_amb"]
    
    h_rad = var["h_rad"]
    S = var["S"]

    T_Base_mean = var["T_Base_mean"]

    res = (1/(1/R_T+h_rad+1/R_INTER))*(S+T_amb/R_T+h_rad*T_sky+(T_Base_mean/R_INTER))

    var["T_PV_meanB"] = res

# Eq. 560.47
def Q_top_conv(parameters,var):

    T_PV_m = var["T_PV"]
    T_amb = parameters["T_amb"]

    R_T = parameters["R_TOP"] + 1/parameters["h_top"]
    W = parameters["W"]
    L = parameters["L_riser"]

    var["Q_top_conv"] = (W*L)*(T_PV_m-T_amb)/R_T

def Q_top_rad(parameters,var):

    h_r = var["h_rad"]
    T_PV_m = var["T_PV"]
    T_sky = parameters["T_sky"]
    W = parameters["W"]

    L = parameters["L_riser"]

    var["Q_top_rad"] = W*L*h_r*(T_PV_m-T_sky)

def Q_PV_plate(parameters,var):

    R_INTER = parameters["R_INTER"]
    W = parameters["W"]

    T_PV_m = var["T_PV"]
    T_abs_m = var["T_abs_mean"]
    L = parameters["L_riser"]

    var["Q_PV_plate"] = (W*L)*(T_PV_m-T_abs_m)/R_INTER

def power_balance_1(parameters,var):
    S = var["S"]
    Q1 = var["Q_top_conv"]
    Q2 = var["Q_top_rad"]
    Q3 = var["Q_PV_plate"]
    W = parameters["W"]
    L = parameters["L_riser"]

    var["power_balance_1"] = (W*L)*S-Q1-Q2-Q3

def Q_PV_Base(parameters,var):

    R_INTER = parameters["R_INTER"]
    l_B = parameters["l_B"]

    T_PV_mB = var["T_PV_meanB"]
    T_Base_m = var["T_Base_mean"]
    L = parameters["L_riser"]

    var["Q_PV_Base"] = L*l_B*((T_PV_mB-T_Base_m)/R_INTER)

def qp_PV_Base(parameters,var):

    R_INTER = parameters["R_INTER"]
    l_c = parameters["l_c"]

    T_PV_m = var["T_PV"]
    T_Base_m = var["T_Base_mean"]
    L = parameters["L_riser"]

    var["qp_PV_Base"] = l_c*((T_PV_m-T_Base_m)/R_INTER)

def Q_abs_back1(parameters,var):

    R_B = parameters["R_2"] + 1/(parameters["h_back"]+parameters["h_rad_back"])
    L_af = parameters["L_af"]

    T_abs_m = var["T_abs_mean"]
    T_back = parameters["T_back"]
    L = parameters["L_riser"]

    var["Q_abs_back1"] = L*L_af*(T_abs_m-T_back)/R_B

def Q_fluid(parameters,var):

    h_fluid = parameters["h_fluid"]
    p_int_tube = parameters["p_int_tube"]
    C_B = parameters["C_B"]
    chi = 1/(h_fluid*p_int_tube)+1/C_B

    T_Base_m = var["T_Base_mean"]
    T_fluid_m = var["T_fluid_mean"]
    L = parameters["L_riser"]

    var["Q_fluid1"]=(L/chi)*(T_Base_m-T_fluid_m)

    coeff_c_p = [4.2184,-0.0028218,0.000073478,-9.4712e-7,7.2869e-9,-2.8098e-11,4.4008e-14]
    coeff_c_p = list(reversed(coeff_c_p))

    T_m_C = (var["T_fluid_in"]+var["T_fluid_out"])/2 - 273.15
    parameters["C_p"] = np.polyval(coeff_c_p,T_m_C)*1000

    N_harp = parameters["N_harp"]
    L = parameters["L_riser"]
    m_dot = parameters["m_dot"]
    C_p = parameters["C_p"]    
    
    T_f_out = var["T_fluid_out"]
    T_f_in = parameters["T_fluid_in0"]

    var["Q_fluid2"] = (m_dot*C_p*(T_f_out-T_f_in))/(N_harp)

def Q_Base_back(parameters,var):

    R_B = parameters["R_2"] + 1/(parameters["h_back"]+parameters["h_rad_back"])
    iota = parameters["iota"]

    T_Base_m = var["T_Base_mean"]
    T_back = parameters["T_back"]

    L = parameters["L_riser"]

    var["Q_Base_back"] = L*iota*(T_Base_m-T_back)/R_B

def qp_Base_back(parameters,var):

    R_B = parameters["R_2"] + 1/(parameters["h_back"]+parameters["h_rad_back"])
    iota = parameters["iota"]

    T_Base_m = var["T_Base_mean"]
    T_back = parameters["T_back"]

    L = parameters["L_riser"]

    var["qp_Base_back"] = iota*(T_Base_m-T_back)/R_B

def Q_absfins_Base(parameters,var):
    q = var["qp_fin"]
    L = parameters["L_riser"]

    var["Q_absfins_Base"] = 2*L*q

def Q_abs_back2(parameters,var):
    var["Q_abs_back2"] = var["Q_absfins_Base"] - var["Q_PV_plate"] + var["Q_PV_Base"]

def power_balance_3(parameters,var):
    Q_PV_Base = var["Q_PV_Base"]
    Q_absfins_Base = var["Q_absfins_Base"]
    Q_fluid = var["Q_fluid1"]
    Q_Base_back = var["Q_Base_back"]
    Q_fluid_back = var["Q_fluid_back"]

    var["power_balance_3"] = Q_PV_Base + Q_absfins_Base - (Q_fluid + Q_fluid_back) - Q_Base_back

def PB_3(parameters,var):
    PB3 = var["qp_PV_Base"] - var["qp_Base_back"] + 2*var["qp_fin"]-var["qp_fluid"]
    var["PB_3"] = PB3
    # print(PB3)

def Q_fluid_back(parameters,var):

    p_ext_tube = parameters["p_ext_tube"]
    R_2 = parameters["R_2"]
    h_back = parameters["h_back"]+parameters["h_rad_back"]

    k = parameters["k_ail"]
    C_B_f = (p_ext_tube*parameters["k_riser"])/parameters["lambd_riser_back"]
    h_fluid = parameters["h_fluid"]
    p_int_tube = parameters["p_int_tube"]

    chi = 1/(h_fluid*p_int_tube)+1/C_B_f

    L = parameters["L_riser"]

    if parameters["fin_0"]==1:
        gamma_0_int = parameters["gamma_0_int"]
    else:
        gamma_0_int = 0
    if parameters["fin_1"]==1:
        gamma_1_int = parameters["gamma_1_int"]
    else:
        gamma_1_int = 0

    R_2 = parameters["R_2"]
    h_back = parameters["h_back"]+parameters["h_rad_back"]
    gamma_back = p_ext_tube/(R_2+1/h_back)

    T_fluid_m = var["T_fluid_mean"]
    T_back = parameters["T_back"]

    zeta = (gamma_back)/(1+chi*(gamma_back+gamma_1_int+gamma_0_int))

    var["Q_fluid_back"] = L*zeta*(T_fluid_m-T_back)


def qp_f0(parameters,var):

    T_fluid_m = var["T_fluid_mean"]
    T_back = parameters["T_back"]

    gamma_0_int = parameters["gamma_0_int"]

    var["qp_f0"] = gamma_0_int*(T_fluid_m-T_back)

def Q_f01(parameters,var):

    h_fluid = parameters["h_fluid"]
    p_int_tube = parameters["p_int_tube"]
    p_ext_tube = parameters["p_ext_tube"]

    k = parameters["k_ail"]
    C_B_f = (p_ext_tube*parameters["k_riser"])/parameters["lambd_riser_back"]


    chi = 1/(h_fluid*p_int_tube)+1/C_B_f

    L = parameters["L_riser"]

    if parameters["fin_0"]==1:
        gamma_0_int = parameters["gamma_0_int"]
    else:
        gamma_0_int = 0
    if parameters["fin_1"]==1:
        gamma_1_int = parameters["gamma_1_int"]
    else:
        gamma_1_int = 0

    R_2 = parameters["R_2"]
    h_back = parameters["h_back"]+parameters["h_rad_back"]
    gamma_back = p_ext_tube/(R_2+1/h_back)

    zeta = (gamma_1_int + gamma_0_int)/(1+chi*(gamma_back+gamma_1_int+gamma_0_int))
    
    T_fluid_m = var["T_fluid_mean"]
    T_back = parameters["T_back"]

    Q = L*zeta*(T_fluid_m-T_back)

    var["Q_f01"] = Q


def qp_f1(parameters,var):

    T_fluid_m = var["T_fluid_mean"]
    T_back = parameters["T_back"]

    gamma_1_int = parameters["gamma_1_int"]

    var["qp_f1"] = gamma_1_int*(T_fluid_m-T_back)

def qp_f2(parameters,var):

    T_abs_m = var["T_abs_mean"]
    T_back = parameters["T_back"]

    gamma_2_int = parameters["gamma_2_int"]

    var["qp_f2"] = gamma_2_int*(T_abs_m-T_back)

def Q_f2(parameters,var):

    var["Q_f2"] = var["qp_f2"] * parameters["L_riser"]

def one_loop(parameters,T_fluid_in,var):

    parameters["T_fluid_in0"] = T_fluid_in

    if parameters["fin_0"] == 1:
        Bi_f0(parameters)
        gamma_0_int(parameters)
    if parameters["fin_1"] == 1:
        Bi_f1(parameters)
        gamma_1_int(parameters)
    if parameters["fin_2"] == 1:
        Bi_f2(parameters)
        gamma_2_int(parameters)
    if parameters["fin_3"] == 1:
        Bi_f3(parameters)
        # directement dans le calcul de KTE()

    h_rad(parameters,var) # T_PV
    X_celltemp(parameters,var) # T_PV
    eta_PV(parameters,var) # X_celltemp so only T_PV
    S(parameters,var) # eta_PV so only T_PV

    Fp(parameters,var) # h_rad
    j(parameters,var) # Fp
    m(parameters,var) # Fp and j
    b(parameters,var) # h_rad, S and Fp
    KTE(parameters,var) # h_rad, S, Fp, j, m, b

    ab_f(parameters,var)

    T_fluid_out(parameters,T_fluid_in,var)
    qp_fluid(parameters,T_fluid_in,var)
    T_fluid_mean(parameters,T_fluid_in,var)
    T_Base_mean(parameters,var)
    T_fin_mean(parameters,var)
    T_abs_mean(parameters,var)

    if parameters["fin_0"] == 1 or parameters["fin_1"] == 1 or parameters["fin_2"] == 1:
        h_back_mean(parameters,var)
    else:
        h_back(parameters,var)

    T_PV_mean(parameters,var)
    T_PV_meanB(parameters,var)

    qp_PV_Base(parameters,var)
    qp_Base_back(parameters,var)
    qp_fin(parameters,var)

    h_top(parameters,var)


def compute_power(parameters,var):
    Q_top_conv(parameters,var)
    Q_top_rad(parameters,var)
    Q_PV_plate(parameters,var)
    Q_abs_back1(parameters,var)
    Q_PV_Base(parameters,var)
    Q_Base_back(parameters,var)
    Q_fluid(parameters,var)
    # qp_fluid_back(parameters,var)
    qp_fin(parameters,var)
    Q_absfins_Base(parameters,var)
    Q_abs_back2(parameters,var)
    Q_fluid_back(parameters,var)

    if parameters["fin_0"]==1 or parameters["fin_1"]==1:
        Q_f01(parameters,var)

    power_balance_1(parameters,var)
    power_balance_3(parameters,var)

    if parameters["fin_0"] == 1:
        qp_f0(parameters,var)
    if parameters["fin_1"] == 1:
        qp_f1(parameters,var)
    if parameters["fin_2"] == 1:
        pass

# parameters and var are dictionnaries
# Division of the panel in N rectangles (N=16)
def simu_one_steady_state(parameters,T_fluid_in0,guess_T_PV):

    list_T_PV = [guess_T_PV]
    list_T_f_out = [T_fluid_in0]

    list_var_conv = []

    N=parameters["N_meander"]

    list_df_historic = [] # liste de N df correspondant aux historiques de convergence pour chaque tranche de panneau
    df = pd.DataFrame()

    for i in range(N):
        var = {}

        new_guess_T_PV = list_T_PV[i]
        var["T_PV0"] = 0
        var["T_PV"] = new_guess_T_PV

        var['Slice'] = i

        T_f_in = list_T_f_out[i]
        var['T_fluid_in'] = T_f_in
        
        # print('boucle ',i)
        compt = 0
        while compt<= 2 or abs(var["T_PV"]-var["T_PV0"])>=0.001:
        # while compt<= 2 or abs(var["PB_3"])>=0.01:
            compt+=1
            one_loop(parameters,T_f_in,var)

            compute_power(parameters,var)

            par_var = {'m_dot' : parameters['m_dot'],'G':parameters['G'],'Gp':parameters['Gp'],'T_amb':parameters['T_amb'],'u':parameters['u'],'h_top' : parameters['h_top'], 'h_back' : parameters['h_back'], 'h_rad_back' : parameters["h_radh_back"],'h_fluid' : parameters['h_fluid']}
            var_copy = copy.deepcopy(var)
            to_add_conv = {**par_var, **var_copy}
            list_var_conv.append(to_add_conv)

        one_loop(parameters,T_f_in,var)
        #break
        # T_PV_27(parameters,var)
        
        compute_power(parameters,var)

        par_var = {'m_dot' : parameters['m_dot'],'G':parameters['G'],'Gp':parameters['Gp'],'T_amb':parameters['T_amb'],'u':parameters['u'],'h_top' : parameters['h_top'], 'h_back' : parameters['h_back'], 'h_rad_back' : parameters["h_radh_back"], 'h_fluid' : parameters['h_fluid']}
        var_copy = copy.deepcopy(var)
        to_add = {**par_var, **var_copy}

        df_to_add = pd.DataFrame.from_dict({'row' : to_add.values()},orient='index',columns=to_add.keys())
        df = pd.concat([df,df_to_add])

        list_T_PV.append(var["T_PV"])
        list_T_f_out.append(var["T_fluid_out"])

        list_df_historic.append(pd.DataFrame(list_var_conv))    

    df_mean = df.mean()
    df_sum = df.sum()

    df_one = pd.DataFrame()

    for str in df.keys():
        if str in ['m_dot','G','Gp','T_amb','u']:
            df_one[str] = [parameters[str]]
        elif str == "T_fluid_in":
            df_one[str] = [T_fluid_in0]
        elif str == "T_fluid_out":
            df_one[str] = [list_T_f_out[N]]
        elif str in ["T_fluid_mean","T_PV","T_abs_mean","T_Base_mean","T_fin_mean","T_abs_mean","T_PV_meanB","h_rad","h_top","h_back","h_fluid","X_celltemp","eta_PV","S"]:
            df_one[str] = [df_mean[str]]
        elif str in ["qp_fluid","qp_PV_Base","qp_Base_back","qp_fin","Q_top_conv","Q_top_rad","Q_PV_plate","Q_abs_back","Q_PV_Base","Q_Base_back","Q_fluid1","Q_fluid2","Q_absfins_Base","Q_fluid_back","Q_f01","qp_f0","qp_f1","qp_f2"]:
            df_one[str] = [df_sum[str]]

    return df,df_one,list_df_historic

def pos(x):
    if x>=0:
        return x
    else:
        return 0

def neg(x):
    if x<=0:
        return x
    else:
        return 0

def pos_df(df,col_name):
    l = []
    for x in df[col_name]:
        l.append(pos(x))
    return l

def neg_df(df,col_name):
    l = []
    for x in df[col_name]:
        l.append(neg(x))
    return l   


def simu_condi(par,condi_df):
    
    # Dataframe object
    df_res = pd.DataFrame()

    sigma = par["sigma"]

    compt_test = 0

    list_df = []
    list_list_df_historic = []

    for i in range(1,len(condi_df)+1):

        par["G"]=condi_df["G"][i]
        par["T_amb"]=condi_df["ta"][i]+273.15
        change_T_sky(par,'TUV')
        # Back temperature = ambiant temperature
        par["T_back"]=par["T_amb"]
        # Change wind_speed in parameters and adapt R_T
        change_u(par,condi_df["U"][i])
        par["m_dot"] = condi_df["mdot"][i]
        
        T_guess = (par["T_amb"]+condi_df["tin"][i]+273.15)/2

        df,df_one,list_df_historic = simu_one_steady_state(par,condi_df["tin"][i]+273.15,T_guess)

        df_res = pd.concat([df_res,df_one],ignore_index=True)
        list_df.append(df)
        list_list_df_historic.append(list_df_historic)

        compt_test+=1

    df_par = pd.DataFrame.from_dict(par, orient='index')

    # Analysing df

    # Be careful here you have zeros for some columns

    tab = pd.DataFrame()

    df_res['DT'] = df_res['T_fluid_out'] - df_res['T_fluid_in']
    df_res['T_m'] = (df_res['T_fluid_out'] + df_res['T_fluid_in'])/2
    df_res['T_m en °C'] = df_res['T_m']-273.15

    tab['G'] = df_res['G'] # a0
    tab['-(T_m - T_a)'] = -(df_res['T_m'] - df_res['T_amb']) # a1
    # tab['-(T_m - T_a)^2'] = -(df_res['T_m'] - df_res['T_amb'])**2 # a2
    tab['-(T_m - T_a)^2'] = 0.*df_res['T_m'] # a2
    tab['-up x (T_m - T_a)'] = (df_res['u'] - 3) * tab['-(T_m - T_a)'] # a3
    # tab['Gp'] = df_res['Gp'] # a4
    tab['Gp'] = 0. * df_res['Gp'] # a4
    tab['up x G'] = -(df_res['u'] - 3) * df_res['G'] # a6
    tab['up x Gp'] = -(df_res['u'] - 3) * df_res["Gp"] # a7
    tab['-(T_m - T_a)^4'] = -tab['-(T_m - T_a)']**4 # a8

    # coeff_density = [999.85,0.05332,-0.007564,0.00004323,-1.673e-7,2.447e-10]
    # coeff_density = list(reversed(coeff_density))

    coeff_c_p = [4.2184,-0.0028218,0.000073478,-9.4712e-7,7.2869e-9,-2.8098e-11,4.4008e-14]
    coeff_c_p = list(reversed(coeff_c_p))

    # df_res['density(T)'] = np.polyval(coeff_density,df_res['T_m en °C'])
    df_res['c_p(T)'] = np.polyval(coeff_c_p,df_res['T_m en °C'])*1000

    # df_res['m_dot'] = df_res['density(T)']*(par["m_dot"]/1000)

    df_res['Q_dot'] = df_res['m_dot']*df_res['c_p(T)']*df_res['DT']
    df_res['Q_dot / A_G'] = df_res['Q_dot']/(par['A_G'])

    matrice = tab.to_numpy()
    B = df_res['Q_dot / A_G'].to_numpy()

    X = np.linalg.lstsq(matrice, B, rcond = -1)

    #_ = plt.plot(df['T_m*'].to_numpy(), B, 'o', label='Original data', markersize=2)
    #_ = plt.plot(df['T_m*'].to_numpy(), np.dot(matrice,X[0]), 'o', label='Fitted line',markersize=2)
    #_ = plt.legend()
    #plt.show()

    df_res_to_concat = df_res.drop(columns=["G","Gp"])

    df_res = pd.concat([tab,df_res_to_concat],axis=1)

    return df_par,df_res,X,list_df,list_df_historic

def find_a_i(df,par):
    tab = pd.DataFrame()

    df['DT'] = df['T_fluid_out'] - df['T_fluid_in']
    df['T_m'] = (df['T_fluid_out'] + df['T_fluid_in'])/2

    df['T_m en °C'] = df['T_m']-273.15

    tab['G'] = df['G'] # a0
    tab['-(T_m - T_a)'] = -(df['T_m'] - df['T_amb']) # a1
    # tab['-(T_m - T_a)^2'] = -(df['T_m'] - df['T_amb'])**2 # a2
    tab['-(T_m - T_a)^2'] = 0.*df['T_m'] # a2
    tab['-up x (T_m - T_a)'] = (df['u'] - 3) * tab['-(T_m - T_a)'] # a3
    # tab['Gp'] = df['Gp'] # a4
    tab['Gp'] = 0. * df['Gp'] # a4
    tab['dT/dt'] = 0. * df['Gp'] # a5 = 0
    tab['up x G'] = -(df['u'] - 3) * df['G'] # a6
    tab['up x Gp'] = -(df['u'] - 3) * df["Gp"] # a7
    tab['-(T_m - T_a)^4'] = -tab['-(T_m - T_a)']**4 # a8

    # coeff_density = [999.85,0.05332,-0.007564,0.00004323,-1.673e-7,2.447e-10]
    # coeff_density = list(reversed(coeff_density))

    coeff_c_p = [4.2184,-0.0028218,0.000073478,-9.4712e-7,7.2869e-9,-2.8098e-11,4.4008e-14]
    coeff_c_p = list(reversed(coeff_c_p))

    # df['density(T)'] = np.polyval(coeff_density,df['T_m en °C'])
    df['c_p(T)'] = np.polyval(coeff_c_p,df['T_m en °C'])*1000

    # df['m_dot'] = df['density(T)']*(par["m_dot"]/1000)

    df['Q_dot'] = df['m_dot']*df['c_p(T)']*df['DT']
    df['Q_dot / A_G'] = df['Q_dot']/(par['A_G'])

    matrice = tab.to_numpy()
    B = df['Q_dot / A_G'].to_numpy()

    X = np.linalg.lstsq(matrice, B, rcond = -1)

    return X

def simu_condi_mpe(par,condi_df,l,h_back,L):
    
    variables = ['N_test','T_guess','G', 'Gp', 'T_amb', 'u', 'T_abs','T_fluid_in', 'T_fluid_out']
    
    # Dataframe object
    df = pd.DataFrame(columns = variables)

    sigma = par["sigma"]

    compt_test = 0

    for i in range(1,len(condi_df)+1):

        par["G"]=condi_df["G"][i]

        # T_amb = T_back
        par["T_amb"]=condi_df["ta"][i]+273.15

        change_T_sky(par,'TUV')

        # Back temperature = ambiant temperature
        par["T_back"]=par["T_amb"]

        # Change wind_speed in parameters and adapt R_T
        change_u(par,condi_df["U"][i])

        par["m_dot"] = condi_df["mdot"][i]

        T_f_in_list = [condi_df["tin"][i]+273.15]                

        T_f_out = par["T_back"] + (T_f_in_list[0]-par["T_back"])*math.exp(-(l*h_back*L)/((par["m_dot"]/par["N_harp_actual"])*par["C_p"]))
        
        # len(T_f_out_list) = 1

        to_add = {'N_test' : compt_test, 'T_guess' : 293.15, 'G' : par["G"], 'Gp' : par["Gp"], 'T_amb' : par["T_amb"], 'h_back' : h_back, 'u' : par["u"], 'T_fluid_in' : T_f_in_list[0], 'T_abs' : 293.15,'T_fluid_out' : T_f_out}

        df_to_add = pd.DataFrame.from_dict({'row' : to_add.values()},orient='index',columns=to_add.keys())

        df = pd.concat([df,df_to_add])

        compt_test+=1

    df_par = pd.DataFrame.from_dict(par, orient='index')

    # Analysing df

    # Be careful here you have zeros for some columns

    df['DT'] = df['T_fluid_out'] - df['T_fluid_in']
    df['T_m'] = (df['T_fluid_out'] + df['T_fluid_in'])/2
    df['T_m*'] = (df['T_m'] - df['T_amb'])/df['G']
    df['G x (T_m*)^2'] = df['G'] * df['T_m*']**2 * 0
    df['up x T_m*'] = (df['u'] - 3) * df['T_m*']
    df['Gp/G'] = df['Gp']/df['G']
    df['up'] = df['u'] - 3
    df['up x Gp/G'] = (df['up'] * df['Gp'])/df['G']
    df['G^3 x (T_m*)^4'] = df['G']**3 * df['T_m*']**4 * 0

    df['T_m en °C'] = df['T_m']-273.15

    coeff_density = [999.85,0.05332,-0.007564,0.00004323,-1.673e-7,2.447e-10]
    coeff_density = list(reversed(coeff_density))

    coeff_c_p = [4.2184,-0.0028218,0.000073478,-9.4712e-7,7.2869e-9,-2.8098e-11,4.4008e-14]
    coeff_c_p = list(reversed(coeff_c_p))

    df['density(T)'] = np.polyval(coeff_density,df['T_m en °C'])
    df['c_p(T)'] = np.polyval(coeff_c_p,df['T_m en °C'])*1000

    df['m_dot'] = df['density(T)']*(par["m_dot"]/1000)

    df['Q_dot'] = df['m_dot']*df['c_p(T)']*df['DT']
    df['Q_dot / (A_G x G)'] = df['Q_dot']/(par['A_G']*df['G'])

    ones = pd.DataFrame(np.ones(len(df['T_m*'])),columns=['Ones'])
    ones_column = ones["Ones"]
    df_mat = df[['T_m*','G x (T_m*)^2','up x T_m*','Gp/G','up','up x Gp/G','G^3 x (T_m*)^4']].join(ones_column)

    matrice = df_mat.to_numpy()
    B = df['Q_dot / (A_G x G)'].to_numpy()

    X=np.linalg.lstsq(matrice, B, rcond = -1)

    #_ = plt.plot(df['T_m*'].to_numpy(), B, 'o', label='Original data', markersize=2)
    #_ = plt.plot(df['T_m*'].to_numpy(), np.dot(matrice,X[0]), 'o', label='Fitted line',markersize=2)
    #_ = plt.legend()
    #plt.show()

    return df_par,df,X

def simu_condi_mpe_big(par,condi_df,l,L,h_back_top,h_back_bottom,N_harp):
    
    variables = ['N_test', 'm_dot', 'T_guess','G', 'Gp', 'T_amb', 'u', 'T_abs','T_fluid_in', 'T_fluid_out']
    
    # Dataframe object
    df_res = pd.DataFrame(columns = variables)

    sigma = par["sigma"]

    compt_test = 0

    for i in range(1,len(condi_df)+1):

        par["G"]=condi_df["G"][i]

        # T_amb = T_back
        par["T_amb"]=condi_df["ta"][i]+273.15

        change_T_sky(par,'TUV')

        # Back temperature = ambiant temperature
        par["T_back"]=par["T_amb"]

        # Change wind_speed in parameters and adapt R_T
        change_u(par,condi_df["U"][i])

        par["m_dot"] = condi_df["mdot"][i]

        T_f_in_list = [condi_df["tin"][i]+273.15]                

        T_f_out = par["T_back"] + (T_f_in_list[0]-par["T_back"])*math.exp(-(l*L*h_back_top+l*L*h_back_bottom)/((par["m_dot"]/N_harp)*par["C_p"]))
        
        # len(T_f_out_list) = 1

        to_add = {'N_test' : compt_test, 'm_dot' : par["m_dot"], 'T_guess' : 293.15, 'G' : par["G"], 'Gp' : par["Gp"], 'T_amb' : par["T_amb"], 'h_back' : h_back_top, 'u' : par["u"], 'T_fluid_in' : T_f_in_list[0], 'T_abs' : 293.15,'T_fluid_out' : T_f_out}

        df_to_add = pd.DataFrame.from_dict({'row' : to_add.values()},orient='index',columns=to_add.keys())

        df_res = pd.concat([df_res,df_to_add])

        compt_test+=1

    df_par = pd.DataFrame.from_dict(par, orient='index')

    # Analysing df

    # Be careful here you have zeros for some columns

    tab = pd.DataFrame()

    df_res['DT'] = df_res['T_fluid_out'] - df_res['T_fluid_in']
    df_res['T_m'] = (df_res['T_fluid_out'] + df_res['T_fluid_in'])/2
    df_res['T_m en °C'] = df_res['T_m']-273.15

    # tab['G'] = 0. * df_res['G'] # a0
    tab['-(T_m - T_a)'] = -(df_res['T_m'] - df_res['T_amb']) # a1
    # tab['-(T_m - T_a)^2'] = -(df_res['T_m'] - df_res['T_amb'])**2 # a2
    # tab['-(T_m - T_a)^2'] = 0.*df_res['T_m'] # a2
    # tab['-up x (T_m - T_a)'] = (df_res['u'] - 3) * tab['-(T_m - T_a)'] # a3
    # tab['Gp'] = df_res['Gp'] # a4
    # tab['Gp'] = 0. * df_res['Gp'] # a4
    # tab['up x G'] = -(df_res['u'] - 3) * df_res['G'] # a6
    # tab['up x Gp'] = -(df_res['u'] - 3) * df_res["Gp"] # a7
    # tab['-(T_m - T_a)^4'] = 0. * (-tab['-(T_m - T_a)']**4) # a8

    # coeff_density = [999.85,0.05332,-0.007564,0.00004323,-1.673e-7,2.447e-10]
    # coeff_density = list(reversed(coeff_density))

    coeff_c_p = [4.2184,-0.0028218,0.000073478,-9.4712e-7,7.2869e-9,-2.8098e-11,4.4008e-14]
    coeff_c_p = list(reversed(coeff_c_p))

    # df_res['density(T)'] = np.polyval(coeff_density,df_res['T_m en °C'])
    df_res['c_p(T)'] = np.polyval(coeff_c_p,df_res['T_m en °C'])*1000

    # df_res['m_dot'] = df_res['density(T)']*(par["m_dot"]/1000)

    df_res['Q_dot'] = df_res['m_dot']*df_res['c_p(T)']*df_res['DT']
    df_res['Q_dot / A_G'] = df_res['Q_dot']/(par['A_G'])

    tab = tab.astype('float64')

    matrice = tab.to_numpy()
    B = df_res['Q_dot / A_G'].to_numpy()

    X = np.linalg.lstsq(matrice, B, rcond = -1)

    #_ = plt.plot(df['T_m*'].to_numpy(), B, 'o', label='Original data', markersize=2)
    #_ = plt.plot(df['T_m*'].to_numpy(), np.dot(matrice,X[0]), 'o', label='Fitted line',markersize=2)
    #_ = plt.legend()
    #plt.show()

    df_res_to_concat = df_res.drop(columns=["G","Gp"])

    df_res = pd.concat([tab,df_res_to_concat],axis=1)

    return df_par,df_res,X


# def q_tot_persqm(parameters,T_abs):
#     var = {'T_abs_mean':T_abs}
#     h_back(parameters,var) # this function uses T_back 
#     ail_biot(parameters)
#     alpha_ail(parameters)
#     beta_ail(parameters)
#     gamma(parameters)

#     gamm = parameters["gamma"]
#     DT = T_abs - parameters["T_back"]

#     D_tube = parameters["D_tube"]
 
#     N_meander = parameters["N_meander"]
#     delta = parameters["delta"]
#     longueur = parameters["longueur"]
    

#     k_ail = parameters["k_ail"]
#     a = parameters["lambd_ail"]
#     DELTA_a = parameters["DELTA_a"]

#     #return 2*N_meander*(delta/longueur)*k_ail*a*DELTA_a*gamm*DT

#     #return parameters["h_back"]
#     #return gamm
#     return -((longueur-N_meander*D_tube)/longueur)*k_ail*a*DELTA_a*gamm*DT

def change_T_sky(parameters,type):
    if type == "TUV":
        parameters["Gp"] = 4
        parameters["T_sky"] = ((parameters["Gp"]/parameters["sigma"]) + parameters["T_amb"]**4)**(1/4)
    
    else :
        Tsk = 0.0552*parameters["T_amb"]**1.5

        parameters["T_sky"] = Tsk
        parameters["Gp"] = parameters["sigma"]*(parameters["T_sky"]**4 - parameters["T_amb"]**4)

def change_N_ail(parameters,N):
    parameters["N_ail"] = N
    parameters["DELTA_a"] = N/parameters["L_riser"]

def change_a(parameters,a):
    parameters["lambd_ail"]=a
    Bi_f0(parameters)
    Bi_f1(parameters)
    Bi_f2(parameters)
    Bi_f3(parameters)

def change_air_layer(par,air_layer):
    old_air_layer = par["air_layer"]
    k_air = par["k_air"]

    old_R_T = par["R_INTER"]

    old_r_air = old_air_layer/k_air
    new_r_air = air_layer/k_air

    par["R_INTER"] = old_R_T - old_r_air + new_r_air
    par["air_layer"] = air_layer
    #print(par["R_INTER"])

def change_b_htop(par,b_htop):
    par["b_htop"] = b_htop

    change_u(par,par["u"])

def change_ins(par,e_ins):
    k_ins = par["k_insulation"]

    par["R_2"]=e_ins/k_ins

def change_N_fins_per_EP(par,N):
    par["N_fins_on_abs"] = (6*N)/par["N_harp"]
    par["D"] = (0.160/N)

