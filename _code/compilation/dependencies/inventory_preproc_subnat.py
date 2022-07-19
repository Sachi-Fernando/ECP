
# Ideally, need to write this so that one function can accommodate several subnational inventories.

import os
import glob
import pandas as pd
import numpy as np

# path to GHG data
path_ghg = "/Users/gd/OneDrive - rff/Documents/Research/projects/ecp/ecp_dataset/source_data/ghg_inventory/raw"

# load (subnat) jurisdictions lists
stream = open("/Users/gd/GitHub/WorldCarbonPricingDatabase/_code/_compilation/_dependencies/jurisdictions.py")
read_file = stream.read()
exec(read_file)

# load inventory sector names to IPCC 
stream = open("/Users/gd/GitHub/ECP/_code/compilation/dependencies/ipcc_map_subnat.py")
read_file = stream.read()
exec(read_file)

# jur names mapping
stream = open("/Users/gd/GitHub/ECP/_code/compilation/dependencies/jur_names_concordances.py")
read_file = stream.read()
exec(read_file)




# Common pre-processing
# CANADA

can = pd.read_csv(path_ghg+'/subnational/Canada/harmonized_data/ECCC/GHG_IPCC_Can_Prov_Terr.csv',
            low_memory=False)

can.rename(columns={"Region":"jurisdiction", "Category":"ipcc_code"}, inplace=True)

can = can.loc[can.jurisdiction != "Canada", :]
can.drop(["Rollup", "CategoryID", "CH4", "N2O", "Unit"], axis=1, inplace=True)
can.rename(columns={"Region":"jurisdiction", "Year":"year",
                    "CH4 (CO2eq)":"CH4", "N2O (CO2eq)":"N2O", "CO2eq":"all_GHG"}, inplace=True)

can = can.loc[~can.ipcc_code.isna(), :] #keep all sectors in 'can' dataframe but assign IEA and IPCC codes so that they can be sorted
can["ipcc_code"].replace(to_replace=category_names_ipcc_can_map, inplace=True)

# eliminating 'x' entries in the columns
for col in ["CO2", "CH4", "N2O", "HFCs", "PFCs", "SF6", "NF3", "all_GHG"]:
    can[col].replace(to_replace={"x":None}, inplace=True)
    can[col] = can[col].astype(float)

can["F-GASES"] = can[["HFCs", "PFCs", "SF6", "NF3"]].sum(axis=1)
can.drop(["HFCs", "PFCs", "SF6", "NF3"], axis=1, inplace=True)

can["supra_jur"] = "Canada"



# CHINA

inv_jur_names_chn = pd.read_excel(path_ghg+"/subnational/China/CEADS/CEADS_provincial_emissions/Emission_inventories_for_30_provinces_1997.xlsx", 
                            sheet_name="Sum")
inv_jur_names_chn = list(inv_jur_names_chn["Unnamed: 0"])[:-2]

file_list = os.listdir(path_ghg+"/subnational/China/CEADS/CEADS_provincial_emissions/")
#file_list.remove('.DS_Store')

china_comb = pd.DataFrame() # df for combustion emissions
china_proc = pd.DataFrame() # df for process emissions

for file in file_list:
    for prov in inv_jur_names_chn:
        temp = pd.read_excel(path_ghg+"/subnational/China/CEADS/CEADS_provincial_emissions/"+file, 
                            sheet_name=prov, skiprows=[1,2])

        temp.rename(columns={"Unnamed: 0":"ipcc_code"}, inplace=True)
        temp["year"] = file[-9:-5]
        temp["jurisdiction"] = prov

        temp_comb = temp[["jurisdiction", "year", "ipcc_code", "Process", "Total"]].copy()
        temp_proc = temp[["jurisdiction", "year", "ipcc_code", "Process"]].copy()

        temp_comb.loc[:, "CO2"] = temp.loc[:, "Total"]-temp.loc[:, "Process"]
        temp_comb.drop(["Process", "Total"], axis=1, inplace=True)

        if china_comb.empty == True:
            china_comb = temp_comb
            china_proc = temp_proc
        else:
            china_comb = pd.concat([china_comb, temp_comb])
            china_proc = pd.concat([china_proc, temp_proc])


            # From the CEADS data, we can actually recover the emissions associated with each broad fuel category (like for national jurisdictions)

# Replace province names by those in dataset
china_comb.replace(to_replace=subnat_names_map_chn, inplace=True)
china_comb.replace(to_replace=category_names_ipcc_chn_map, inplace=True)

china_proc.replace(to_replace=subnat_names_map_chn, inplace=True)
china_proc = china_proc.loc[china_proc.ipcc_code=='Nonmetal Mineral Products                                ', :]
china_proc.replace(to_replace={'Nonmetal Mineral Products                                ':"2A"}, inplace=True)
china_proc.rename(columns={"Process":"CO2"}, inplace=True)

# concatenate combustion and process emissions dataframes

china = pd.concat([china_comb, china_proc])
china = china.loc[china.ipcc_code!="Total Consumption"] # remove total category from dataframe

# sum at the (aggregate) sector level - since some sectors have been assigned the same IPCC code

chn = china.groupby(["jurisdiction", "year", "ipcc_code"]).sum()
chn = chn.reset_index()
["year"] = chn.year.astype(int)

# generating empty columns for greenhouse gases that are not in China's source data
for col in ["CH4", "N2O", "F-GASES", "all_GHG"]:
    chn[col] = np.nan

chn["supra_jur"] = "China"


# UNITED STATES

us = pd.DataFrame()

os.chdir(path_ghg+'/subnational/United_States/Rhodium/')
file_list = glob.glob('*.csv')

