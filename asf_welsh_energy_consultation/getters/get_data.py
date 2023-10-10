# File: asf_welsh_energy_consultation/getters/get_data.py
"""
Data getters.
"""

from asf_welsh_energy_consultation import PROJECT_DIR
from asf_welsh_energy_consultation import config

from asf_core_data import load_preprocessed_epc_data, get_mcs_installations
from asf_core_data.getters.mcs_getters.get_mcs_installations import (
    get_processed_installations_data_by_batch,
)
from asf_core_data.getters.epc.data_batches import get_batch_path
from asf_core_data.config import base_config
from asf_core_data.getters.data_getters import download_core_data

import pandas as pd
import numpy as np
import os

from argparse import ArgumentParser

epc_processing_version = config["epc_data_config"]["epc_processing_version"]
download_core_data_epc_version = config["epc_data_config"][
    "download_core_data_epc_version"
]

postcode_path = "inputs/data/postcodes"
regions_path = "inputs/data/regions.csv"
off_gas_path = "inputs/data/off-gas-live-postcodes-2022.xlsx"
oa_path = "inputs/data/postcode_to_output_area.csv"
rurality_path = "inputs/data/rurality.ods"
tenure_path = "inputs/data/tenure.csv"


def create_argparser():
    """
    Creates an Argument Parser that can receive the following arguments:
    - local_data_dir
    - epc_batch
    - mcs_batch

    Returns:
        Argument Parser
    """
    parser = ArgumentParser()

    parser.add_argument(
        "--local_data_dir",
        help="Local directory where EPC data is/will be stored",
        type=str,
    )

    parser.add_argument(
        "--epc_batch",
        help='Specifies which EPC data batch to use in the form `YYYY_[Quarter]_complete`. Defaults to "newest"',
        default="newest",
        type=str,
    )

    parser.add_argument(
        "--mcs_batch",
        help="Specifies which MCS installations data batch to use. Only date required in YYMMDD format. "
        'Defaults to "newest"',
        default="newest",
        type=str,
    )

    return parser


def get_args():
    """
    Get arguments from Argument Parser.

    Returns:
        List of arguments.
    """
    parser = create_argparser()

    return parser.parse_args()


arguments = get_args()
LOCAL_DATA_DIR = arguments.local_data_dir


def get_mcs_and_joined_data():
    """
    Get cleaned MCS data, and cleaned MCS data fully joined with EPC dataset up to date specified in args.

    Returns:
        MCS dataset and MCS dataset fully joined with EPC dataset
    """
    mcs_date = arguments.mcs_batch

    # Get latest MCS data or batch specified in args
    if mcs_date == "newest":
        mcs_data = get_mcs_installations(epc_version="none")
        mcs_epc_full_data = get_mcs_installations(epc_version="full")
    else:
        mcs_data = get_processed_installations_data_by_batch(
            batch_date=mcs_date, epc_version="none"
        )
        mcs_epc_full_data = get_processed_installations_data_by_batch(
            batch_date=mcs_date, epc_version="full"
        )
    return mcs_data, mcs_epc_full_data


# Get MCS data from S3
mcs_installations_data, mcs_installations_epc_full_data = get_mcs_and_joined_data()


def get_countries():
    """Get lookup table of postcodes to countries.

    Returns:
        Dataframe: Postcode geographic data.
    """
    # Read postcode data
    postcode_folder = PROJECT_DIR / postcode_path
    files = os.listdir(postcode_folder)
    postcode_df = pd.concat(
        # Only need postcode and LA code cols
        (pd.read_csv(postcode_folder / file, header=None)[[0, 8]] for file in files),
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
        " ": np.nan,
    }
    postcode_df["country"] = (
        postcode_df["la_code"].fillna(" ").apply(lambda code: country_dict[code[0]])
    )

    return postcode_df


def get_mcs_domestic():
    """Get domestic MCS data.

    Returns:
        pd.DataFrame: Domestic MCS installation records.
    """
    mcs = mcs_installations_data

    # Older MCS data batches will need this processing step
    # Newer batches have been through this processing step already in the pipeline
    if "end_user_installation_type" in mcs.columns:
        mcs["installation_type"] = mcs["installation_type"].fillna(
            mcs["end_user_installation_type"]
        )
        mcs = mcs.drop(columns=["end_user_installation_type"])

    mcs_domestic = mcs.loc[mcs.installation_type == "Domestic"].reset_index(drop=True)

    return mcs_domestic


def get_offgas():
    """Get dataset of off-gas-grid postcodes.

    Returns:
        pd.DataFrame: Dataframe containing off-gas postcodes.
    """
    og = pd.read_excel(
        PROJECT_DIR / off_gas_path,
        sheet_name="Off Gas Live PostCodes 22",
    )

    og = og.rename(columns={"Post Code": "postcode"})
    og["postcode"] = og["postcode"].str.replace(" ", "")
    og["off_gas"] = True

    return og


def get_rurality():
    """Get dataset of postcodes and their rurality indices.
    Two codes are used - the more specific 10-fold code, and the less specific
    two-fold code ("rural"/"urban").

    Returns:
        pd.DataFrame: Dataset with postcodes and ruralities.
    """
    oa = pd.read_csv(
        PROJECT_DIR / oa_path, encoding="latin-1"
    )  # latin-1 as otherwise invalid byte

    oa = oa[["pcd7", "oa11cd"]].rename(
        columns={"pcd7": "postcode", "oa11cd": "oa_code"}
    )
    oa["postcode"] = oa["postcode"].str.replace(" ", "")

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


def check_local_epc():
    """
    Checks local directory for relevant EPC batch and downloads relevant EPC batch from S3 to local directory if not found.

    """
    epc_batch = arguments.epc_batch

    local_epc_output_dir = os.path.join(
        LOCAL_DATA_DIR, base_config.OUTPUT_DATA_PATH, "{}"
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
        print(
            f"EPC data; batch: `{local_epc_batch_path.parts[-2]}`; version: `{epc_processing_version}` not found in "
            f"local directory: {LOCAL_DATA_DIR}.\n"
            f"Now downloading from S3 to {LOCAL_DATA_DIR}."
        )
        download_core_data(
            dataset=download_core_data_epc_version,
            local_dir=LOCAL_DATA_DIR,
            batch=epc_batch,
        )


def get_wales_epc():
    """Get Welsh EPC data (processed but not deduplicated).

    Returns:
        pd.DataFrame: Welsh preprocessed EPC data.
    """
    check_local_epc()

    epc_batch = arguments.epc_batch

    wales_epc = load_preprocessed_epc_data(
        data_path=LOCAL_DATA_DIR,
        usecols=None,
        version=epc_processing_version,
        subset="Wales",
        batch=epc_batch,
    )

    return wales_epc


def get_mcs_epc_domestic():
    """Get domestic MCS installations joined with EPC data.

    Returns:
        pd.DataFrame: Domestic MCS-EPC data.
    """
    mcs_epc = mcs_installations_epc_full_data
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


def get_electric_tenure():
    """Get census 2021 data on electric heating vs tenure.

    Returns:
        pd.DataFrame: Dataset of tenure counts for properties on electric heating.
    """
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
