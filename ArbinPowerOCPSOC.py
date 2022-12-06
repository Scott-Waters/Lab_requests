import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
from statistics import mean
import scipy
import csv
import openpyxl


def check_step(df):

    stepType = ""
    
    cycle_num_ser = pd.unique(df["Cycle_Index"].values.ravel())    
    cycle_num_list = cycle_num_ser.tolist()
    df_name = ""
    step_dict = {}
    stepSer =  pd.unique(df["Step_Index"].values.ravel())
    stepList = stepSer.tolist()
    

    for x in cycle_num_list:
        #makes df of individual cycles
        df_name = f"Cycle_{x}_df"
        df_name = df.query("Cycle_Index == @x")
        df_name.drop(["Data_Point","Date_Time", "Test_Time(s)", "ACR(Ohm)", "dV/dt(V/s)", "Internal_Resistance(Ohm)", "dQ/dV(Ah/V)", "Charge_Energy(Wh)", "Discharge_Energy(Wh)", "dV/dQ(V/Ah)"], inplace = True, axis =1)
        
           
    #finds unique values in step index
        #makes df of each step in order to assign step type 
        CycleStepSer =  pd.unique(df_name["Step_Index"].values.ravel())
        CycleStepList = CycleStepSer.tolist()
        #is all steps IN CYCLE
        for n in stepList:
            #step list is all steps
            #looks for each step in the cycle, if the cycle is in the step, it checks the type
            if n in CycleStepList and n not in step_dict.keys():
                
                #makes df of step n
                df_step_name = ""
                df_step_name = f"Step_{n}_df"
                df_step_name = df_name.query("Step_Index == @n")
            #find first and last, and average current, voltage and time value of a step
                A1 = df_step_name["Current(A)"].iloc[0]
                AF = df_step_name["Current(A)"].iloc[-1]
                averageA = df_step_name["Current(A)"].mean()
                V1 = df_step_name["Voltage(V)"].iloc[0]
                VF = df_step_name["Voltage(V)"].iloc[-1]
                averageV = df_step_name["Voltage(V)"].mean()
                TF = df_step_name["Step_Time(s)"].iloc[-1]
               

                #determine the type of step
                
                if TF < 1:
                    stepType = "IR or cap reset"

                elif abs(AF) - abs(A1) > 0.1 or abs(AF) - abs(A1) < -0.1:
                    if abs(averageV) - abs(V1) <0.15 and abs(averageV) - abs(VF) <0.15 and averageA > 0: #changing current, constant V, average positive current
                        stepType = "Charge V Hold"
                    elif averageA > 0:#changing current, average positive current
                        #if it is the first instance, it will be the ASR
                        if("ASR" in step_dict.values()):
                            stepType = "Charge Sweep"   
                        else:
                            stepType = "ASR"
                    
                    elif abs(averageV) - abs(V1) <0.15 and abs(averageV) - abs(VF) <0.15 and averageA < 0:
                        #changing current, constant V, average negative current
                        stepType = "Discharge V Hold"
                    elif averageA < 0:
                        #changing current, average negative current
                        stepType = "Discharge Sweep"
                   
                elif A1 - AF < 0.05 and averageA > 0: #constant positive current
                    #checks if it is the first charge, assigns it as pre-charge if it is
                    if("Pre-charge" in step_dict.values()):
                        stepType = "Charging"   
                    else:
                        stepType = "Pre-charge"
                    
                elif A1 - AF < 0.05 and averageA < 0: #constant negative current
                    #checks if it is the first 'discharge' step, corresponding to predischarge
                    if("Pre-discharge" in step_dict.values()):
                        stepType = "Discharging"   
                    else:
                        stepType = "Pre-discharge"
                elif A1 == 0 and AF == 0: #no current
                    
                    if("Charged OCP" in step_dict.values()):
                        stepType = "Discharged OCP"   
                    else:
                        stepType = "Charged OCP"
                    #assigns stype type to step number (#:TYPE)
                step_dict[n] = stepType
         
    return step_dict

