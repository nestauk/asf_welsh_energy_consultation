from asf_welsh_energy_consultation import PROJECT_DIR

import pandas as pd
import numpy as np
import os

postcode_path = "inputs/data/postcodes"
regions_path = "inputs/data/regions.csv"

LOCAL_DATA_DIR = "/Users/chris.williamson/Documents/ASF_data"


def get_regions():
    """Get dataset of all UK postcodes with easting/northing coordinates,
    top-level region, and country columns. Save postcode and region columns
    as csv to enable lookup.

    Returns:
        Dataframe: Postcode geographic data.
    """
    # Read postcode data
    postcode_folder = PROJECT_DIR / postcode_path
    files = os.listdir(postcode_folder)
    postcode_df = pd.concat(
        # Only need postcode, coordinates and LA code cols
        (
            pd.read_csv(postcode_folder / file, header=None)[[0, 2, 3, 8]]
            for file in files
        ),
        ignore_index=True,
    )
    postcode_df.columns = ["postcode", "easting", "northing", "la_code"]

    postcode_df["postcode"] = postcode_df["postcode"].str.replace(" ", "")

    # Read English regions data so that LA codes can be associated with region names
    regions = pd.read_csv(PROJECT_DIR / regions_path)
    regions = regions[["LAD21CD", "RGN21NM"]]
    regions.columns = ["la_code", "region_name"]

    pc_regions = postcode_df.merge(regions, on="la_code", how="left")

    # Get country names from LA codes - country can be inferred from
    # first character of LA code
    country_dict = {
        "E": "England",
        "W": "Wales",
        "S": "Scotland",
        "N": "Northern Ireland",
        " ": np.nan,
    }
    pc_regions["country"] = (
        pc_regions["la_code"].fillna(" ").apply(lambda code: country_dict[code[0]])
    )
    # Outside England, region = country
    pc_regions["region_name"] = pc_regions["region_name"].fillna(pc_regions["country"])

    return pc_regions


def get_mcs_domestic():
    mcs = pd.read_csv("inputs/data/mcs_installations_230315.csv")

    mcs["installation_type"] = mcs["installation_type"].fillna(
        mcs["end_user_installation_type"]
    )
    mcs_domestic = mcs.loc[mcs.installation_type == "Domestic"].reset_index(drop=True)

    return mcs_domestic


def get_offgas():
    og = pd.read_excel(
        "inputs/data/off-gas-live-postcodes-2022.xlsx",
        sheet_name="Off Gas Live PostCodes 22",
    )

    og = og.rename(columns={"Post Code": "postcode"})
    og["postcode"] = og["postcode"].str.replace(" ", "")
    og["off_gas"] = True

    return og


def get_rurality():
    oa = pd.read_csv(
        "inputs/data/postcode_to_output_area.csv", encoding="latin-1"
    )  # latin-1 as otherwise invalid byte

    oa = oa[["pcd7", "oa11cd"]].rename(
        columns={"pcd7": "postcode", "oa11cd": "oa_code"}
    )
    oa["postcode"] = oa["postcode"].str.replace(" ", "")

    rural = pd.read_excel(
        "inputs/data/rurality.ods", engine="odf", sheet_name="OA11", skiprows=2
    )
    rural = rural.rename(
        columns={
            "Output Area 2011 Code": "oa_code",
            "Rural Urban Classification 2011 code": "rurality_10_code",
            "Rural Urban Classification 2011 (10 fold)": "rurality_10_label",
            "Rural Urban Classification 2011 (2 fold)": "rurality_2_label",
        }
    )
    rural["rurality_10_code"] = rural["rurality_10_code"].replace(
        {"C1\xa0\xa0": "C1", "D1\xa0": "D1"}
    )
    rural["rurality_10_label"] = rural["rurality_10_label"].replace(
        {
            "Urban major conurbation\xa0": "Urban major conurbation",
            "Urban city and town\xa0\xa0": "Urban city and town",
            "Rural town and fringe\xa0": "Rural town and fringe",
            "Rural village\xa0in a sparse setting": "Rural village in a sparse setting",
            "Rural town and fringe\xa0in a sparse setting\xa0": "Rural town and fringe in a sparse setting",
        }
    )

    oa_rural = oa.merge(rural, on="oa_code")
    # rurality data is just for England/Wales - fine for this purpose

    return oa_rural


from asf_core_data import load_preprocessed_epc_data


def get_wales_epc():
    wales_epc = load_preprocessed_epc_data(
        data_path=LOCAL_DATA_DIR, usecols=None, version="preprocessed", subset="Wales"
    )
    return wales_epc


def get_mcs_epc():
    mcs_epc = pd.read_csv("inputs/data/mcs_installations_epc_full_230315.csv")
    mcs_epc["commission_date"] = pd.to_datetime(mcs_epc["commission_date"])
    mcs_epc["INSPECTION_DATE"] = pd.to_datetime(mcs_epc["INSPECTION_DATE"])

    mcs_epc["capacity"] = mcs_epc["capacity"].mask(mcs_epc["capacity"] > 100)

    return mcs_epc