for file in file_list:
    temp = pd.read_csv(path_ghg+'/subnational/United_States/Rhodium/'+file, decimal=',')
    #extract US state name from file name
    state_name = file[len("DetailedGHGinventory_"):-4]
    #add state name as key column
    temp.loc[:, "jurisdiction"] = state_name
    #concat
    us = pd.concat([us, temp])

#add ipcc_code
us.loc[:, "ipcc_code"] = us.loc[:, "Subsector"]
us.loc[:, "ipcc_code"] = us.loc[:, "ipcc_code"].replace(to_replace=category_names_ipcc_usa_map)

excl_sectors = ['Transport - Natural gas pipeline', 'Carbon Dioxide Consumption', 'Abandoned Oil and Gas Wells', 'Phosphoric Acid Production',
                'Natural Gas Systems', 'Petroleum Systems', 'Urea Consumption for Non-Agricultural Purposes']

us = us.loc[~us.ipcc_code.isin(excl_sectors), :]

us = pd.pivot_table(us, values = "Emission (mmt CO2e)", index=['jurisdiction','Year', 'ipcc_code'], columns = 'Gas').reset_index()

us["CO2"] = us["CO2 (combustion)"]+us["CO2 (non-combustion)"]
us["F-GASES"] = us[["HFCs", "PFCs", "NF3", "SF6"]].sum(axis=1)
us["all_GHG"] = us[["HFCs", "PFCs", "NF3", "SF6"]].sum(axis=1)

us = us.drop(["CO2 (combustion)", "CO2 (non-combustion)", "LULUCF", 
              "NF3", "SF6", "PFCs", "HFCs"], axis=1)
us = us.rename(columns={"Year":"year"})

us = us.loc[us.year<=2020, :]
us = us.sort_values(by=["jurisdiction", "year", "ipcc_code"])

#needed to aggregate over IPCC sectors as I have attributed same ipcc_code to multiple Rhodium categories
us = us.groupby(by=["jurisdiction", "year", "ipcc_code"]).sum()
us = us.reset_index()

# replace name of Georgia State to avoid clash with Georgia country
us["jurisdiction"].replace(to_replace={"Georgia":"Georgia_US"}, inplace=True)

# add supra jurisdiction column
us["supra_jur"] = "United States"


def subnat_total():

    #CANADA 
    can_tot = can.loc[can.Category=="0"]
    can_tot.drop("Category", axis=1, inplace=True)

    can_lulucf = can.loc[can.Category.isin(["LAND USE, LAND-USE CHANGE AND FORESTRY"]), :]
    can_lulucf.drop("Category", axis=1, inplace=True)

    #Calculating totals excluding LULUCF
    temp = can_tot.merge(can_lulucf, on=["jurisdiction", "year"], how="left")

    for gas in ["CO2", "CH4", "N2O", "F-GASES", "all_GHG"]:
        temp[gas+"_x"] = temp[gas+"_x"]-temp[gas+"_y"]
        temp.rename(columns={gas+"_x":gas}, inplace=True)
        temp.drop([gas+"_y"], axis=1, inplace=True)

    can_tot = temp

    # CHINA

    chn_tot = china.groupby(["jurisdiction", "year"]).sum()
    chn_tot = chn_tot.reset_index()

    # USA

    usa_tot = us.groupby(["jurisdiction", "year"]).sum()
    usa_tot = usa_tot.reset_index()

    # COMBINED

    subnat_total = pd.concat([can_tot, chn_tot, usa_tot])

    return subnat_total


def inventory_subnat(wcpd_df, ipcc_iea_map, gas):

    # Inventory structure
    inventory_subnat = wcpd_df.loc[wcpd_df.jurisdiction.isin(subnat_names), ["jurisdiction", "year", "ipcc_code", "iea_code"]]

    # we don't have fuel level GHG data for subnational jurisdictions so we drop the Product column and delete duplicate/redundant rows 
    inventory_subnat.drop_duplicates(subset=["jurisdiction", "year", "ipcc_code", "iea_code"], inplace=True)
    inventory_subnat[["iea_code"]] = inventory_subnat[["iea_code"]].fillna("NA")


    # CANADA

    can_inv = can[["jurisdiction", "year", "ipcc_code", gas]]

    # CHINA

    chn_inv = chn[["jurisdiction", "year", "ipcc_code", gas]]

    # UNITED STATES

    usa_inv = us[["jurisdiction", "year", "ipcc_code", gas]]




    # -------------------------------Combined inventory df-----------------------------------
    # This part of the code needs adjustment as and when new GHG inventories are added to the 


    # COMBINED data
    combined_subnat = pd.concat([can_inv, chn_inv, usa_inv])
    combined_subnat = combined_subnat.merge(ipcc_iea_map, on=["ipcc_code"], how="left")
    combined_subnat[["iea_code"]] = combined_subnat[["iea_code"]].fillna("NA")

    inventory_subnat.loc[inventory_subnat.jurisdiction.isin(us_states), "supra_jur"] = "United States"
    inventory_subnat.loc[inventory_subnat.jurisdiction.isin(can_prov), "supra_jur"] = "Canada"
    inventory_subnat.loc[inventory_subnat.jurisdiction.isin(chn_prov), "supra_jur"] = "China"
    inventory_subnat.loc[inventory_subnat.jurisdiction.isin(jpn_pref), "supra_jur"] = "Japan"

    inventory_subnat = inventory_subnat.merge(combined_subnat, on=["supra_jur", "jurisdiction", "year", "ipcc_code", "iea_code"], how="left")
    inventory_subnat = inventory_subnat[['supra_jur', 'jurisdiction', 'year', 'ipcc_code', "iea_code", 'CO2_emissions']]
    
    return inventory_subnat