def file_reader(file, theo_cap, SA, cycles, volt_prof_list):
    #opens excel file, makes df of the correct sheet
    xls = pd.ExcelFile(file)
    df1 = pd.read_excel(xls, sheet_name = 1)
    step_type = check_step(df1)
    #runs df1 through data collector, which breaks apart the steps into new df, returns dictionary of step#:type
    
    #gets lists of keys and values
    step_list = list(step_type.keys())
    type_list = list(step_type.values())

    #gets location of value, associates it to the key
    charge_pos = type_list.index("Charging")
    charge_step = step_list[charge_pos]

    discharge_pos = type_list.index("Discharging")
    discharge_step = step_list[discharge_pos]

    power_pos = type_list.index("Discharge Sweep")
    power_step = step_list[power_pos]

    OCP_pos = type_list.index("Charged OCP")
    OCP_step = step_list[OCP_pos]

    

    ASR_pos = type_list.index("ASR")
    ASR_step = step_list[ASR_pos]
    #Plot ASR, return ASR as float 2 dec
    ASR_df = df1.query("Step_Index == @ASR_step")
    ASR = ASR_calc(ASR_df, SA)
    ASR_dict = {}
    ASR_dict[f"ASR (Ohm cm\u00b2)"] = ASR
    df_ASR_fin = pd.DataFrame.from_dict(ASR_dict, orient = "index")
    df_ASR_fin.columns = ["Initial"]
    #makes df of all charge steps, discharge steps, power, and charged OCP steps
    SOC_list = []
    SOC_dict = {}

    charging_df = df1.query("Step_Index == @charge_step")
    SOC_list = SOC_calc(charging_df, theo_cap)
    #makes list of SOC of the charge cycles
    SOC_dict["SOC (%)"] = SOC_list

    df_SOCs = pd.DataFrame.from_dict(SOC_dict)
    df_SOCs.reset_index(inplace=True)
    df_SOCs = df_SOCs.rename(columns = {'index':'Cycle Number'})


    discharging_df = df1.query("Step_Index == @discharge_step")
    #makes voltage profile plots of desired cycles based on prompted units for x
    #returns CE, VE, EE for all cycles as a function of cycle number and time
    stats = Cycle_stats(charging_df, discharging_df)

    #gets cycle numbers associated with a charge cycle
    cycle_num_ser = pd.unique(charging_df["Cycle_Index"].values.ravel())    
    cycle_num_list = cycle_num_ser.tolist()

    cycles_to_plot = []
    #list initialized which cycles will be plotted, will be appended to based on "cycles" list, which may be empty

    #determines which cyle numbers to plot
    if("" in cycles):   
        cycles_to_plot.append(cycle_num_list[0])
        cycles_to_plot.append(cycle_num_list[-1])
    else:
        cycles = list(map(int, cycles))    
        cycles_to_plot.extend(cycles)

    just_cycles, all_cycles = Voltage_Profiles(charging_df, discharging_df, cycles_to_plot, volt_prof_list, theo_cap)
