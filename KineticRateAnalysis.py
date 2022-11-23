#Created by Scott Waters
import pandas as pd
import numpy as np
import glob
import matplotlib.pyplot as plt
import scipy

#To use: copy .csv files needed to directory. Run script. Provide wavelength, molar
#absorbtivities, cuvette length

#outputs: data for all kinetics scans at each wavelength for each file "data_filename"
#         "Kinetics_Final_Data.csv" which has the rate order for each specific file 
#           and wavelength
def main():
    #input of user-defined values
    wls = input("What wavelength(s) do you want to look at? If multiple, separate by \", \": ")
    molar_abs = input("What is the molar absorbance of your peak(s), in the same order separated by \", \", (e.g. 1, 50, 10000): ")
    pathL = float(input("What is the path length of cuvette (in cm)?: "))
    molar_abs_list = molar_abs.split(", ")
    molar_abs_list = list(map(float, molar_abs_list))
    
    wls_list = wls.split(", ")
    wls_list = list(map(int, wls_list))
    #makes sure each nm has a molar abs
    if len(molar_abs_list) != len(wls_list):
        exit()
    else:
        final_dict = {}
        #pull .CSV files
        print("Pulling the .CSV files in this directory")
        file_list = [i for i in glob.glob('*.csv')]
        
        for file in file_list:

            file_name = ""
            file_name = str(file)

            if file_name[0:5] == "data_":
                file_list.remove(file_name)
            if file_name[0:4] == "data":
                file_list.remove(file_name)
            elif file_name[0:5] == "temp_":
                file_list.remove(file_name)
                
            elif file_name == 'Kinetics_Final_Data.csv':
                file_list.remove(file_name)

        print(f"new file list {file_list}")

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
        print("The files to be plotted are: ", file_list)  
    #makes runs the program for each file. makes a dict of final answers
        for file in file_list:
            temp_dict = {}
            temp_dict = data_gather(file, wls_list, molar_abs_list, pathL) 
            final_dict[file] = temp_dict
   #here to next comments are formatting and cleaning output csv
    df_final = pd.DataFrame.from_dict({(i,j):final_dict[i][j] 
                           for i in final_dict.keys() 
                           for j in final_dict[i].keys()},
                       orient='index')
    df_final = df_final.iloc[1: , :]
    df_final.to_csv("temp_kin_fin.csv")

    df_final_fix = pd.read_csv("temp_kin_fin.csv")
    
    df_final_fix.columns = ["File, Wavelength (nm)", "Order"]
    new = df_final_fix["File, Wavelength (nm)"].str.split(" ", n = 1, expand = True)
    
    df_final_fix['File'] = new[0]
    df_final_fix["Wavelength (nm)"] = new[1]
    df_final_fix.drop(columns =["File, Wavelength (nm)"], inplace = True)
    df_final_fix['File'] =  df_final_fix['File'].map(lambda x: x.lstrip('(\'').rstrip('\','))
    df_final_fix["Wavelength (nm)"] =  df_final_fix["Wavelength (nm)"].map(lambda x: x.rstrip(')'))
    #formatted/cleaned
    #final output
    df_final_fix.to_csv("Kinetics_Final_Data.csv")

    
            
def data_gather(file, wls, mlr_abs, pathL):
    
    
    df = pd.read_csv(file, nrows=402)
    df2 = pd.read_csv(file, nrows=1400)
        
    with open("temp_txt.txt", 'w') as f:
        dfAsString = df2.to_string(header=False, index=False)
        f.write(dfAsString)
    with open("temp_txt.txt", 'r') as f:
        for i in f:
            if "Cycle Time(min)" in i:
                list_cycle_time = i.split()
                    #when found, splits the line into parts. All the data included here was separated by space (which is split() default)
                cycle_start = float(list_cycle_time[2]) * 60
                cycle_end = float(list_cycle_time[3]) * 60
                
            if "End Time(min)" in i:
                list_end_time = i.split()
                    #when found, splits the line into parts. All the data included here was separated by space (which is split() default)
                end1 = float(list_end_time[2]) * 60
                end2 = float(list_end_time[3]) * 60
                
                break

    scan_num_i = end1 / cycle_start  #initial scan numbers
    scan_num_b = round((end2 - end1) / cycle_end) #bulk scan numbers

    #removes the sample name from header
    df.rename(columns=df.iloc[0], inplace = True)
    df.drop([0], inplace = True)      

    #converts string nums to floats
    df = df.applymap(lambda x : pd.to_numeric(x,errors='ignore'))
    #converts to float, rounds to int
    df["Wavelength (nm)"] = df["Wavelength (nm)"].round(0).astype(int)
    #makes a single column df to find row index of needed nms
    df3 = df.iloc[:, :1]
    idx_list_i = []
    #finds index of nms, puts in list
    
    for nm in wls:
       
        #checks if nm was collected
        if (nm in df3["Wavelength (nm)"].values):
            #finds index of nm
            idx = df3.loc[df3["Wavelength (nm)"] == nm].index[0]
            idx_list_i.append(idx)
        else:
            
            wls.remove(nm)

    #find all abs of the needed nm as function of time. returns dict of dict nm: {time, abs}
    #e.g. {600 nm : {1 s : 0.05 abs}}
    nm_time_conc = {}

    key_count = len(list(df))
    
    #abs starts at 1, goes every other
    #enumerate of length of key count to know how many values. check if it is a initial
    #or bulk scan and multiply. Sum the times.
    
    
    for count, row in enumerate(idx_list_i):
        #loop for each nm
        time = 0 #keeps track of the time of scan taken
        temp_time_conc = {}  

        nm_check = wls[count]  #tracks nm  
        molar_abs_check = mlr_abs[count] #track molar abs
        for scan_num, col in enumerate(range(1, key_count, 2)):
            #loop for each abs col, keeps count of the # of scan
            abs = df.iloc[row, col] #gets the abs of the column
            conc = abs / (molar_abs_check *pathL)
            if (scan_num < scan_num_i): 
                #checks how much time to add based on initial or bulk scans
                time += cycle_start
            else: 
                time += cycle_end
            #initialize data
            data_list = []
            #inner dict is time(s):abs
            temp_time_conc[time] = conc
            #add dict to list
            data_list.append(temp_time_conc)
        #adds nm: [:]
        nm_time_conc[nm_check] = data_list

    
        #forms data frame Wavelength | time | abs
    df4 = pd.concat({k: pd.DataFrame(v).T for k, v in nm_time_conc.items()}, axis=0)
   
    df4.to_csv("temp_kin_csv")

    df_total = pd.read_csv("temp_kin_csv")
    df_total.columns = ["Wavelength (nm)", "Time (s)", "Concentration (M)"]

    #add columns for conc., 1/conc, ln[A]
    #1st = [] vs time | 2nd = ln[A] vs time | 3rd = 1/[] vs time
    df_total["ln[A]"] = np.log(df_total["Concentration (M)"])
    df_total["1/[A]"] = 1 / df_total["Concentration (M)"]
    df_total.to_csv(f"data_{file}")
    print(f"file is {file}")
    return data_plotter(df_total, wls)
                
                
