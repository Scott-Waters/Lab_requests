#CREATED BY Scott Waters

#required import libraries: math for ...math
#pandas for CSV formating/output. Requires pip install in terminal ("pip install Pandas")
from math import sin, radians
import pandas as pd

def find_data_multi(file_list): 
#returns dict where each "key" is a your file name and the "value" is a dictionary
#  of the requested data. takes input from user as a list of file names
    all_data = {} #initialize final dict.
    for fileName in file_list: #parse list of provided files
        file = open(fileName) #opens parsed file
        file_name = str(fileName) #saves file name as string
        sample_name = crystal_name(fileName) #saves crystal name using below function
        data = {} #initialize dict for individual files
        data["Sample Name"] = sample_name #first entry in the "file name" key is sample name     
        for i in file.readlines(): 
            #pulls all requested data and adds it to the file name dictionary
            #to add more data to request, copy/paste the if statement format as below
            #if ("SEARCH PHRASE FROM CIF" in i):
            #    list_SEARCHKEY = i.split()
            #    data["DICTIONARY ENTRY KEY"] = list_SEARCHKEY[1]"

            
                
            
            if ("_cell_formula_units_Z" in i): #searches for key phrase in document
                list_z = i.split() #when found, splits the line into parts. All the data included here was separated by space (which is split() default)
                data["cell_formula_units_Z"] = list_z[1] #chooses the value of the line. list_z[0] would be "cell_formula_units_Z"
            if ("_cell_length_a" in i):
                list_a = i.split()
                data["cell_length_a"] = list_a[1]
            if ("_cell_length_b" in i):
                list_b = i.split()
                data["cell_length_b"] = list_b[1]
            if ("_cell_length_c" in i):
                list_c = i.split()
                data["cell_length_c"] = list_c[1]
            if ("_cell_angle_alpha" in i):
                list_alpha = i.split()
                data["cell_angle_alpha"] = list_alpha[1]
            if ("_cell_angle_beta" in i):
                list_beta = i.split()
                data["cell_angle_beta"] = list_beta[1]  
            if ("_cell_angle_gamma" in i):
                list_gamma = i.split()
                data["cell_angle_gamma"] = list_gamma[1]
            if ("_cell_volume" in i):
                list_volume = i.split()
                data["cell_volume"] = list_volume[1]  
            if ("_exptl_crystal_density_diffrn" in i):
                list_diff = i.split()
                data["exptl_crystal_density_diffrn"] = list_diff[1]
            if ("_exptl_absorpt_coefficient_mu" in i):
                list_mu = i.split()
                data["exptl_absorpt_coefficient_mu"] = list_mu[1]
            if ("_diffrn_reflns_number" in i):
                list_ref = i.split()
                data["diffrn_reflns_number"] = list_ref[1]
            if ("_reflns_number_total" in i):
                list_tot = i.split()
                data["reflns_number_total"] = list_tot[1]
            if ("_reflns_number_gt" in i):
                list_gt = i.split()
                data["reflns_number_gt"] = list_gt[1]
            if ("_diffrn_reflns_av_R_equivalents" in i):
                list_Req = i.split()
                data["diffrn_reflns_av_R_equivalents"] = list_Req[1]
            if ("_refine_ls_R_factor_gt" in i):
                list_Rgt = i.split()
                data["refine_ls_R_factor_gt"] = list_Rgt[1]
            if ("_refine_ls_wR_factor_ref" in i):
                list_wR = i.split()
                data["refine_ls_wR_factor_ref"] = list_wR[1]
            if ("_refine_ls_goodness_of_fit_ref" in i):
                list_refFit = i.split()
                data["refine_ls_goodness_of_fit_ref"] = list_refFit[1]
            if ("_refine_diff_density_max" in i):
                list_denMax = i.split()
                data["refine_diff_density_max"] = list_denMax[1]
            if ("_refine_diff_density_min" in i):
                list_denMin = i.split()
                data["refine_diff_density_min"] = list_denMin[1]
            if ("_diffrn_reflns_theta_max" in i):
                list_rad = i.split()
                cell_rad = radians(float(list_rad[1]))
                data["refln_theta_max_in_rad"] = 0.7107 / (2 * sin(cell_rad))
            all_data[file_name] = data #adds the key of "file name" with the value of "dictionary of all the values of that file" to final dictionary
        
        file.close() #closes file being parsed
    return all_data

def crystal_name(fileName): #returns name of crystal sample
    file = open(fileName) #opens file
    title = file.readline() #reads first line
    pos = 5 #assumes the first line contains the sample name and stars with "Data_"
    while(pos<len(title) and (not title[pos].isspace())):
    #finds name of crystal starting after "data_" and going until there is a space
        pos += 1
        name = title[5:pos]
                    
    file.close() #closes file
    return name

#prompts user for cif names
cifs_imported = input("What are the cif names? (separate using \", \"): ")
#converts the provided string to a list
cifs_needed = cifs_imported.split(", ")
data_list = {}
#stores a dict of the result of the program "find_data_multi" with the user provided cifs
data_list = find_data_multi(cifs_needed) 
#generates data frame using pandas of "data_list" dict. the first column is renamed to "cif file name"
df = pd.DataFrame(data_list).rename_axis('cif file name').reset_index()

#converts the dataframe to csv and saves it as "out.csv"
df.to_csv('out.csv', index=False)