#returns df of data for the cycles requested and all cycles
#turns them into csv 
    just_cycles.drop(["Data_Point","Date_Time", "ACR(Ohm)", "dV/dt(V/s)", "Internal_Resistance(Ohm)", "dQ/dV(Ah/V)", "Charge_Energy(Wh)", "Discharge_Energy(Wh)", "dV/dQ(V/Ah)"], inplace = True, axis =1)
    
    
    all_cycles.drop(["Data_Point","Date_Time", "ACR(Ohm)", "dV/dt(V/s)", "Internal_Resistance(Ohm)", "dQ/dV(Ah/V)", "Charge_Energy(Wh)", "Discharge_Energy(Wh)", "dV/dQ(V/Ah)"], inplace = True, axis =1)
    

    power_df = df1.query("Step_Index == @power_step")
    power_plots, max_power = power_SOC(power_df, SOC_list, SA)
    
    #makes plots of SOC v max discharge power density, current density vs discharge power density
    #returns dict of both data sets (all data, max data)
    #turns them into csv


    #all data is converted to organized data frames
    df_powerPlots = pd.DataFrame.from_dict(power_plots, orient = 'index' )
    df_powerPlots.columns = [f"Current Density (A/cm\u00b2)", f"Discharge Power Density (W/cm\u00b2)"]
    
    df_powerPlots.reset_index(inplace=True)
    df_powerPlots = df_powerPlots.rename(columns = {'index':'SOC (%)'})

    
    CD_Float = df_powerPlots.iloc[0, 1]
    CD_str = str(CD_Float)
    df_powerPlots.iloc[0, 1] = CD_str


    PD_Float = df_powerPlots.iloc[0, 2]
    PD_str = str(PD_Float)
    df_powerPlots.iloc[0, 2] = PD_str

    df_powerPlots[f"Current Density (A/cm\u00b2)"] = df_powerPlots[f"Current Density (A/cm\u00b2)"].str.split(',')
    df_powerPlots[f"Discharge Power Density (W/cm\u00b2)"] = df_powerPlots[f"Discharge Power Density (W/cm\u00b2)"].str.split(',')
    df_powerPlots = df_powerPlots.set_index(["SOC (%)"]).apply(pd.Series.explode).reset_index()
    df_powerPlots[f"Current Density (A/cm\u00b2)"] =  df_powerPlots[f"Current Density (A/cm\u00b2)"].str.replace(r'[][]', '', regex=True)
    df_powerPlots[f"Discharge Power Density (W/cm\u00b2)"] =  df_powerPlots[f"Discharge Power Density (W/cm\u00b2)"].str.replace(r'[][]', '', regex=True)
    
    df_powerPlots[f"Discharge Power Density (W/cm\u00b2)"] = df_powerPlots[f"Discharge Power Density (W/cm\u00b2)"].astype(str).astype(float)
    df_powerPlots[f"Current Density (A/cm\u00b2)"] = df_powerPlots[f"Current Density (A/cm\u00b2)"].astype(str).astype(float)
    

    df_maxPowerSOC = pd.DataFrame.from_dict(max_power, orient = 'index')
    df_maxPowerSOC.T.reset_index().T.reset_index(drop=True)
    df_maxPowerSOC.reset_index(inplace=True)
    df_maxPowerSOC = df_maxPowerSOC.rename(columns = {'index':'SOC (%)'})
    df_maxPowerSOC.rename(columns={0:"Maximum Discharge Power Density (W/cm\u00b2)"}, inplace = True)

    
    charged_OCP_df = df1.query("Step_Index == @OCP_step")  
    OCP_SOC_dict= {}  
    OCP_SOC_dict = OCP_SOC_workup(charged_OCP_df, SOC_list)

    #Makes dict of SOC:OCP, generates plot 
    df_OCP_SOC = pd.DataFrame.from_dict(OCP_SOC_dict, orient = 'index')
    df_OCP_SOC.reset_index(inplace=True)
    df_OCP_SOC = df_OCP_SOC.rename(columns = {'index':'SOC (%)'})
    df_OCP_SOC.rename(columns={0:"OCP (V)"}, inplace = True)
    

    
        
    #all dataframes are added to a single excel spread sheet under different sheets
    with pd.ExcelWriter("Arbin_Data_Workup.xlsx", mode = 'a') as writer:
        just_cycles.to_excel(writer, sheet_name= "Requested Cycles")
        all_cycles.to_excel(writer, sheet_name= "All_Cycles")
        df_powerPlots.to_excel(writer, sheet_name= "Power plot data")
        df_maxPowerSOC.to_excel(writer, sheet_name= "Max Power vs SOC")
        df_OCP_SOC.to_excel(writer, sheet_name= "SOC vs OCP")
        df_ASR_fin.to_excel(writer, sheet_name= "ASR")
        df_SOCs.to_excel(writer, sheet_name= "SOC List")

    


def ASR_calc(df, SA):
    ASR = 0
    
    #where voltage is greater than 1, plot V vs A
    df_ASR = df.loc[df["Voltage(V)"] > 1]
    df_ASR["Current Density (A/cm\u00b2)"] = df_ASR["Current(A)"] / SA

    CD = []
    V = []
    CD = df_ASR["Current Density (A/cm\u00b2)"].tolist()
    V = df_ASR["Voltage(V)"].tolist()
    plt.clf()

    plt.plot(V, CD)
    #calculate equation for trendline
    slope, int, r_value, p_value, std_err = scipy.stats.linregress(V, CD)
    r_squared = r_value**2
    R2 = f'{r_squared:.2f}'
    print(u"R\u00b2 = ", R2)
    Slope = f'{slope:.2E}'
    int = f'{int:.2E}'
    print(f"slope when greater than 1 V = {Slope}")
    plt.title('ASR')
    plt.xlabel("Cell Potential (V)")
    plt.ylabel(u'Current Density (A/cm\u00b2)')
    plt.savefig("ASR.jpg")
    plt.show()
    ASR = round(slope * SA, 2)
    print(f"ASR is {ASR} Ohm cm\u00b2")
    #ASR calulated based on trend line slope times SA
    return ASR

