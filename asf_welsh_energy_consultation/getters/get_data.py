# File: asf_welsh_energy_consultation/getters/get_data.py
"""
Data getters.
"""

from asf_welsh_energy_consultation import PROJECT_DIR
from asf_welsh_energy_consultation import config_file

from asf_core_data import load_preprocessed_epc_data, get_mcs_installations
from asf_core_data.getters.mcs_getters.get_mcs_installations import (
    get_processed_installations_data_by_batch,
)

from asf_core_data.getters.epc.data_batches import get_batch_path
from asf_core_data.config import base_config
from asf_core_data.getters.data_getters import download_core_data, logger

import pandas as pd
import numpy as np
import os


def get_mcs_and_joined_data(epc_version, mcs_date):
    """
    Get cleaned MCS data, and cleaned MCS data fully joined with EPC dataset, and cleaned MCS data joined with most recent EPC before HP
    installation or earliest after installation, up to date specified in args.

    Args:
        epc_version (str): specifies which EPC version is joined to MCS data. One of "none", "full", "newest" or "most_relevant".
            "none" returns just MCS installation data, "full" returns MCS installation data with
            each property's entire EPC history attached, "newest" selects the EPC
            corresponding to the most recent inspection and "most_relevant" selects the
            most recent EPC from before the HP installation if one exists or the earliest EPC
            from after the HP installation otherwise. Defaults to "none".
        mcs_date (str): which MCS installations data batch to use in the form `YYMMDD`.

    Returns:
        pandas.DataFrame: specified MCS or MCS-EPC joined dataset.
    """

    # Get latest MCS data or batch specified in args
    if mcs_date == "newest":
        mcs_data = get_mcs_installations(epc_version=epc_version)
    else:
        mcs_data = get_processed_installations_data_by_batch(
            batch_date=mcs_date, epc_version=epc_version
        )
    return mcs_data


def get_countries(input_data_path):
    """Get lookup table of postcodes to countries.

    Args:
        input_data_path (str): path to supplementary data directory

    Returns:
        Dataframe: Postcode geographic data.
    """
    data_edition = input_data_path.split("/")[-1]
    # Read postcode data
    postcode_path = os.path.join(
        input_data_path, config_file["supplementary_data"][data_edition]["postcode_dir"]
    )

    # From 202411 analysis, we use the full postcode directory rather than the partitioned files
    if data_edition >= "data_202411":
        postcode_df = pd.read_csv(os.path.join(PROJECT_DIR, postcode_path))
        postcode_df = postcode_df.rename(
            columns={"pcd": "postcode", "osward": "la_code"}
        )
    else:  # 202310 or 202304 analysis
        postcode_folder = PROJECT_DIR / postcode_path
        files = os.listdir(postcode_folder)
        try:
            postcode_df = pd.concat(
                # Only need postcode and LA code cols
                (
                    pd.read_csv(os.path.join(postcode_folder, file), header=0)[
                        ["pcd", "osward"]
                    ]
                    for file in files
                ),
                ignore_index=True,
            )
            postcode_df = postcode_df.rename(
                columns={"pcd": "postcode", "osward": "la_code"}
            )

        except KeyError:  # Older data has no col names so use col numbers
            postcode_df = pd.concat(
                # Only need postcode and LA code cols
                (
                    pd.read_csv(postcode_folder / file, header=None)[[0, 8]]
                    for file in files
                ),
                ignore_index=True,
            )
            postcode_df = postcode_df.rename(columns={0: "postcode", 8: "la_code"})

    postcode_df["postcode"] = postcode_df["postcode"].str.replace(" ", "")

    # Get country names from LA codes - country can be inferred from
    # first character of LA code
    country_dict = {
        "E": "England",
        "W": "Wales",
        "S": "Scotland",
        "N": "Northern Ireland",
        "L": "Channel Islands",
        "M": "Isle of Man",
        " ": np.nan,
    }

    postcode_df["country"] = (
        postcode_df["la_code"]
        .fillna(" ")
        .apply(
            lambda code: country_dict[code[0]]
            if code[0] in country_dict.keys()
            else "other"
        )
    )

    return postcode_df


