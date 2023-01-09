#created by Scott Waters
#need to pip install the below imported libraries
import pandas as pd
import matplotlib.pyplot as plt
import glob
from galvani import BioLogic as BL
import numpy as np
from statistics import mean
from scipy.signal import argrelextrema
import openpyxl
from openpyxl import Workbook




#finds peaks of Ru corrected values, assigns to dict with scan rate(sr) {sr: [peaks], [], [], []}
def get_peaks(df):

   #find local min and max
    x = df[f"Potential (V vs Fc/Fc\u207A)"].tolist()
    y = df["I/mA"].tolist()
    #initiate storage
    red_peak_xlist = []
    red_peak_ylist = []
    ox_peak_xlist = []
    ox_peak_ylist = []
    
    #find the ends of the cycles
    xmax = max(x)
    ind_max_x = x.index(xmax)
    xmin = min(x)
    ind_min_x = x.index(xmin)

    #find local peaks
    ox_peaks = argrelextrema(np.array(y), np.greater, 0, 200, "wrap")
    red_peaks = argrelextrema(np.array(y), np.less, 0, 200)
    red_list = list(red_peaks)
    lists = list(ox_peaks)
    #makes sure local peaks are not end points
    for val in lists:
        breaker = val.tolist()
        for i in breaker:
            c1 = i - 50
            c2 = i + 50

            if c1 < ind_max_x > c2:
                breaker.remove(i)

        ox_peak_xlist.append(x[i])
        ox_peak_ylist.append(y[i])


    for val in red_list:
        breaker_R = val.tolist()

        for j in breaker_R:
            c1 = j - 10
            c2 = j + 10

            if c1 > ind_min_x < c2:
                breaker_R.remove(j)
        red_peak_xlist.append(x[j])
        red_peak_ylist.append(y[j])
       
            #returns lists that get put into dict of the scan rate
    return ox_peak_xlist, ox_peak_ylist, red_peak_xlist, red_peak_ylist


def make_ind_plots():
    xls = pd.ExcelFile('CV_Data_Workup.xlsx')
    sheet_list = []
    sheet_list = xls.sheet_names
#check if the sheet is cycling data
    for sheet in sheet_list:
        if "mVs" in sheet and "2nd" not in sheet:
            df = pd.read_excel(xls, sheet_name=sheet)
#makes plot with title of scan rate and saves as jpg
            CycleStepSer =  pd.unique(df["cycle number"].values.ravel())
            CycleStepList = CycleStepSer.tolist()

            direction = ""

            df["V_diff (V)"] = df["Ewe/V"].diff()
            
            df["Current_diff (mA)"] = df["I/mA"].diff()

            Vlist = df["V_diff (V)"].tolist()
            Vlist = list(map(float, Vlist))

            #get scan direction
            Vi = Vlist[1:11]
            i_dV = mean(Vi)
            if(i_dV > 0):
                direction = "oxidizing sweep"
            elif(i_dV < 0):
                direction = "reducing sweep"

            n = len(CycleStepList)
            colors = plt.cm.jet(np.linspace(0,1,n))
            plt.clf()
            #data = {}


            for count, cycle in enumerate(CycleStepList, 1):
                temp = df.loc[df["cycle number"] == cycle]
                x = temp[f"Potential (V vs Fc/Fc\u207A)"].tolist()
                y = temp["I/mA"].tolist()
                mV_s = []
                # xmax = max(x)
                # ind_max_x = x.index(xmax)
                # xmin = min(x)
                #ind_min_x = x.index(xmin)


            # #find local min and max, adds to plot as colored dots. Removed because unnecessary and causes slow down

            #     ox_peaks = argrelextrema(np.array(y), np.greater, 0, 200, "wrap")
            #     red_peaks = argrelextrema(np.array(y), np.less, 0, 200)
            #     red_list = list(red_peaks)

            #     lists = list(ox_peaks)
            #     for val in lists:
            #         breaker = val.tolist()
            #         for i in breaker:
            #             c1 = i - 50
            #             c2 = i + 50

            #             if c1 < ind_max_x > c2:
            #                 breaker.remove(i)
            #         plt.scatter(x[i], y[i], c = "green")

            #     for val in red_list:
            #         breaker_R = val.tolist()

            #         for j in breaker_R:
            #             c1 = j - 10
            #             c2 = j + 10

            #             if c1 > ind_min_x < c2:
            #                 breaker_R.remove(j)
            #         plt.scatter(x[j], y[j], c = "red")


                plt.plot(x, y,  c= colors[count-1], label = f"Cycle {count}")

            #get scan rate by finding voltage where time = 1 s, compares to first point. ind = index
            


            # #saving data for overlays
            # all_x = df[f"Potential (V vs Fc/Fc\u207A)"].tolist()
            # all_y = df["I/mA"].tolist()
            # data[mV_s] = all_x, all_y
            plt.xlabel(f"Potential (V vs Fc/Fc\u207A)")
            plt.ylabel("Current (mA)")
            ymin = min(y)
            xavg = mean(x)
            plt.text(xavg + 0.1, ymin, direction, fontsize = 12)
            mV_s = sheet.split()

        
            plt.title(f"{mV_s[0]} mV/s")
            plt.legend()
            plt.tight_layout()
            plt.show()
            