def Voltage_Profiles(chg, dchg, cycles, units, theo_cap):
    #getting cycles
    df_cycling = pd.concat([chg, dchg])
    df_cycles = df_cycling.loc[df_cycling["Cycle_Index"].isin(cycles)]
    df_chg_cyc = chg.loc[df_cycling["Cycle_Index"].isin(cycles)]
    df_dchg_cyc = dchg.loc[df_cycling["Cycle_Index"].isin(cycles)]
    #counts for color placement
    n = len(cycles)
    colors = plt.cm.jet(np.linspace(0,1,n))
    #choices for plotting based on x axis, changes by if statement. all plotted the same
    if("Negolyte Capacity (Ah)" in units):
        plt.clf() 
        for colorC, cycle in enumerate(cycles):
            chg_caps = []
            dchg_caps = []
            chg_V = []
            dchg_V = []
            #plots cycles individually to prevent restarting of data making lines
            chg_caps = df_chg_cyc.loc[df_chg_cyc["Cycle_Index"] == cycle, "Charge_Capacity(Ah)"].tolist()
            chg_V = df_chg_cyc.loc[df_chg_cyc["Cycle_Index"] == cycle, "Voltage(V)"].tolist()
            dchg_caps = df_dchg_cyc.loc[df_dchg_cyc["Cycle_Index"] == cycle, "Discharge_Capacity(Ah)"].tolist()
            dchg_V = df_dchg_cyc.loc[df_dchg_cyc["Cycle_Index"] == cycle, "Voltage(V)"].tolist()
            plt.plot(chg_caps, chg_V, c = colors[colorC], label = f"{cycle}")
            plt.plot(dchg_caps, dchg_V, c = colors[colorC])
        plt.legend(title = "Cycle Number", bbox_to_anchor=(1.05, 1.0), loc='upper left')
        plt.title("Negolyte Capacity (Ah) vs Cell Potential (V)")
        plt.ylabel("Cell Potential (V)")
        plt.xlabel("Negolyte Capacity (Ah)")
        plt.tight_layout()
        plt.savefig("Capacity_vs_Pot.jpg")
        plt.show()
    if("Time (s)" in units):
        plt.clf()
        for colorA, cycle in enumerate(cycles):
            chg_time = []
            dchg_time = []
            chg_V = []
            dchg_V = []
            #plots cycles individually to prevent restarting of data making lines
            chg_time = df_chg_cyc.loc[df_chg_cyc["Cycle_Index"] == cycle, "Step_Time(s)"].tolist()
            chg_V = df_chg_cyc.loc[df_chg_cyc["Cycle_Index"] == cycle, "Voltage(V)"].tolist()
            dchg_time = df_dchg_cyc.loc[df_dchg_cyc["Cycle_Index"] == cycle, "Step_Time(s)"].tolist()
            dchg_V = df_dchg_cyc.loc[df_dchg_cyc["Cycle_Index"] == cycle, "Voltage(V)"].tolist()
            plt.plot(chg_time, chg_V, c = colors[colorA], label = f"{cycle}")
            plt.plot(dchg_time, dchg_V, c = colors[colorA])

        plt.legend(title = "Cycle Number", bbox_to_anchor=(1.05, 1.0), loc='upper left')
        plt.title("Time (s) vs Cell Potential (V)")
        plt.ylabel("Cell Potential (V)")
        plt.xlabel("Time (s)")
        plt.tight_layout()
        plt.savefig("Time_s_vs_pot.jpg")
        plt.show()
    if("Time (h)" in units):
        plt.clf()

        for colorA, cycle in enumerate(cycles):
            chg_time_h = []
            dchg_time_h = []
            chg_time_s = []
            dchg_time_s = []
            chg_V = []
            dchg_V = []
            #plots cycles individually to prevent restarting of data making lines
            chg_time_s = df_chg_cyc.loc[df_chg_cyc["Cycle_Index"] == cycle, "Step_Time(s)"].tolist()
            chg_V = df_chg_cyc.loc[df_chg_cyc["Cycle_Index"] == cycle, "Voltage(V)"].tolist()
            dchg_time_s = df_dchg_cyc.loc[df_dchg_cyc["Cycle_Index"] == cycle, "Step_Time(s)"].tolist()
            dchg_V = df_dchg_cyc.loc[df_dchg_cyc["Cycle_Index"] == cycle, "Voltage(V)"].tolist()
            chg_time_h = [x/3600 for x in chg_time_s]
            dchg_time_h = [x/3600 for x in dchg_time_s]
            plt.plot(chg_time_h, chg_V, c = colors[colorA], label = f"{cycle}")
            plt.plot(dchg_time_h, dchg_V, c = colors[colorA])

        plt.legend(title = "Cycle Number", bbox_to_anchor=(1.05, 1.0), loc='upper left')
        plt.title("Time (h) vs Cell Potential (V)")
        plt.ylabel("Cell Potential (V)")
        plt.xlabel("Time (h)")
        plt.tight_layout()
        plt.savefig("Time_h_vs_Pot.jpg")
        plt.show()
    if("SOC (%)" in units):
        plt.clf() 
        for colorB, cycle in enumerate(cycles):
            chg_caps = []
            dchg_caps = []
            chg_V = []
            dchg_V = []
            #plots cycles individually to prevent restarting of data making lines
            chg_caps = df_chg_cyc.loc[df_chg_cyc["Cycle_Index"] == cycle, "Charge_Capacity(Ah)"].tolist()
            chg_V = df_chg_cyc.loc[df_chg_cyc["Cycle_Index"] == cycle, "Voltage(V)"].tolist()
            dchg_caps = df_dchg_cyc.loc[df_dchg_cyc["Cycle_Index"] == cycle, "Discharge_Capacity(Ah)"].tolist()
            dchg_V = df_dchg_cyc.loc[df_dchg_cyc["Cycle_Index"] == cycle, "Voltage(V)"].tolist()
            chg_SOC = [x/theo_cap*100 for x in chg_caps]
            dchg_SOC = [x/theo_cap*100 for x in dchg_caps]
            plt.plot(chg_SOC, chg_V, c = colors[colorB], label = f"{cycle}")
            plt.plot(dchg_SOC, dchg_V, c = colors[colorB])
        plt.legend(title = "Cycle Number", bbox_to_anchor=(1.05, 1.0), loc='upper left')
        plt.title("SOC (%) vs Cell Potential (V)")
        plt.ylabel("Cell Potential (V)")
        plt.xlabel("SOC (%)")
        plt.tight_layout()
        plt.savefig("SOC_vs_Pot.jpg")
        plt.show()
        #returns a data frame of the data for the asked for cycles and all cycles
    return df_cycles, df_cycling

