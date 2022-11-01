#created by Scott Waters
#need to pip install pandas and matplotlib
import pandas as pd
import matplotlib.pyplot as plt
import glob

#determines if scans are initiated with reduction or oxidation by comparing starting position and first step position
#returns scan rate
def find_scan_rate_direction(file_name):
    txt_file = open(file_name)
    init, next = 0, 0
    for line in txt_file.readlines():
        if ("Scan Rate" in line):
            ListScan = line.split()
            scan_rate = float(ListScan[2])/1000
        if ("Initial E" in line):
            ListDirInit = line.split()
            init = float(ListDirInit[2])
        if ("Scan Limit 1" in line):
            ListNext = line.split()
            next = float(ListNext[2])
    txt_file.close()

    return scan_rate, init, next

#finds peaks of Ru corrected values
def get_peaks(file_name, Ru):

    txt_file = open(file_name)
    Voltage = []
    Current = []
    #finds all voltages and currents and puts them into lists
    for line in txt_file.readlines(): 
        if ("\"\t" in line and "#" not in line and "Pt" not in line):
            ListVal = line.split()
            Voltage.append(ListVal[3])
            Current.append(ListVal[4])
    txt_file.close()
    
    #converts lists of str to floats
    Voltage = list(map(float, Voltage))
    Current = list(map(float, Current))
    CurrentD = []
    for i in range(len(Current)):
        CurrentD.append(Current[i]/0.0707)
    
    #corrects for GetRU experiment, allows for 0 ohm Ru
    Voltage_corrected = [] 
    if(Ru == 0):
        Voltage_corrected = Voltage
    else:
        for i in range(len(Voltage)):
            Voltage_corrected.append(Voltage[i] - (Current[i] * Ru))
   
    #finds max/min current
    max_A = max(Current)
    min_A = min(Current)
    #finds the index of the max/min values
    max_A_ind = Current.index(max_A)
    min_A_ind = Current.index(min_A)
    #finds the voltage at the corresponding max. index
    max_V = Voltage_corrected[max_A_ind]
    min_V = Voltage_corrected[min_A_ind]
    #creates dict of peaks
    peaks = {'reduction peak current (A)': min_A, 'reduction peak potential (V)':  min_V,
             'oxidation peak current (A)': max_A, 'oxidation peak potential (V)': max_V}

    return peaks, Voltage_corrected, CurrentD


def process_files(file_list, Ru, conc): 
    #returns {scan rate: peak, peak} 

    data = {}
    
    for file in file_list:
        f = open("temp.txt", 'w')
        initial, end = 0, 0
        
        df = pd.read_table(file, delimiter=",",on_bad_lines='error',  header=None)
        df.to_csv("temp.txt", header=None, index=None, sep='\t', mode='a')
        temp_scan, initial, end = find_scan_rate_direction("temp.txt")
        
        temp_peaks, temp_voltage, temp_currentD = get_peaks("temp.txt", Ru)
        make_plots(temp_voltage, temp_currentD, temp_scan, conc, initial, end)
        data[temp_scan] = temp_peaks
        f.close()    

    return data


def find_Ehalf(data_frame):
    #finds E1/2 values from scan data
    
    
    data_frame["E 1/2"] = data_frame[["reduction peak potential (V)", "oxidation peak potential (V)"]].mean(axis=1)
    #adds current density to DF
    data_frame["reduction peak current density (A/cm^2)"] = data_frame["reduction peak current (A)"] / 0.0707
    data_frame["oxidation peak current density (A/cm^2"] = data_frame["oxidation peak current (A)"] / 0.0707

    #returns saved data for export to CSV
    return data_frame

def make_plots(voltage, currentD, scan_rate, conc, zero, step):
#makes plot with title of scan rate and saves as jpg
    print ("plot made")
    x = voltage
    y = currentD

    plt.plot(x, y)
    pltname = str(round(scan_rate, 2)) + " V/s, " + str(conc) + " M"
    file_name = str(round(scan_rate, 2)) + "_Vs_" + str(conc) + "_plot.png"
    plt.title(pltname)
    plt.xlabel("Potential (V vs Ag/AgCl)")
    plt.ylabel(u'Current Density (A/cm\u00b2)')
    #calculate equation for trendline
    maxA = max(currentD)
    minA = min(currentD)
    maxV = max(voltage)
    minV = min(voltage)
    
    scan_dir = ""
    if(zero > step):
        scan_dir = "Sweeping negative"
    elif(zero < step):
        scan_dir = "Sweeping positive"
    E1_2 = (maxV - minV) / 2
    plt.text(E1_2, minA, scan_dir, fontsize = 12)
    plt.show()  
    plt.savefig(file_name)

#prompt for necessary constants
Ru = float(input("Assuming the Ru has not been fixed, what is the internal resistance (getRU) value of the experiment? (in Ohms): "))
conc = float(input("What is the concentration of the solution? (in mol): "))

    
#pull .dta files
print("Pulling the .DTA files in this directory")
file_list = [i for i in glob.glob('*.dta')]
   
#returns key: scan rate (V/s) with val: current (A), voltage (V)
remove_files = input("Do you need to remove files? (Y/N): ")
remove_files = remove_files.upper()
if remove_files == 'Y':
    to_remove = input("What files do you want to remove? (separate by \", \") (can be one or multiple) : ")
    remove_list = to_remove.split(", ")
    for each in remove_list:
        print("removing :", each)
        file_list.remove(each)
        print(each, " has been removed")
    
data_points = process_files(file_list, Ru, conc)


    #gets dict with scan rates and peak values
all_data_df = pd.DataFrame.from_dict(data_points, orient = "index")

    #finds diffusion coeff and choice of K (ox or red or both). Returns as dataframe
final_df = find_Ehalf(all_data_df)

    #adds constants to DF
final_df["Internal Resistance (Ohms)"] = Ru
final_df["Concentration [M]"] = conc


    #converts final dataframe with all data to a CSV
final_df.to_csv("final_df_CVs.csv")
print("FINAL_DF_CVs.CSV generated")















































