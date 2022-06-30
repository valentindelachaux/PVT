# variable N_ail
# elif par["test"]=="q0":

#     L = par["longueur"]
#     l = par["largeur"]

#     N_meander = 16 

#     a = par["lambd_ail"]
#     L_a = par["L_a"]


#     theta_list = [35]
#     Tabs_list = [269.9,269.5,269,268,267,266]
#     Tamb_list = [270.1,270.5,271,272,273,274]

#     #Tabs_list = [268]
#     #Tamb_list = [272]

#     for i in range(len(theta_list)):
#         par["theta"] = theta_list[i]
#         for j in range(len(Tabs_list)):
#             par["T_back"] = Tamb_list[j]

#             df = pd.DataFrame(columns = ['ailettes','absorbeur','tubes'])

#             DT = Tabs_list[j] - Tamb_list[j]
#             DTround = round(DT,1)
            
#             N_list = []
#             q_tot_persqm_list = []
#             for N in range(10,200):
#                 N_list.append(N)
#                 par["N_ail"] = N
#                 par["DELTA_a"] = N/par["L_riser"]

#                 ail = ty.q_tot_persqm(par,Tabs_list[j])
#                 df = df.append({'ailettes' : ail, 'absorbeur' : (par["h_inner"]*l*(1-N*a)*DT)/(L*l), 'tubes' : (N_meander*par["h_inner"]*math.pi*par["D_tube"]*par["L_riser"]*DT)/(L*l)}, ignore_index=True)

#                 q_tot_persqm_list.append(ail)
#                 #ty.h_inner(par,Tabs0,Tamb0)
#                 #q_tot_persqm_list.append(par["h_inner"])

#             plt.plot(np.array(N_list),np.array(df['ailettes']),label='DT = '+str(DTround)+' K ')
#             #plt.plot(np.array(N_list),np.array(df['absorbeur']),label='Absorbeur'+'DT = '+str(DT)+' K '+str(theta_list[i])+'°')
#             #plt.plot(np.array(N_list),np.array(df['tubes']),label='Tubes'+'DT = '+str(DT)+' K '+str(theta_list[i])+'°')

#     plt.xlabel('Number of fins')
#     plt.ylabel('Power (W/m2 abs.)')
#     #plt.ylabel('h_back (W/(mK)')
#     plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
#     plt.title('Inclinaison '+str(par["theta"])+'°, N_riser = '+str(par["N_meander"])+', L_a = '+str(par["L_a"]*100)+' cm, a = '+str(par["lambd_ail"]*1000)+' mm')
#     plt.gcf().subplots_adjust(right = 0.762)
#     plt.grid()

#     plt.show()

#     print("ok")

# # variable a
# elif par["test"]=="q1":

#     L = par["longueur"]
#     l = par["largeur"]

#     N_meander = 16 

#     a = par["lambd_ail"]
#     L_a = par["L_a"]


#     a_list = np.linspace(0.00001,0.001,100)
#     a_list_mm = np.linspace(0.01,1,100)
#     Tabs_list = [268]
#     Tamb_list = [272]

#     N_list = [20,40,60,80,100,120,140,160,180,200,220]

#     #Tabs_list = [268]
#     #Tamb_list = [272]

#     for i in range(len(N_list)):
#         ty.change_N_ail(par,N_list[i])
#         for j in range(len(Tabs_list)):
#             par["T_back"] = Tamb_list[j]

#             df = pd.DataFrame(columns = ['ailettes','absorbeur','tubes'])

#             DT = Tabs_list[j] - Tamb_list[j]
#             DTround = round(DT,1)
            
#             q_tot_persqm_list = []
#             for l in range(len(a_list)):
#                 ty.change_a(par,a_list[l])

#                 ail = ty.q_tot_persqm(par,Tabs_list[j])
#                 df = df.append({'ailettes' : ail}, ignore_index=True)

#                 q_tot_persqm_list.append(ail)
#                 #ty.h_inner(par,Tabs0,Tamb0)
#                 #q_tot_persqm_list.append(par["h_inner"])

#             plt.plot(np.array(a_list_mm),np.array(df['ailettes']),label='N = '+str(N_list[i])+' fins ')
#             #plt.plot(np.array(N_list),np.array(df['absorbeur']),label='Absorbeur'+'DT = '+str(DT)+' K '+str(theta_list[i])+'°')
#             #plt.plot(np.array(N_list),np.array(df['tubes']),label='Tubes'+'DT = '+str(DT)+' K '+str(theta_list[i])+'°')

#     print(par)

#     plt.xlabel('Width of fins a (mm)')
#     plt.ylabel('Power (W/m2 abs.)')
#     plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
#     plt.title('Inclinaison '+str(par["theta"])+'°, N_riser = '+str(par["N_meander"])+', L_a = '+str(par["L_a"]*100)+' cm, DT = '+str(DT)+' K')
#     plt.grid()

#     plt.show()

#     print("ok")

# elif par["test"]=="q2":

#     Tabs0 = 299.9
#     Tamb0 = 300.1
#     DT = Tabs0-Tamb0
#     L = par["longueur"]
#     l = par["largeur"]

#     N_ail = par["N_ail"]

#     D_tube = par["D_tube"]

#     a = par["lambd_ail"]
#     L_a = par["L_a"]

#     theta_list = [30]
#     N_ail_list = [10,30,50]

#     for i in range(len(theta_list)):

#         for j in range(len(N_ail_list)):
#             par["N_ail"] = N_ail_list[j]
#             par["DELTA_a"] = N_ail_list[j]/par["L_riser"]

#             df = pd.DataFrame(columns = ['ailettes','absorbeur','tubes'])

#             par["theta"] = theta_list[i]
            
#             N_list = []
#             q_tot_persqm_list = []
#             for N in range(10,40):
#                 N_list.append(N)
#                 par["N_meander"] = N

#                 ail = ty.q_tot_persqm(par,Tabs0,Tamb0)
#                 df = df.append({'ailettes' : ail, 'absorbeur' : (par["h_inner"]*(L*(l-par["N_ail"]*a)-l*D_tube*N)*DT)/(L*l), 'tubes' : (par["N_meander"]*par["h_inner"]*math.pi*par["D_tube"]*par["L_riser"]*DT)/(L*l)}, ignore_index=True)

#                 q_tot_persqm_list.append(ail)
#                 #ty.h_inner(par,Tabs0,Tamb0)
#                 #q_tot_persqm_list.append(par["h_inner"])

#             plt.plot(np.array(N_list),np.array(df['ailettes']),label='Ailettes ('+str(N_ail_list[j])+') '+str(theta_list[i])+'°')
#             plt.plot(np.array(N_list),np.array(df['absorbeur']),label='Absorbeur ('+str(N_ail_list[j])+') '+str(theta_list[i])+'°')
#             plt.plot(np.array(N_list),np.array(df['tubes']),label='Tubes ('+str(N_ail_list[j])+') '+str(theta_list[i])+'°')

#     plt.xlabel('Number of risers')
#     plt.ylabel('Power (W/m2 abs.)')
#     plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
#     plt.grid()

#     plt.show()

#     print("ok")