def Cycle_stats(chg, dchg):
    #initialize needed vals
    CEavg, VEavg, EEavg, ChgVavg, DchgVavg = 0, 0, 0, 0 ,0
    cycleNum_stats = {}
    #makes list of cycle numbers
    cycle_num_ser = pd.unique(chg["Cycle_Index"].values.ravel())    
    cycle_num_list = cycle_num_ser.tolist()
    max_cycle = max(cycle_num_list)
    for cycle in cycle_num_list:
        charge_cap = []
        discharge_cap = []
        charge_V = []
        discharge_V = []

        #for each cycle, pull the max charge and discharge cap (Ah)
        charge_cap = chg.query("Cycle_Index == @cycle")["Charge_Capacity(Ah)"].tolist()
        discharge_cap = dchg.query("Cycle_Index == @cycle")["Discharge_Capacity(Ah)"].tolist()
        #max value of charge cap and discharge
        cycle_discap = round(max(discharge_cap), 2)
        cycle_cap = round(max(charge_cap), 2 )
        #gets CE
        CE = round(cycle_discap/ cycle_cap * 100, 1)

        #gets average charge and discharge voltages
        charge_V = chg.query("Cycle_Index == @cycle")["Voltage(V)"].tolist()
        discharge_V = dchg.query("Cycle_Index == @cycle")["Voltage(V)"].tolist()
        ChgVavg = round(mean(charge_V), 3)
        DchgVavg = round(mean(discharge_V), 3)

        #gets VE
        VE = round(DchgVavg / ChgVavg * 100, 1)

        #calcs EE

        EE = round(CE * VE /100, 1)
        #puts all values associated with each cycle into stats
        cycleNum_stats[f"Cycle Number {cycle}"] = CE, VE, EE, ChgVavg, DchgVavg, cycle_cap, cycle_discap
    #makes df with all values, adds mean
    df = pd.DataFrame(cycleNum_stats, index = ["Coulombic Efficiency (%)", "Voltaic Efficiency (%)", "Energy Efficiency (%)", "Average Charge Potential (V)", "Average Discharge Potential (V)", "Charge Capacity (Ah)", "Discharge Capacity (Ah)"])
    df['mean'] = df.mean(axis=1)
    dfT = df.transpose()

    #generates the excel sheet (because it is the first call) and writes the stats
    with pd.ExcelWriter("Arbin_Data_Workup.xlsx") as writer:
        dfT.to_excel(writer, sheet_name= "All Stats")
    
    plot_choice = ""
    plot_choice = input(f"\n\nWhat do you want to plot as a function of SOC? \n Type all that apply or all or none (Stats (CE, VE, EE), Avg Pots(chg/dis pts), or Capacities (Chg Cap, Dischg Cap)): ")
    plot_choice_list = plot_choice.split(", ")

    plt.clf()
   
    rows_needed = dfT.shape[0] -1
    #plotting of desired stats
    if "all" in plot_choice_list:
        for count, i in enumerate(range(rows_needed), 1):
            
            plt.scatter(count, dfT.iloc[i, 0], c = 'black', label = "CE")
            plt.scatter(count, dfT.iloc[i, 1], c = "red", label = "VE")
            plt.scatter(count, dfT.iloc[i, 2], c = "blue", label = "EE")
    #plots stats
        
        plt.title('Cycle Statistics')
        plt.xlabel("Cycle Number")
        plt.ylabel("Effiency (%)")
        plt.legend(["CE", "VE", "EE"], bbox_to_anchor=(1.05, 1.0), loc='upper left')
        plt.tight_layout()
        plt.savefig("CycleNum_vs_Efficiency.jpg")
        plt.show()

        #plots voltages
        for count, i in enumerate(range(rows_needed), 1):
            plt.scatter(count, dfT.iloc[i, 3], c = "black", label = "Avg Chg V")
            plt.scatter(count, dfT.iloc[i, 4], c = "red", label = "Avg Dischg V")        
            
    
        
        plt.title('Average Charge and Discharge Potentials')
        plt.xlabel("Cycle Number")
        plt.ylabel("Avg Cell Potential (V)")
        plt.legend(["Avg Chg (V)", "Avg Dischg (V)"], bbox_to_anchor=(1.05, 1.0), loc='upper left')
        plt.tight_layout()
        plt.savefig("CycleNum_vs_AvgPot.jpg")
        plt.show()

        #plots capacities
        for count, i in enumerate(range(rows_needed), 1):     
            plt.scatter(count, dfT.iloc[i, 5], c = "black", label = "Chg Cap")
            plt.scatter(count, dfT.iloc[i, 6], c = 'red', label = "Dchg Cap")
    
        
        plt.title('Cycle Capacity')
        plt.xlabel("Cycle Number")
        plt.ylabel("Cell Capacity (Ah)")
        plt.legend(["Chg Cap", "Discharge Cap"], bbox_to_anchor=(1.05, 1.0), loc='upper left')
        plt.tight_layout()
        plt.savefig("CycleNum_vs_Cap.jpg")
        plt.show()
    if "stats" in plot_choice_list:
        #plots stats
        
        plt.title('Cycle Statistics')
        plt.xlabel("Cycle Number")
        plt.ylabel("Effiency (%)")
        plt.legend(["CE", "VE", "EE"], bbox_to_anchor=(1.05, 1.0), loc='upper left')
        plt.tight_layout()
        plt.savefig("CycleNum_vs_Efficiency.jpg")
        plt.show()
    if "Avg Pots" in plot_choice_list:
          #plots voltages
        for count, i in enumerate(range(rows_needed), 1):
            plt.scatter(count, dfT.iloc[i, 3], c = "black", label = "Avg Chg V")
            plt.scatter(count, dfT.iloc[i, 4], c = "red", label = "Avg Dischg V")        
            
    
        
        plt.title('Average Charge and Discharge Potentials')
        plt.xlabel("Cycle Number")
        plt.ylabel("Avg Cell Potential (V)")
        plt.legend(["Avg Chg (V)", "Avg Dischg (V)"], bbox_to_anchor=(1.05, 1.0), loc='upper left')
        plt.tight_layout()
        plt.savefig("CycleNum_vs_AvgPot.jpg")
        plt.show()
    if "Capacities"in plot_choice_list:
        #plots capacities
        for count, i in enumerate(range(rows_needed), 1):     
            plt.scatter(count, dfT.iloc[i, 5], c = "black", label = "Chg Cap")
            plt.scatter(count, dfT.iloc[i, 6], c = 'red', label = "Dchg Cap")
    
        
        plt.title('Cycle Capacity')
        plt.xlabel("Cycle Number")
        plt.ylabel("Cell Capacity (Ah)")
        plt.legend(["Chg Cap", "Discharge Cap"], bbox_to_anchor=(1.05, 1.0), loc='upper left')
        plt.tight_layout()
        plt.savefig("CycleNum_vs_Cap.jpg")
        plt.show()

    #returns df of the data stats
    return df