def make_over(): #makes overlaid plot

    plt.clf()
    #open xlsx, gets the sheets corresponding to the second cycles
    xls = pd.ExcelFile('CV_Data_Workup.xlsx')
    list_names = xls.sheet_names
    list_2C = []
    
    for sheet in list_names:
        legend_entry = []
        legend_entry = sheet.split()
        if "2nd" in legend_entry:
            list_2C.append(sheet)
       
    list_2C_sorted = sorted(list_2C)
        
    #sheet converted to DF
    for sheet in list_2C_sorted:
        df1 = pd.read_excel(xls, sheet)
        #DF added to plots X, Y with legend entry based on sheet name
        legend_entry = []
        legend_entry = sheet.split()
        x = df1[f"Potential (V vs Fc/Fc\u207A)"].tolist()
        y = df1["I/mA"].tolist()
        #plots, but does not show
        plt.plot(x, y, label = f"{legend_entry[0]} mV/s" )
    
    #plot details
    plt.title("overlaid")
    plt.xlabel(f"Potential (V vs Fc/Fc\u207A)")
    plt.ylabel("Current (mA)")
    plt.legend()
    plt.tight_layout()
    plt.show()


#used to get ferrocene E1/2 used for future scan reference potential
def get_fc(file, Ru):
    E12 = 0
    df = pd.read_csv(file)
    if(Ru != 0):
        df["Voltage Corrected"] = df["Ewe/V"] - (df["I/mA"] * Ru)
        V =  df["Voltage Corrected"].tolist()
    else:
        V = df["Ewe/V"].tolist()
    A =  df["I/mA"].tolist()
    max_A = A.index(max(A))
    min_A = A.index(min(A))
    V_peaks = []
    V_peaks.append(V[max_A])
    V_peaks.append(V[min_A])
    E12 = mean(V_peaks)
    return E12

def main():

