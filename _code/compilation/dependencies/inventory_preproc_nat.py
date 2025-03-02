
import pandas as pd
import csv
import os
from importlib.machinery import SourceFileLoader

path_dependencies = '/Users/gd/GitHub/ECP/_code/compilation/dependencies'
path_ghg = '/Users/gd/OneDrive - rff/documents/research/projects/ecp/ecp_dataset/source_data/ghg_inventory/raw'

ecp_general = SourceFileLoader('general_func', path_dependencies+'/ecp_v3_gen_func.py').load_module()

# CO2

def inventory_co2(wcpd_df, ipcc_iea_map, jur_names, edgar_wb_map):

    # concatenate IEA yearly emissions files
    ecp_general.concat_iea() 
    
    # aggregate fuel products to three aggregate categories (coal, oil, natural gas)
    result = {}

    with open(path_ghg+'/national/IEA/iea_energy_combustion_emissions/detailed_figures/emissions_allyears/iea_CO2em_ally.csv', 'r',
             encoding = 'latin-1') as csvfile:
        data_reader = csv.reader(csvfile)
        next(data_reader, None)  # skip the headers

        for row in data_reader:
            #extract column value based on column index
            year = row[6]
            location = row[1]
            product_code = row[2]
            flow = row[4]
            sector_name = row[5]
            value = ecp_general.convert_value(row[8]) #uses the convert_value function created above

            #'product_code' function defined above; assigns a 'product category' to each of the sub-products based on its product code
            product_category = ecp_general.get_product_category(product_code)

            #initialise container of year key
            if year not in result:
                result[year] = {}

            #initialise container of location key
            if location not in result[year]:
                    result[year][location] = {}

            # initialise container of product_category key if not present; that is, if the product category key is NOT already present in result, it will be addded to it
            if product_category not in result[year][location]:
                result[year][location][product_category] =  {}

            #initialise container of flow-sector names if not present
            if sector_name not in result[year][location][product_category]:
                result[year][location][product_category][sector_name] = {}

            # initialise container of flow codes if not present
            if flow not in result[year][location][product_category][sector_name]:
                result[year][location][product_category][sector_name][flow] = 0

            # perform the aggregation (in the present case, for each row, the code adds the value of 'value' to the container)
            result[year][location][product_category][sector_name][flow] += value

    with open(path_ghg+'/national/IEA/iea_energy_combustion_emissions/detailed_figures/agg_product/iea_aggprod.csv', "w", encoding = 'utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(('Country','year','Flow','Sector','Product','CO2'))

        for year in result:
            for location in result[year]:
                for product_category in result[year][location]:
                    for sector_name in result[year][location][product_category]:
                        for flow in result[year][location][product_category][sector_name]:
                            writer.writerow((location, year, flow, sector_name, product_category, result[year][location][product_category][sector_name][flow]))

    os.remove(path_ghg+'/national/IEA/iea_energy_combustion_emissions/detailed_figures/emissions_allyears/iea_CO2em_ally.csv')                

    # standardize country names to WB names
    combustion_nat = pd.read_csv(path_ghg+"/national/IEA/iea_energy_combustion_emissions/detailed_figures/agg_product/iea_aggprod.csv",
                      encoding = "utf-8") #specify encoding

    map_iea_wb = {"CÃ\x83Â´te d'Ivoire": "Cote d'Ivoire", "CÃ´te d'Ivoire": "Cote d'Ivoire",
                  '"China (P.R. of China and Hong Kong, China)"': 'China (P.R. of China and Hong Kong, China)',
                  "People's Republic of China": 'China', 'CuraÃ\x83Â§ao/Netherlands Antilles': 'Curacao/Netherlands Antilles',
                  'CuraÃ§ao': 'Curacao', 'CuraÃ§ao/Netherlands Antilles': 'Curacao/Netherlands Antilles',
                  'Democratic Republic of Congo': 'Congo, Dem. Rep.', 'Democratic Republic of the Congo': 'Congo, Dem. Rep.',
                  'Republic of the Congo': 'Congo, Rep.', 'Egypt': 'Egypt, Arab Rep.', 'Hong Kong (China)': 'Hong Kong SAR, China',
                  'Islamic Republic of Iran': 'Iran, Islamic Rep.', "Democratic People's Republic of Korea": 'Korea, Dem. Rep.',
                  'Korea': 'Korea, Rep.', 'Kyrgyzstan': 'Kyrgyz Republic', 'Republic of North Macedonia': 'North Macedonia',
                  'Republic of Moldova':'Moldova', 'Chinese Taipei':'Taiwan, China',
                  'Venezuela': 'Venezuela, RB', 'Plurinational State of Bolivia':'Bolivia',
                  'United Republic of Tanzania':'Tanzania',
                  'Bolivarian Republic of Venezuela': 'Venezuela, RB', 'Viet Nam': 'Vietnam', 'Yemen': 'Yemen, Rep.'}

    combustion_nat['Country'] = combustion_nat['Country'].replace(to_replace=map_iea_wb) 

    combustion_nat.to_csv(path_ghg+'/national/IEA/iea_energy_combustion_emissions/detailed_figures/agg_product/iea_aggprod.csv',index=None)

    # dataframe format/labels standardization
    combustion_nat.rename(columns={"Country":"jurisdiction", "Year":"year", "Flow":"iea_code"}, inplace=True)
    combustion_nat.drop("Sector", axis=1, inplace=True)

    combustion_nat = combustion_nat.merge(ipcc_iea_map, on=["iea_code"], how="left")

    # Data from EDGAR database

    edgar = pd.read_excel(path_ghg+"/national/EDGAR/v60_CO2_excl_short-cycle_org_C_1970_2018.xls",
                              sheet_name="v6.0_EM_CO2_fossil_IPCC2006", skiprows=9)

    edgar.drop(['IPCC_annex', 'C_group_IM24_sh', 'Country_code_A3', 'ipcc_code_2006_for_standard_report_name', 'fossil_bio'], axis=1, inplace=True)

    edgar = edgar.loc[~edgar.Name.isin(["Int. Shipping", "Int. Aviation"]), :]
    edgar = edgar.melt(id_vars=["Name", "ipcc_code_2006_for_standard_report"])

    edgar.rename(columns={"Name":"jurisdiction", "ipcc_code_2006_for_standard_report":"ipcc_code", "variable":"year", "value":"CO2"}, 
                     inplace=True)
    # format ipcc_code and year columns
    edgar["ipcc_code"] = edgar["ipcc_code"].apply(lambda x: x.replace('.', '').upper())
    edgar["year"] = edgar["year"].apply(lambda x: x.replace('Y_', '').upper())
    edgar["ipcc_code"] = edgar["ipcc_code"].apply(lambda x: x.replace('_NORES', '').upper())
    edgar["year"] = edgar["year"].astype(int)

    # select sectors
    ippu_fug_nat = edgar.loc[edgar.ipcc_code.str.match("1B|2"), :]

    ippu_fug_nat["jurisdiction"] = ippu_fug_nat["jurisdiction"].replace(to_replace=edgar_wb_map)

    # dataframe standardization
    ippu_fug_nat = ippu_fug_nat[["jurisdiction", "year", "ipcc_code", "CO2"]]
    ippu_fug_nat["year"] = ippu_fug_nat["year"].astype(int)
    ippu_fug_nat["iea_code"] = "NA"
    ippu_fug_nat["Product"] = "NA"


    # COMBINED INVENTORY

    inventory_nat = wcpd_df.loc[wcpd_df.jurisdiction.isin(jur_names), ["jurisdiction", "year", "ipcc_code", "iea_code", "Product"]]
    inventory_nat[["iea_code", "Product"]] = inventory_nat[["iea_code", "Product"]].fillna("NA")

    combined_nat = pd.concat([combustion_nat, ippu_fug_nat])

    inventory_nat = inventory_nat.merge(combined_nat, on=["jurisdiction", "year", "ipcc_code", "iea_code", "Product"], how="left")
    
    return inventory_nat


# OTHER GHGs

def inventory_non_co2(wcpd_df, jur_names, gas, edgar_wb_map, ipcc_gwp_list):

    gas_file_name = {"CH4":"v60_CH4_1970_2018.xls", "N2O":"v60_N2O_1970_2018.xls"}

    if gas == "F-GASES":
        # list of file names containing F-gases data
        file_names_fgases = os.listdir("/Users/gd/OneDrive - rff/Documents/Research/projects/ecp/ecp_dataset/source_data/ghg_inventory/raw/national/EDGAR/v60_GHG_fgases_1990_2018")

        fgases_tot = pd.DataFrame()

        # Aggregate files for f-gases
        for i in range(0,len(file_names_fgases)):
            edgar_fgas = pd.read_excel(path_ghg+"/national/EDGAR/v60_GHG_fgases_1990_2018/"+file_names_fgases[i], skiprows=9,
                                sheet_name="v6.0_EM_"+file_names_fgases[i][:-15]+"_IPCC2006")
            edgar_fgas = edgar_fgas.loc[edgar_fgas.fossil_bio=="fossil"] # keep only fossil emissions

            edgar_fgas.drop(["IPCC_annex", "C_group_IM24_sh", "Country_code_A3", "ipcc_code_2006_for_standard_report_name",
                             "fossil_bio"], axis=1, inplace=True)
            edgar_fgas.rename(columns={"Name":"ctry_name"}, inplace=True)

            edgar_fgas = edgar_fgas.melt(id_vars=["ctry_name", "ipcc_code_2006_for_standard_report"])

            edgar_fgas.rename(columns={"ctry_name":"jurisdiction", "ipcc_code_2006_for_standard_report":"ipcc_code", 
                                       "variable":"year", "value":file_names_fgases[i][:-15]}, inplace=True)

            # format ipcc_code and year columns
            edgar_fgas["ipcc_code"] = edgar_fgas["ipcc_code"].apply(lambda x: x.replace('.', '').upper())
            edgar_fgas["year"] = edgar_fgas["year"].apply(lambda x: x.replace('Y_', '').upper())
            edgar_fgas["ipcc_code"] = edgar_fgas["ipcc_code"].apply(lambda x: x.replace('_NORES', '').upper())
            edgar_fgas["year"] = edgar_fgas["year"].astype(int)

            edgar_fgas['jurisdiction'].replace(to_replace=edgar_wb_map, inplace=True)

            # convert to CO2 equivalent
            edgar_fgas[file_names_fgases[i][:-15]] =  edgar_fgas[file_names_fgases[i][:-15]]*ipcc_gwp_list[file_names_fgases[i][:-15]]

            if fgases_tot.empty == True:
                fgases_tot = edgar_fgas
            else:
                fgases_tot = fgases_tot.merge(edgar_fgas, on=["jurisdiction", "year", "ipcc_code"], how="outer")

        # Sum of all f-gases
        fgases_tot.fillna(0, inplace=True)
        fgases_tot["F-GASES"] = fgases_tot.drop(["jurisdiction", "year", "ipcc_code"], axis=1).sum(axis=1)
        edgar = fgases_tot[["jurisdiction", "year", "ipcc_code", "F-GASES"]] # keep only aggregate F-GASES value and merge keys

    else:

        edgar = pd.read_excel(path_ghg+"/national/EDGAR/"+gas_file_name[gas],
                                sheet_name="v6.0_EM_"+gas+"_IPCC2006", skiprows=9)

        edgar.drop(['IPCC_annex', 'C_group_IM24_sh', 'Country_code_A3', 'ipcc_code_2006_for_standard_report_name', 'fossil_bio'], axis=1, inplace=True)

        edgar = edgar.loc[~edgar.Name.isin(["Int. Shipping", "Int. Aviation"]), :]
        edgar = edgar.melt(id_vars=["Name", "ipcc_code_2006_for_standard_report"])

        edgar.rename(columns={"Name":"jurisdiction", "ipcc_code_2006_for_standard_report":"ipcc_code", "variable":"year", "value":gas}, 
                        inplace=True)
        # format ipcc_code and year columns
        edgar["ipcc_code"] = edgar["ipcc_code"].apply(lambda x: x.replace('.', '').upper())
        edgar["year"] = edgar["year"].apply(lambda x: x.replace('Y_', '').upper())
        edgar["ipcc_code"] = edgar["ipcc_code"].apply(lambda x: x.replace('_NORES', '').upper())
        edgar["year"] = edgar["year"].astype(int)

        # convert to CO2 equivalent
        edgar[gas] =  edgar[gas]*ipcc_gwp_list[gas]

    # COMBINED INVENTORY

    inventory_nat = wcpd_df.loc[wcpd_df.jurisdiction.isin(jur_names), ["jurisdiction", "year", "ipcc_code"]]
    inventory_nat.drop_duplicates(subset=["jurisdiction", "year", "ipcc_code"], inplace=True)

    inventory_nat = inventory_nat.merge(edgar, on=["jurisdiction", "year", "ipcc_code"], how="left")


    return inventory_nat


