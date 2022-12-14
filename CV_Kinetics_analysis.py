#made by Scott Waters

import math
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import scipy
import glob

#pip installation needed for pandas matplotlib, numpy, scipy

#finds scan rate of individual file from metadata
def find_scan_rate(file_name):
    txt_file = open(file_name)
    for line in txt_file.readlines():
        if ("Scan Rate" in line):
            ListScan = line.split()
            scan_rate = float(ListScan[2])/1000
    txt_file.close()

    return scan_rate

#finds reduction and oxidation peak of CV for single electron transfers (based on min/max)
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
    
    return peaks


def process_files(file_list, Ru): 
    #returns {scan rate: peak, peak} 

    data = {}
    
    for file in file_list:
        f = open("temp.txt", 'w')
        df = pd.read_table(file, delimiter=",",on_bad_lines='error',  header=None)
        df.to_csv("temp.txt", header=None, index=None, sep='\t', mode='a')
        temp_scan = find_scan_rate("temp.txt")
        
        temp_peaks = get_peaks("temp.txt", Ru)
   
        data[temp_scan] = temp_peaks
        f.close()    

    return data

#used for finding linear fit
def objective(x, a, b):
	return a * x + b

def find_D_K(data_frame, conc, Eo, choice):
    #finds values from scan data
    
    #creates list with values of sqrt scan rate and adds to df
    sqrt_scan_rate_V = []
    for i in data_frame.index:
        sqrt_scan_rate_V.append(math.sqrt(i))
    data_frame["sqrt scan rate (V)"] = sqrt_scan_rate_V

    #adds E- Eo to DF
    data_frame["E - Eo (V) _ red"] = data_frame["reduction peak potential (V)"] - Eo
    data_frame["E - Eo (V) _ ox"] = data_frame["oxidation peak potential (V)"] - Eo
    #adds Ln(current (A)) to DF
    data_frame["Ln(current) (A) _ red"] = np.log(abs(data_frame["reduction peak current (A)"]))
    data_frame["Ln(current) (A) _ ox"] = np.log(abs(data_frame["oxidation peak current (A)"]))
    #adds current density to DF
    data_frame[u"reduction peak current density (A/cm\u00b2)"] = data_frame["reduction peak current (A)"] / 0.0707

    print("Finding Do")

    #Finds Do
    Do_x = data_frame["sqrt scan rate (V)"]
    Do_y = data_frame[u'reduction peak current density (A/cm\u00b2)']
    plt.scatter(Do_x, Do_y)
    #plots Do
    Do_slope, Do_int, r_value_Do, p_value_Do, std_err_Do = scipy.stats.linregress(Do_x, Do_y)
    r_squared = r_value_Do**2
    R2 = f'{r_squared:.2f}'
    print(u"R\u00b2 = ", R2)
    Slope_D = f'{Do_slope:.2E}'
    int_D = f'{Do_int:.2E}'
    
    print("slope =", Slope_D, " intercept = ", int_D)
    
    #Do math. conc is in M
    denomDo = float(299000*math.sqrt(0.5)*conc/1000)
    DoSlope = float(Do_slope)
    Do_red = (DoSlope / denomDo)**2
    #converstion to sci not. 
    Do_red_prnt = f'{Do_red:.2E}'
    #plot formatting
    plt.title(u'D\u2092')

    plt.xlabel("sqrt scan rate (V)")
    plt.ylabel(u'reduction peak current density (A/cm\u00b2)')

    #calculate equation for trendline
    z = np.polyfit(Do_x, Do_y, 1)
    p = np.poly1d(z)
    plt.plot(Do_x, p(Do_x))
    #add trendline to plot
    #plot size
    xmin, xmax, ymin, ymax = plt.axis()
    
    
    #plot text and addition
    plot_text = u'R\u00b2 = ' + R2 + " with line of y = " + Slope_D +"x + " +int_D
    
    plt.text(xmin, ymin, plot_text, fontsize =  12)

    plt.tight_layout()
    plt.savefig("Do_plot.png", bbox_inches='tight')

    plt.show()
    #saves plot
    
    Ko_red = ""
    Ko_ox  = ""
    Ko_red_prnt = ""
    Ko_ox_prnt = ""
    #which data to calculate
    if(choice == "red"):
        Ko_red = K0_red(data_frame, conc)
        Ko_red_prnt = f'{Ko_red:.2E}'
    elif(choice == "ox"):
        Ko_ox = K0_ox(data_frame, conc)
        Ko_ox_prnt = f'{Ko_ox:.2E}'
    elif(choice == "both"):
        Ko_red = K0_red(data_frame, conc)
        Ko_red_prnt = f'{Ko_red:.2E}'
        Ko_ox = K0_ox(data_frame, conc)
        Ko_ox_prnt = f'{Ko_ox:.2E}'
        
    #printing results based on need
    data_frame[u"Diffusion Coefficient (cm\u00b2 s-\u00b1)"] = Do_red
    if(choice == "red"):       
        print("Do = ", Do_red_prnt, ". K0_red = ", Ko_red_prnt)
        data_frame["Heterogeneous Electron Rate Transfer Constant (cm s^-1)"] = Ko_red
    elif(choice == "both"):
        print("Do = ", Do_red_prnt, ". K0_red = ", Ko_red_prnt, ". K0_ox = ", Ko_ox_prnt)
        data_frame["Heterogeneous Electron Rate Transfer Constant (red) (cm s^-1)"] = Ko_red
        data_frame["Heterogeneous Electron Rate Transfer Constant (ox) (cm s^-1)"] = Ko_ox
    else:
        print("Do = ", Do_red_prnt, ". K0_ox = ", Ko_ox_prnt)
        data_frame["Heterogeneous Electron Rate Transfer Constant (ox) (cm s^-1)"] = Ko_ox

    #returns saved data for export to CSV
    return data_frame