#     #prompt for necessary constants
    Ru = float(input("\n\nAssuming the internal resistance has not been fixed, what is the value? (in Ohms) (Enter 0 if not needed): "))

        #pull .mpr files
    print("\n\n\nPulling the .mpr files in this directory\n\n\n")
    file_list = [i for i in glob.glob('*.mpr')]
    plots = input("\n\n\nDo you want to make plots? (Y/N): ")
    plots = plots.lower()
    choice = ""
    if plots == "y":
        choice = input("\n\n\nDo you want to make individual plots, overlaid plots or both? (ind, over, both): ")
        choice = choice.lower()
    ferroceneFile = ""
    peaks = {}
    #convert mpr to csv
    for file in file_list:
        mpr = BL.MPRfile(file)
        df = pd.DataFrame(mpr.data)
        file_name = file[0:-4]
        df.to_csv(f"{file_name}.csv")


    #pull csv files, find the ferrocene ref
    csv_list = [i for i in glob.glob('*.csv')]

    for csv in csv_list:
        file_L = csv.lower()
        if ("ferrocene" in file_L or "fc" in file_L):
            ferroceneFile = csv
            csv_list.remove(csv)
        if(csv == "Peak_data.csv"):
            csv_list.remove(csv)

    print (f"\n\n\n.mpr files to be plotted are {file_list}.\n\n\nThe ferrocene reference file is {ferroceneFile}\n\n\n")
    
    reference_pot = get_fc(ferroceneFile, Ru)

    #initialize workbook
    wb = Workbook()
    wb.save("CV_Data_Workup.xlsx")
    
   
        #for each csv file, runs plotting and peak finding
    for csv in csv_list:
        time = []
        mV_s_label =""
        mV_s_label_2 = ""
        scan_rate = 0
        df1 = pd.read_csv(csv)
        df2 = df1[["time/s", "Ewe/V", "I/mA", "cycle number", '(Q-Qo)/C']].copy()

        #correct voltage for internal resistance

        if(Ru != 0):
            df2["Voltage Corrected"] = df2["Ewe/V"] - (df2["I/mA"] * Ru/1000)
            df2[f"Potential (V vs Fc/Fc\u207A)"] =  df2["Voltage Corrected"] - reference_pot
        else:
            df2[f"Potential (V vs Fc/Fc\u207A)"] =  df2["Ewe/V"] - reference_pot
      
        
        df2[f"Current Density (mA/cm\u00B2)"] = df["I/mA"] / 0.0707
        
        #determine scan rate by finding where time equals 1s
        time = df2["time/s"].tolist()
        formatted_time = [ '%.2f' % elem for elem in time ]
        idx1 = formatted_time.index('1.00')      
        V_at_1s = df2.loc[idx1]["Ewe/V"]
        inital_V = df2.loc[0]["Ewe/V"]
        

        scan_rate = abs(round(V_at_1s - inital_V, 2) * 1000)

        #formating final df of scan parameters
        df3 = df2[['Potential (V vs Fc/Fc⁺)','I/mA', 'Current Density (mA/cm²)', 'time/s', 'cycle number', '(Q-Qo)/C','Ewe/V']].copy()
        df_cycle2only = df3.loc[df3["cycle number"] == 2]
        
        #makes sheet labels for excel doc
        mV_s_label = f"{scan_rate} mVs"
        mV_s_label_2 = f"{scan_rate} mVs 2nd"      
        
        #get peaks from the second cycle of scanrate
        peaks[scan_rate] = get_peaks(df_cycle2only)

        #move all dfs to excel sheet
        with pd.ExcelWriter("CV_Data_Workup.xlsx", mode="a") as writer:
            df3.to_excel(writer, sheet_name= mV_s_label)
            df_cycle2only.to_excel(writer, sheet_name= mV_s_label_2)
        
        print(f"Scan rate {scan_rate} data added.")
    #end csv for loop
    
    if choice == "ind":
        make_ind_plots()
    elif choice == "over":
        make_over()
    elif choice == "both":
        make_ind_plots()
        make_over()


    temp_df = pd.DataFrame.from_dict(peaks, orient = 'index')

    temp_df.columns = ["Oxidation Peak Potential (V vs Fc/Fc\u207A)", "Oxidation Peak Current (mA)", f"Reduction Peak Potential (V vs Fc/Fc\u207A)", "Reduction Peak Current (mA)"]
    temp_df.reset_index(inplace=True)
    temp_df = temp_df.rename(columns = {'index':'Scan Rate (mV/s)'})

    
    ox_peak_A = temp_df.iloc[0, 2]
    red_peak_A = temp_df.iloc[0, 4]


    #converts lists to floats for peak data
    if len(ox_peak_A) == 1:
        temp_df["Oxidation Peak Current (mA)"] = pd.DataFrame([x for x in temp_df["Oxidation Peak Current (mA)"]])
        temp_df[f"Oxidation Peak Potential (V vs Fc/Fc\u207A)"] = pd.DataFrame([x for x in temp_df[f"Oxidation Peak Potential (V vs Fc/Fc\u207A)"]])
    else:
        temp_df.explode("Oxidation Peak Current (mA)", ignore_index=True)
        temp_df.explode(f"Oxidation Peak Potential (V vs Fc/Fc\u207A)", ignore_index=True)
       
     
    if len(red_peak_A) == 1:
        temp_df["Reduction Peak Current (mA)"] = pd.DataFrame([x for x in temp_df["Reduction Peak Current (mA)"]])
        temp_df[f"Reduction Peak Potential (V vs Fc/Fc\u207A)"] = pd.DataFrame([x for x in temp_df[f"Reduction Peak Potential (V vs Fc/Fc\u207A)"]])
    else:
        temp_df.explode("Reduction Peak Current (mA)", ignore_index=True)
        temp_df.explode(f"Reduction Peak Potential (V vs Fc/Fc\u207A)", ignore_index=True)
    final_df = temp_df.sort_values("Scan Rate (mV/s)")
    #puts peak data into one excel file with multiple sheets
    with pd.ExcelWriter("CV_Data_Workup.xlsx", mode = 'a') as writer:
        final_df.to_excel(writer, sheet_name= "Peak Data")
    workbook1 = openpyxl.load_workbook("CV_Data_Workup.xlsx")
    del workbook1["Sheet"]
    workbook1.save("CV_Data_Workup.xlsx")

    
    
        

if __name__ == "__main__":
     main()
     print("Job Finished")


