def get_mcs_domestic(mcs_date):
    """Get domestic MCS data.

    Args:
        mcs_date (str): which MCS installations data batch to use in the form `YYMMDD`.

    Returns:
        pd.DataFrame: Domestic MCS installation records.
    """
    mcs = get_mcs_and_joined_data(epc_version="none", mcs_date=mcs_date)

    # Older MCS data batches will need this processing step
    # Newer batches have been through this processing step already in the pipeline
    if "end_user_installation_type" in mcs.columns:
        mcs["installation_type"] = mcs["installation_type"].fillna(
            mcs["end_user_installation_type"]
        )
        mcs = mcs.drop(columns=["end_user_installation_type"])

    mcs_domestic = mcs.loc[mcs.installation_type == "Domestic"].reset_index(drop=True)

    return mcs_domestic


def get_rurality(input_data_path):
    """
    Get rurality df with country code column.

    Args:
        input_data_path (str): path to supplementary data directory

    Returns:
        pandas.DataFrame: Rurality data.
    """
    data_edition = input_data_path.split("/")[-1]
    rural_path = os.path.join(
        input_data_path,
        config_file["supplementary_data"][data_edition]["rurality_data"],
    )

    rural_df = pd.read_excel(
        os.path.join(PROJECT_DIR, rural_path),
        engine="odf",
        sheet_name="LSOA11",
        skiprows=2,
    )

    rural_df = rural_df.rename(
        columns={
            "Lower Super Output Area 2011 Code": "lsoa_code",
            "Rural Urban Classification 2011 (2 fold)": "rural_2",
        }
    )

    # Add country col
    rural_df["country"] = rural_df["lsoa_code"].apply(lambda x: x[0])

    return rural_df


def get_dwelling_data(input_data_path):
    """
    Get total number of dwellings per LSOA.

    Args:
        input_data_path (str): path to supplementary data directory

    Returns:
        pandas.DataFrame: Total number of dwellings per LSOA.
    """
    data_edition = input_data_path.split("/")[-1]
    dwelling_path = os.path.join(
        input_data_path,
        config_file["supplementary_data"][data_edition]["dwelling_data"],
    )

    dwellings = pd.read_excel(
        os.path.join(PROJECT_DIR, dwelling_path), sheet_name="1c", skiprows=3
    )
    dwellings = dwellings[
        [
            "LSOA Code",
            "Total: All dwellings (excluding communal establishments)",
            "LSOA Name",
        ]
    ]
    dwellings = dwellings.rename(
        columns={
            "LSOA Code": "lsoa_code",
            "Total: All dwellings (excluding communal establishments)": "total_dwellings",
            "LSOA Name": "lsoa_name",
        }
    )

    return dwellings


def get_offgas(input_data_path):
    """Get dataset of off-gas-grid postcodes.

    Args:
        input_data_path (str): path to supplementary data directory

    Returns:
        pd.DataFrame: Dataframe containing off-gas postcodes.
    """
    data_edition = input_data_path.split("/")[-1]
    off_gas_path = os.path.join(
        input_data_path, config_file["supplementary_data"][data_edition]["off_gas_data"]
    )
    og = pd.read_excel(
        PROJECT_DIR / off_gas_path,
        sheet_name=config_file["supplementary_data"][data_edition]["off_gas_sheet"],
    )

    og = og.rename(columns={"Post Code": "postcode"})
    og["postcode"] = og["postcode"].str.replace(" ", "")
    og["off_gas"] = True

    return og