def data_plotter(data_dict, wls):
    data = {}
    for nm in wls:
        #make df of individual wavelengths
        ind_nm = data_dict.query(" `Wavelength (nm)` == @nm")
        
        r2_list = []
        #gets values as list
        x = ind_nm["Time (s)"].tolist()

        #0th     
        y0 = ind_nm["Concentration (M)"].tolist()
        #finds R2
        y0_slope, y0_int, r_value_y0, p_value_y0, std_err_y0 = scipy.stats.linregress(x, y0)
        r_squared_y0 = r_value_y0**2
        R2_y0 = f'{r_squared_y0:.2f}'
        print(u"R\u00b2 for 0th order = ", R2_y0)
        r2_list.append(R2_y0)

        #1st
        y1 = ind_nm["ln[A]"].tolist()

        y1_slope, y1_int, r_value_y1, p_value_y1, std_err_y1 = scipy.stats.linregress(x, y1)
        r_squared_y1 = r_value_y1**2
        R2_y1 = f'{r_squared_y1:.2f}'
        print(u"R\u00b2 for 1st order = ", R2_y1)
        r2_list.append(R2_y1)

        #2nd
        y2 = ind_nm["1/[A]"].tolist()
        
        y2_slope, y2_int, r_value_y2, p_value_y2, std_err_y2 = scipy.stats.linregress(x, y2)
        r_squared_y2 = r_value_y2**2
        R2_y2 = f'{r_squared_y2:.2f}'
        print(u"R\u00b2 for 2nd order = ", R2_y2)
        r2_list.append(R2_y2)

        
        xmin = 0
        xmin = min(x)
        ymin = 0

        max_R = 0.0
        max_R = max(r2_list)
        #finds best fit, prints suggested answer, stores in dict, shows plot DOES NOT SAVE
        if max_R == R2_y0:
            print(f'{nm} nm is 0th order')
            data[nm] = "0th"
            

            ind_nm.plot(x = "Time (s)", y = "Concentration (M)")
            plt.title('Zero Order')
            
            plot_text = u'R\u00b2 = ' + max_R
            ymin = min(y0)
            plt.text(xmin, ymin, plot_text, fontsize =  12)
            plt.ylabel('[A]')
            plt.tight_layout()

            #plt.show()

        elif max_R == R2_y1:
            print(f'{nm} nm is 1st order') 
            data[nm] = "1st"

            ind_nm.plot(x = "Time (s)", y = "ln[A]")
            plt.title('First Order')
            
            plot_text = u'R\u00b2 = ' + max_R
            ymin = min(y1)
            plt.text(xmin, ymin, plot_text, fontsize =  12)
            plt.ylabel('ln[A]')
            plt.tight_layout()

            #plt.show()

        elif max_R == R2_y2:
            print(f'{nm} nm is 2nd order')
            data[nm] = "2nd"

            ind_nm.plot(x = "Time (s)", y = "1/[A]")
            plt.title('Second Order')
            
            plot_text = u'R\u00b2 = ' + max_R
            ymin = min(y2)
            plt.text(xmin, ymin, plot_text, fontsize =  12)
            plt.ylabel('1/[A]')
            
            plt.tight_layout()
            #plt.show()

        else:
            print(f"Order of {nm} nm is unclear or has multiple answers")

              
    return data
                
        

        

if __name__ == '__main__':
    main()