def K0_ox(data, conc):
    print("Finding Ko of oxidation")
    #Finds Ko of oxidation
    Ko_x_ox = data["E - Eo (V) _ ox"]
    Ko_y_ox = data["Ln(current) (A) _ ox"]
    #plots data
    
    #save slope, int, r_value, p_value (not used), Std err (not used). 
    Ko_slope, Ko_int, r_value, p_value_Ko_ox, std_err_Ko_ox = scipy.stats.linregress(Ko_x_ox, Ko_y_ox)
    r_squared = r_value**2
    R2_Ko_ox = f'{r_squared:.2f}'
    print(u"R\u00b2 = ", R2_Ko_ox)
    Slope_K_ox = f'{Ko_slope:.2E}'
    int_K_ox = f'{Ko_int:.2E}'
        
    print("slope =", Slope_K_ox, " intercept = ", int_K_ox)
    
        #Ko math
    denom = float(0.227*964800*0.0707*conc/1000)
    Ko_ox_intFloat = float(int_K_ox)
    Ko_ox = float(math.exp(Ko_ox_intFloat) / denom)
        #putting into scientific notation
    plt.scatter(Ko_x_ox, Ko_y_ox)
    plt.title('Ko_ox')
    plt.xlabel("E - Eo (V) _ ox")
    plt.ylabel('Ln(current) (A) _ ox')
    #calculate equation for trendline
    z = np.polyfit(Ko_x_ox, Ko_y_ox, 1)
    p = np.poly1d(z)
    #add trendline to plot
    plt.plot(Ko_x_ox, p(Ko_x_ox))

    plot_text = u'R\u00b2 = ' + R2_Ko_ox + " with line of y = " + Slope_K_ox +"x + " +int_K_ox
    xmin, xmax, ymin, ymax = plt.axis()
    plt.text(xmin, ymin, plot_text, fontsize =  12)
    plt.tight_layout()
    plt.savefig("Ko_ox_plot.png", bbox_inches='tight')
    plt.show()
        
    
    
    return Ko_ox

def K0_red(data, conc):
    print("Finding Ko of reduction")
        #Finds Ko
    Ko_x = data["E - Eo (V) _ red"]
    Ko_y = data["Ln(current) (A) _ red"]

    plt.scatter(Ko_x, Ko_y)

    #save slope, int, r_value, p_value (not used), Std err (not used). 
    Ko_slope, Ko_int, r_value, p_value_Ko, std_err_Ko = scipy.stats.linregress(Ko_x, Ko_y)

    r_squared = r_value**2
    R2 = f'{r_squared:.2f}'
    print(u"R\u00b2 = ", R2)
    print("slope =", Ko_slope, " intercept = ", Ko_int)

    #Ko math
    Ko_red_denom = float(0.227*964800*0.0707 *conc / 100000)
    Ko_int_float = float(Ko_int)
    Ko_red = math.exp(Ko_int_float) / Ko_red_denom
    #putting into scientific notation

    plt.title('Ko_red')
    plt.xlabel("E - Eo (V) _ red")
    plt.ylabel('Ln(current) (A) _ red')
    #calculate equation for trendline
    z = np.polyfit(Ko_x, Ko_y, 1)
    p = np.poly1d(z)
    #add trendline to plot
    plt.plot(Ko_x, p(Ko_x))

    plot_text = u'R\u00b2 = ' + str(R2) + " with line of y = " + str(Ko_slope) +"x + " + str(Ko_int)
    xmin, xmax, ymin, ymax = plt.axis()
    plt.text(xmin, ymin, plot_text, fontsize =  12)
    plt.tight_layout()
    plt.savefig("Ko_red_plot.png", bbox_inches='tight')
    plt.show()
    
    return Ko_red



def main():
    #prompt for required constants
    E0 = float(input("What is the E0 (vs Ag/AgCl) of the species? (in Volts): "))
    Ru = float(input("Assuming the Ru has not been fixed, what is the internal resistance (getRU) value of the experiment? (in Ohms): "))
    conc = float(input("What is the concentration of the solution? (in M): "))
    choice = input("Do you want kinetic constant values for reduction, oxidation, or both? (red/ox/both): ")
    if (choice == "red" or choice == "ox" or choice == "both"):
        
        #pull .dta files
        print("Pulling the .DTA files in this directory")
        file_list = [i for i in glob.glob('*.dta')]
    
        #option to remove files (useful if one scan is awful)
        remove_files = input("Do you need to remove files? (Y/N): ")
        remove_files = remove_files.upper()
        if remove_files == 'Y':
            to_remove = input("What files do you want to remove? (separate by \", \") (can be one or multiple) : ")
            remove_list = to_remove.split(", ")
            for each in remove_list:
                print("removing :", each)
                file_list.remove(each)
                print(each, " has been removed")
        
        data_points = process_files(file_list, Ru)
        #returns data of scan and peaks

        #gets dict with scan rates and peak values
        all_data_df = pd.DataFrame.from_dict(data_points, orient = "index")

        #finds diffusion coeff and choice of K (ox or red or both). Returns as dataframe
        final_df = find_D_K(all_data_df, conc, E0, choice)

        #adds constants to DF
        final_df["Internal Resistance (Ohms)"] = Ru
        final_df["Concentration [M]"] = conc
        final_df["E0 of species"] = E0

        #converts final dataframe with all data to a CSV
        final_df.to_csv("final_df.csv")
        print("FINAL_DF_DoFiles.CSV generated")

    #catch all for invalid choice
    else: 
        print("invalid choice, please restart")
        exit()


if __name__ == "__main__":
    main()






