def SOC_calc(df_charge, theo_cap):
    #finds each cycle
    cycle_num_ser = pd.unique(df_charge["Cycle_Index"].values.ravel())    
    cycle_num_list = cycle_num_ser.tolist()
    SOC_list =[]

    for cycle in cycle_num_list:
        charge_cap = []
        #for each cycle, pull the max charge cap
        charge_cap = df_charge.query("Cycle_Index == @cycle")["Charge_Capacity(Ah)"].tolist()
        #max value of charge cap

        cycle_cap = max(charge_cap)
        
        #calulate SOC as ratio cycle Ah / max Ah * 100, rounded to 1 decimal
        SOC = round((cycle_cap/theo_cap) * 100, 1)
        SOC_list.append(SOC)
    #returns list of SOC that cycle acheieved
    return SOC_list

def power_SOC(df_power, SOCs, SA):
    cycle_num_ser = pd.unique(df_power["Cycle_Index"].values.ravel())    
    cycle_num_list = cycle_num_ser.tolist()
    SOC_disPowerDen = {}
    SOC_maxDisPowerDen= {}
    
    #make power and current density columns
    df_power[u"Current Density (A/cm\u00b2)"] = df_power["Current(A)"]/SA*-1
    df_power[u"Discharge Power Density (W/cm\u00b2)"] = df_power[u"Current Density (A/cm\u00b2)"] * df_power["Voltage(V)"]
    
    for SOC_pos, cycle in enumerate(cycle_num_list):
        powerD = []
        currentD = []
        #for each cycle, pull the power and current d values into lists

        currentD = df_power.query("Cycle_Index == @cycle")[u"Current Density (A/cm\u00b2)"].tolist()
        powerD = df_power.query("Cycle_Index == @cycle")[u"Discharge Power Density (W/cm\u00b2)"].tolist()
        #max value of discharge power
        maxDPower = max(powerD)

        #dict of SOC:Max power dis
        SOC_maxDisPowerDen[SOCs[SOC_pos]] = maxDPower 

        #dict of SOC: currentD, PowerD
        SOC_disPowerDen[SOCs[SOC_pos]] = currentD, powerD

    #plotting SOC vs max
    plt.clf()
    lists = sorted(SOC_maxDisPowerDen.items()) # sorted by key, return a list of tuples

    x, y = zip(*lists) # unpack a list of pairs into two tuples
    xmax = max(x)
    ymax = max(y)
    plt.scatter(x, y)
    plt.title('SOC vs Maximum Discharge Power')
    plt.xlabel("Negolyte SOC (%)")
    plt.ylabel(u'Maximum Discharge Power (W/cm\u00b2)')
         
    plt.tight_layout()
    plt.savefig("SOC_vs_MaxPower.jpg")
    plt.show()
    print(f"Maximum discharge power density is {ymax} W/cm\u00b2 at {xmax} A/cm\u00b2")

    #plotting all power curves
    plt.clf()
    df = pd.DataFrame(SOC_disPowerDen)
    df2 = df.transpose()
    df2.columns=[u"Current Density (A/cm\u00b2)", u"Discharge Power Density (W/cm\u00b2)"]
    for count, i in enumerate(range(df2.shape[0])):
        plt.plot(df.iloc[0, i], df.iloc[1, i], label = SOCs[count])
        xmax = max(df.iloc[0, i]) - max(df.iloc[0, i]) * 0.1
        
        
    plt.title(u'Current Density (A/cm\u00b2) vs Discharge Power Density (W/cm\u00b2)')
    plt.xlabel(u"Current Density (A/cm\u00b2)")
    plt.ylabel(u'Discharge Power Density (W/cm\u00b2)')
    plt.legend(loc= "upper right", title = "SOC (%)")
    plt.tight_layout()
    plt.savefig("PowerPlots.jpg")
    plt.show()
    #return dicts of the power data to be plotted in origin as dict {SOC: [CD, PD]} and also the max values {SOC:max}
    return SOC_disPowerDen, SOC_maxDisPowerDen

