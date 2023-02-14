import math

import openpyxl as opxl
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def radius(e_he,lambd):
    r = (1/(4*e_he))*(e_he**2+(lambd**2/4))
    return r

def e_he(radius,lambd):
    racines = np.roots([1,-4*radius,lambd**2/4])
    if racines[0]>0 and racines[1]>0:
        return min(racines)
    else:
        return max(racines)

# triplet = [e_he,lambd,radius]

def omega2(trip):
    x2 = trip[1]/2
    y2 = math.sqrt(4*trip[2]**2-x2**2)
    return [x2,y2]