def get_rurality_by_oa(input_data_path):
    """Get dataset of postcodes and their rurality indices.
    Two codes are used - the more specific 10-fold code, and the less specific
    two-fold code ("rural"/"urban").

    Args:
        input_data_path (str): path to supplementary data directory

    Returns:
        pd.DataFrame: Dataset with postcodes and ruralities.
    """
    data_edition = input_data_path.split("/")[-1]
    oa_path = os.path.join(
        input_data_path,
        config_file["supplementary_data"][data_edition]["postcode_to_oa_data"],
    )

    # Historical data requires a different encoding
    if data_edition > "data_202310":
        oa = pd.read_csv(PROJECT_DIR / oa_path)
    else:
        oa = pd.read_csv(
            PROJECT_DIR / oa_path, encoding="latin-1"
        )  # latin-1 as otherwise invalid byte

    oa = oa[["pcd7", "oa21cd"]].rename(
        columns={"pcd7": "postcode", "oa21cd": "oa_code"}
    )
    oa["postcode"] = oa["postcode"].str.replace(" ", "")

    rurality_path = os.path.join(
        input_data_path,
        config_file["supplementary_data"][data_edition]["rurality_data"],
    )
    rural = pd.read_excel(
        PROJECT_DIR / rurality_path, engine="odf", sheet_name="OA11", skiprows=2
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


def check_local_epc(epc_batch, epc_processing_version, local_data_dir):
    """
    Checks local directory for relevant EPC batch and downloads relevant EPC batch from S3 to local directory if not found.

    Args:
        epc_batch (str): which EPC data batch to use in the form `YYYY_QN_complete` or "newest" for latest batch.
        epc_processing_version (str): which processing version of EPC to use. Either `preprocessed` or `preprocessed_and_deduplicated`
        local_data_dir (str): path to local data directory where EPC data stored
    """

    local_epc_output_dir = os.path.join(
        local_data_dir, base_config.OUTPUT_DATA_PATH, "{}"
    )

    local_epc_file_path = os.path.join(
        local_epc_output_dir, f"EPC_GB_{epc_processing_version}.csv"
    )

    local_epc_batch_path = get_batch_path(
        rel_path=local_epc_file_path,
        data_path="S3",
        batch=epc_batch,
        check_folder="outputs",
    )

    if not os.path.exists(local_epc_batch_path) and not os.path.exists(
        os.path.join(local_epc_batch_path, ".zip")
    ):
        if epc_processing_version == "preprocessed":
            download_core_data_epc_version = "epc_preprocessed"
        elif epc_processing_version == "preprocessed_and_deduplicated":
            download_core_data_epc_version = "epc_preprocessed_dedupl"

        logger.info(
            f"EPC data; batch: `{local_epc_batch_path.parts[-2]}`; version: `{epc_processing_version}` not found in "
            f"local directory: {local_data_dir}.\n"
            f"Now downloading from S3 to {local_data_dir}."
        )
        download_core_data(
            dataset=download_core_data_epc_version,
            local_dir=local_data_dir,
            batch=epc_batch,
        )


def get_wales_processed_epc(epc_batch, local_data_dir):
    """Get Welsh EPC data (processed but not deduplicated).

    Args:
        epc_batch (str): which EPC data batch to use in the form `YYYY_QN_complete` or "newest" for latest batch.
        local_data_dir (str): path to local data directory where EPC data stored

    Returns:
        pd.DataFrame: Welsh preprocessed EPC data.
    """
    check_local_epc(
        epc_batch=epc_batch,
        epc_processing_version="preprocessed",
        local_data_dir=local_data_dir,
    )

    wales_epc = load_preprocessed_epc_data(
        data_path=local_data_dir,
        usecols=None,
        version="preprocessed",
        subset="Wales",
        batch=epc_batch,
    )

    return wales_epc


def get_mcs_epc_domestic(mcs_date):
    """Get domestic MCS installations joined with EPC data.

    Args:
        mcs_date (str): which MCS installations data batch to use in the form `YYMMDD`.

    Returns:
        pd.DataFrame: Domestic MCS-EPC data.
    """
    mcs_epc = get_mcs_and_joined_data(epc_version="full", mcs_date=mcs_date)
    mcs_epc["commission_date"] = pd.to_datetime(mcs_epc["commission_date"])
    mcs_epc["INSPECTION_DATE"] = pd.to_datetime(mcs_epc["INSPECTION_DATE"])

    if "end_user_installation_type" in mcs_epc.columns:
        mcs_epc["installation_type"] = mcs_epc["installation_type"].fillna(
            mcs_epc["end_user_installation_type"]
        )
    mcs_epc_domestic = mcs_epc.loc[mcs_epc.installation_type == "Domestic"].reset_index(
        drop=True
    )

    return mcs_epc_domestic


def get_electric_tenure(input_data_path):
    """Get census data on electric heating vs tenure.

    Args:
        input_data_path (str): path to supplementary data directory

    Returns:
        pd.DataFrame: Dataset of tenure counts for properties on electric heating in Wales.
    """
    data_edition = input_data_path.split("/")[-1]
    tenure_path = os.path.join(
        input_data_path, config_file["supplementary_data"][data_edition]["tenure_data"]
    )
    data = pd.read_csv(PROJECT_DIR / tenure_path)

    data = data[
        [
            "Countries",
            "Type of central heating in household (13 categories)",
            "Observation",
            "Tenure of household (5 categories)",
        ]
    ].rename(
        columns={
            "Countries": "country",
            "Type of central heating in household (13 categories)": "heating_type",
            "Observation": "n",
            "Tenure of household (5 categories)": "tenure",
        }
    )

    data = data.loc[
        (data["country"] == "Wales")
        & (data["heating_type"] == "Electric only")
        & (data["tenure"] != "Does not apply")
    ].reset_index(drop=True)

    data["tenure"] = data["tenure"].replace(
        {
            "Owned: Owns outright": "Owned outright",
            "Owned: Owns with a mortgage or loan or shared ownership": "Owned with\nmortgage/loan or\nshared ownership",
            "Private rented or lives rent free": "Private rented or\nrent free",
            "Rented: Social rented": "Social rented",
        }
    )

    return data


def load_wales_df(
    epc_batch, local_data_dir, input_data_path, wales_epc_path, from_csv=True
):
    """Load preprocessed and deduplicated EPC dataset for Wales.
    If data is loaded from all-GB file, the filtered version is saved to csv
    for easier future loading.

    Args:
        epc_batch (str): which EPC data batch to use in the form `YYYY_QN_complete` or "newest" for latest batch.
        local_data_dir (str): path to local data directory where EPC data stored
        input_data_path (str): path to supplementary data directory
        wales_epc_path (str): path to save EPC data filtered for Wales to.
        from_csv (bool, optional): Whether to load Wales subset from saved CSV. Defaults to True.

    Returns:
        pd.DataFrame: EPC data for Wales.
    """
    if from_csv:
        wales_epc = pd.read_csv(wales_epc_path)
    else:
        check_local_epc(
            epc_batch=epc_batch,
            epc_processing_version="preprocessed_and_deduplicated",
            local_data_dir=local_data_dir,
        )

        wales_epc = load_preprocessed_epc_data(
            data_path=local_data_dir,
            subset="Wales",
            batch=epc_batch,
            version="preprocessed_dedupl",
            usecols=[
                "LMK_KEY",
                "INSPECTION_DATE",
                "UPRN",
                "POSTCODE",
                "CURRENT_ENERGY_EFFICIENCY",
                "CURRENT_ENERGY_RATING",
                "WALLS_ENERGY_EFF",
                "FLOOR_ENERGY_EFF",
                "ROOF_ENERGY_EFF",
                "CONSTRUCTION_AGE_BAND",
                "TENURE",
                "TRANSACTION_TYPE",
                "HP_INSTALLED",
            ],
        )

        wales_epc.TENURE = wales_epc.TENURE.replace(
            {
                "owner-occupied": "Owner-occupied",
                "rental (social)": "Socially rented",
                "rental (private)": "Privately rented",
                "unknown": "Unknown",
            }
        )
        # if CONSTRUCTION_AGE_BAND is unknown and TRANSACTION_TYPE is new dwelling,
        # assume construction age is >2007 because EPCs started in 2008
        # This is required for older EPC datasets that were processed before this processing step was added to asf_core_data
        wales_epc["CONSTRUCTION_AGE_BAND"].loc[
            (wales_epc.CONSTRUCTION_AGE_BAND == "unknown")
            & (wales_epc.TRANSACTION_TYPE == "new dwelling")
        ] = "2007 onwards"

        if not os.path.isdir(input_data_path):
            os.makedirs(input_data_path)

        wales_epc.to_csv(os.path.join(input_data_path, wales_epc_path))

    return wales_epc


def load_wales_hp(wales_epc):
    """Load Welsh EPC data filtered to properties with heat pumps.

    Args:
        wales_epc (pd.DataFrame): Wales EPC data.

    Returns:
        pd.DataFrame: EPC data filtered to properties with heat pumps.
    """
    wales_hp = wales_epc.loc[wales_epc.HP_INSTALLED].reset_index(drop=True)

    return wales_hp
