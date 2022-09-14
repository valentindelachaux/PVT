from email.errors import HeaderDefect
from matplotlib import pyplot as plt
from scipy.integrate import solve_bvp,odeint
import scipy.constants as scc
import numpy as np
import math
import pandas as pd
import openpyxl as opxl
from openpyxl.utils.dataframe import dataframe_to_rows

"""
def f(u,z):
    return (u[1],-5*u[1]-7)

y0 = [21,12]
xs = np.arange(0,5,0.1)
us = odeint(f,y0,xs)
ys = us[:,0]

plt.plot(xs,ys,'-')
plt.plot(xs,ys,'ro')
plt.xlabel('x values')
plt.ylabel('y values')

plt.show() """

r = 0.02 # 2 cm de rayon
h = 5
k = 226
# T_ext = 293.15
# T_0 = 297.15

D_tube = 0.01587

W = 0.08 # largeur ailette
Wc = D_tube # largeur d'ailette si on prend en compte que le diamètre du tube
a = 0.00021 # épaisseur ailette
Heta = 0.08 # hauteur d'ailette


def bc(y0, y1,T_0,T_ext):
    # Values of y at z=0:
    T0, Tp0 = y0

    # Values of dy/dz at z=L_a=r:  
    T1, Tp1 = y1

    # These return values are what we want to be 0:
    return [T0-T_0, Tp1+(h/k)*(T1-T_ext)]



# trapèze
def g(z,y,T_ext):
    A = (2*a*W*z)/Heta
    Ap = (2*a*W)/Heta
    p = 2*(a + (2*W*z)/Heta)
    return (y[1],(1/A)*(-Ap*y[1]+(h/k)*p*(y[0]-T_ext)))

# rectangle
def g2(z,y,T_ext):
    A = a*Wc
    Ap = 0
    p = 2*(a + Wc)
    return (y[1],(1/A)*(-Ap*y[1]+(h/k)*p*(y[0]-T_ext)))

# disque
def g3(z,y,T_ext):
    A = 2*math.pi*z*a
    Ap = 2*math.pi*a
    p = 2*(2*math.pi*z)
    return (y[1],(1/A)*(-Ap*y[1]+(h/k)*p*(y[0]-T_ext)))

#zs = np.arange(0,2,0.1)


zs = np.linspace(D_tube/2,Heta/2,100)
    
T_0_list = [250,255,260,265,267,270,275,280,285,290,295,300,305,310]
T_ext_list = [251,256,261,266,271,273,276,281,286,291,296,301,306,311]

variables = ['T_0','T_ext','phi1','phi2']

# Dataframe object
df = pd.DataFrame(columns = variables)

for i in range(len(T_0_list)):
    for j in range(len(T_ext_list)):

        T_0 = T_0_list[i]
        T_ext = T_ext_list[j]

        # Use the solution to the initial value problem as the initial guess
        # for the BVP solver. (This is probably not necessary!  Other, simpler
        # guesses might also work.)
        ystart = odeint(lambda z,y: g(z,y,T_ext), [1, 0], zs, tfirst=True)

        result = solve_bvp(lambda z,y: g(z,y,T_ext),
                        lambda y0, y1: bc(y0, y1,T_0,T_ext), zs, ystart.T)

        phi1 = result.y[1][0]

        ystart = odeint(lambda z,y: g2(z,y,T_ext), [1, 0], zs, tfirst=True)

        result = solve_bvp(lambda z,y: g2(z,y,T_ext),
                        lambda y0, y1: bc(y0, y1,T_0,T_ext), zs, ystart.T)

        phi2 = result.y[1][0]

        df = df.append({'T_0' : T_0, 'T_ext' : T_ext, 'phi1' : phi1, 'phi2' : phi2}, ignore_index=True)

wbo = opxl.Workbook()
wso = wbo.active
wso.title = "Table"

for d in dataframe_to_rows(df, index=True, header=True):
    wso.append(d)

fichier_o = r'C:\Users\BU05\Documents\Modele1D_Type560\Test-ailettes.xlsx'

wbo.save(filename = fichier_o)
wbo.close()

print("Finished")