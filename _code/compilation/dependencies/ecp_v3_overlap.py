#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 23 10:30:44 2022

@author: gd
"""

import pandas as pd
import copy
import itertools

def unique_combinations(elements: list[str]) -> list[tuple[str, str]]:
    """
    Precondition: `elements` does not contain duplicates.
    Postcondition: Returns unique combinations of length 2 from `elements`.

    >>> unique_combinations(["apple", "orange", "banana"])
    [("apple", "orange"), ("apple", "banana"), ("orange", "banana")]
    """
    return list(itertools.combinations(elements, 2))


def overlap(inst_df):
    
    ## LOAD OVERLAP DATAFRAMES
    overlap = pd.read_csv("/Users/gd/GitHub/WorldCarbonPricingDatabase/_raw/overlap/overlap_mechanisms.csv")
    
    ## CREATE OVERLAP COLUMNS
    # Encode overlap as binary variable at jurisdiction-year-sector-product level using wcpd_all and overlapping mechanisms file
    # create as many columns as there are possible overlapping pairs 
    
    id_cols = [x for x in inst_df.columns if x.endswith("_id")]
    
    inst_df_ids = inst_df[["jurisdiction", "year", "iea_code", "ipcc_code", "Product"]+id_cols]
    
    scheme_columns = {"tax":"tax_id", "ets":"ets_id", "ets_2":"ets_2_id"}

    scheme_list = [[a, b] for a in scheme_columns 
                   for b in scheme_columns if a != b]
    
    # Overlap identification columnns
    ovp_columns = {}
    
    a = list(itertools.combinations(list(scheme_columns.keys()), 2))
    
    for i in a:
        inst_df_ids.loc[:, "overlap_"+i[0]+"_"+i[1]] = 0
        inst_df_ids.loc[:, "overlap_"+i[0]+"_"+i[1]]+"_ids"] = inst_df_ids.loc[:, scheme_columns[i]] + inst_df_ids.loc[:, scheme_columns[j]]

        ovp_columns["overlap_"+i+"_"+j] = "overlap_"+i[0]+"_"+i[1]+"_ids"
    
    # Creating a new dataframe containing unique [inst_1, inst_2, ipcc_code entries]
    overlap_unique = overlap.drop_duplicates(["inst_1", "inst_2", "ipcc_code"]) 
    
    for ovp_col in ovp_columns.keys():
        for index, row in overlap_unique.iterrows():
            overlap = copy.deepcopy(overlap)
    
            # extracting the years in which an overalp exists for any pair of schemes
            years = overlap.loc[(overlap.inst_1 == row.inst_1) & (overlap.inst_2 == row.inst_2) & (overlap.ipcc_code == row.ipcc_code), "year"].unique()
    
            row_sel = (inst_df_ids[ovp_columns[ovp_col]].str.contains(row.inst_1)) & (inst_df_ids[ovp_columns[ovp_col]].str.contains(row.inst_2)) & (inst_df_ids.ipcc_code==row.ipcc_code) & (inst_df_ids.year.isin(years))
            inst_df_ids.loc[row_sel, ovp_col] = 1
    
        inst_df_ids.drop(ovp_columns[ovp_col], axis=1, inplace=True)
    
    # merge overlap df into cp df
    inst_df = inst_df.merge(inst_df_ids, on=['jurisdiction', 'year', 'ipcc_code', 'iea_code', 'Product']+id_cols)

    
    return inst_df
