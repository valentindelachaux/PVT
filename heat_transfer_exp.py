import math
import fluids as fds
import ht
import numpy as np
import matplotlib.pyplot as plt

Q = np.linspace(0.1,100,200) # L/h
internal = []
internal_2 = []
internal_3 = []
V_list = []

Re_list = []


Dint = 0.008
rho = 997
nuw = 1*1E-6
muw = nuw*rho

A = math.pi*(Dint/2)**2
Prw = 7.

rel_rghn = 0.001/Dint

lambdaw = 0.660

for q in Q:
    qc = q/3600000 # en m3/s
    V = qc/A # vitesse du fluid en m/s

    Rew = fds.core.Reynolds(V,Dint,rho,mu = muw)
    V_list.append(V)
    Re_list.append(Rew)

    Nu = ht.conv_internal.Nu_conv_internal(Re=Rew,Pr=Prw, eD = rel_rghn, Di = Dint)
    Nu_2 = 0.7*0.023*(Rew**0.8)*(Prw**0.4)
    internal.append((lambdaw/Dint)*Nu)
    internal_2.append((lambdaw/Dint)*Nu_2)
    #internal_2.append(ht.conv_internal.turbulent_Churchill_Zajic(Re=Rew,Pr=Prw,fd=1.))
    #internal_3.append(ht.conv_internal.turbulent_Colburn(Rew,Prw))


#plt.plot(Re_list,internal,label='Churchill')
#plt.plot(Re_list,internal,label='Colburn')

fig, ax1 = plt.subplots()

ax2 = ax1.twinx()
ax1.plot(Q, internal, 'g-')
ax1.plot(Q, internal_2, 'r-')
ax2.plot(Q, Re_list, 'b-')

ax1.set_xlabel('Q (L/h)')
ax1.set_ylabel('h (W/m2K)', color='g')
ax2.set_ylabel('Re', color='b')

plt.grid()
plt.show()