def OCP_SOC_workup(df_OCP, SOCs):
    #gets cycles
    cycle_num_ser = pd.unique(df_OCP["Cycle_Index"].values.ravel())    
    cycle_num_list = cycle_num_ser.tolist()
    SOC_OCP = {}
    
    for SOC_pos, cycle in enumerate(cycle_num_list):
        
        voltages = df_OCP.query("Cycle_Index == @cycle")["Voltage(V)"]
        mean = voltages.mean()
        mean = round(mean, 2)
        #dict of SOC:OCP
        SOC_OCP[SOCs[SOC_pos]] = mean
    

    #gets lists of keys and values

    lists = sorted(SOC_OCP.items()) # sorted by key, return a list of tuples

    x, y = zip(*lists) # unpack a list of pairs into two tuples
    #plots SOC vs OCP
    plt.scatter(x, y)
    plt.title('SOC vs OCP')
    plt.xlabel("Negolyte SOC (%)")
    plt.ylabel('OCP (V)')
    plt.tight_layout()
    plt.savefig("SOC_vs_OCP.jpg")
    plt.show()
    #returns dict of {SOC:OCP}
    return SOC_OCP
        
def main():
    #gets variables needed for capacity/SOC
    conc = float(input(f"\n\nWhat is the concentration of the active species? (M): "))
    vol = float(input(f"\n\nWhat is the volume of the active species? (mL): "))
    num_e = float(input(f"\n\nHow many electrons are being transferred?: "))
    #file_type = input(f"\n\nWhat is your file extension? (e.g. xlsx, csv, etc.): ")
    file_type =".xlsx"
    #SA = 5
    SA = int(input(f"\n\nWhat is the SA of the electrode (in cm\u00b2): "))
    to_plot = input(f"\n\nWhat cycle numbers do you want plotted? \n By default, the first and last cycles will be plotted if no input is given. (e.g. 1, 5, 56): ")
    #to_plot = ""
    cycle_plot_list = to_plot.split(", ")

    volt_prof_unit = input(f"\n\nWhat x-axis do you want for your voltage profile? A graph will be made for each choice \n Choices are Time (s), Time (h), Negolyte Capacity (Ah/L), SOC (%): ")
    volt_prof_list = volt_prof_unit.split(", ")
    #volt_prof_list = "SOC (%)"

    if '.' in file_type:
        file_type = file_type[1:]

    #capacity calc for max theoretical for SOC
    mmol = conc * (vol/1000)
    
    max_cap_Ah = (num_e * mmol * (96485/3600))
    #Ah unit
    
    #gets files with type promt (XLSX is for excel)
    print(f"Collecting all .{file_type} files.")

    file_list = [i for i in glob.glob(f'*.{file_type}')]
    for file in file_list:
        if file[0:2] == "~$":
            file_list.remove(file)
        if file == "Arbin_Data_Workup.xlsx":
            file_list.remove(file)
    #remove unnecessary files
    remove_files = input(f"\n\nDo you need to remove files? (Y/N): ")
    remove_files = remove_files.upper()
    if remove_files == 'Y':
        to_remove = input(f"\n\nWhat files do you want to remove? (separate by \", \") (can be one or multiple) : ")
        remove_list = to_remove.split(", ")
        for each in remove_list:
            print("removing :", each)
            file_list.remove(each)
            print(each, " has been removed")
    print(f"The files to be plotted are: {file_list}")   

    #initial dict, run file reader using files
    
    for file in file_list:  
        file_reader(file, max_cap_Ah, SA, cycle_plot_list, volt_prof_list)  
    


if __name__ == '__main__':
    main()






