# File: asf_welsh_energy_consultation/pipeline/process_data.py
"""
Functions to process and augment data.
"""

import pandas as pd
import logging

from asf_welsh_energy_consultation.getters import get_data

logger = logging.getLogger(__name__)

# PROCESSING MCS


def get_enhanced_mcs():
    """Get dataset of domestic MCS installations with attached off-gas, country and rurality fields.

    Returns:
        pd.DataFrame: Dataset as described above.
    """
    mcs = get_data.get_mcs_domestic()
    og = get_data.get_offgas()
    countries = get_data.get_countries()
    rural = get_data.get_rurality_by_oa()

    # join with off-gas data
    mcs = mcs.merge(og, on="postcode", how="left")
    mcs["off_gas"] = mcs["off_gas"].fillna("On gas").replace({True: "Off gas"})

    # join with regions in order to filter to Wales
    mcs = mcs.merge(countries, on="postcode", how="left")
    if mcs.country.isna().sum() > 0:
        logger.warning(
            f"{mcs.country.isna().sum()} MCS installation records have no country match. "
            f"Potential loss of data when filtering for Wales."
        )
    mcs = mcs.loc[mcs["country"] == "Wales"].reset_index(drop=True)
    # There will be records with no match
    # Some will be new postcodes (new build developments)
    # and some may be expired postcodes

    # join with rurality data
    mcs = mcs.merge(rural, on="postcode", how="left")
    if mcs.rurality_10_code.isna().sum() > 0:
        logger.warning(
            f"Loss of data: {mcs.rurality_10_code.isna().sum()} Welsh MCS installation records have no rurality code match."
        )

    # add custom rurality column (rurality "type 7": all different types of urban mapped to Urban)
    mcs["rurality_7"] = mcs["rurality_10_label"].replace(
        {
            "Urban city and town": "Urban",
            "Urban major conurbation": "Urban",
            "Urban city and town in a sparse setting": "Urban",
            "Urban minor conurbation": "Urban",
        }
    )

    return mcs


# load enhanced MCS as part of this script, so only needs to be done once
enhanced_mcs = get_enhanced_mcs()


def cumsums_by_variable(variable, new_var_name, data=enhanced_mcs):
    """Process data into a form giving the cumulative total of
    installations on each date for each category of a variable.

    Args:
        variable (str): Variable to split by.
        new_var_name (str): Name of variable in processed dataset.
        data (pd.DataFrame, optional): Base data. Defaults to enhanced_mcs.

    Returns:
        pd.DataFrame: Cumulative totals dataset.
    """

    # calculate total number of installations for each date/category pair
    totals = data.groupby(["commission_date", variable]).size()

    totals = totals.reset_index().rename(columns={0: "sum"})

    idx = pd.date_range(
        totals["commission_date"].min(), totals["commission_date"].max()
    )

    totals = totals.pivot(index="commission_date", columns=variable).fillna(0)

    totals.index = pd.DatetimeIndex(totals.index)

    # reindex, fill in gaps with 0, and take cumulative sums
    cumsums = totals.reindex(idx, fill_value=0).cumsum()
    cumsums.columns = cumsums.columns.droplevel(0)
    cumsums = cumsums.rename_axis(None, axis=1).reset_index(names="date")

    cumsums = pd.melt(
        cumsums,
        id_vars="date",
        value_vars=[col for col in cumsums.columns if col != "date"],
    ).rename(columns={"variable": new_var_name, "value": "Number of heat pumps"})

    cumsums["Number of heat pumps"] = cumsums["Number of heat pumps"].astype(int)

    # remove pre-2015 entries as numbers are small
    cumsums = cumsums.loc[cumsums.date >= "2015-01-01"].reset_index(drop=True)

    return cumsums


# PROCESSING EPC

wales_epc = get_data.get_wales_processed_epc()


def correct_new_dwelling_labels():
    """
    For each unique property in the pandas DataFrame that has more than one record where `TRANSACTION_TYPE == "new dwelling"`,
    replace "new dwelling" with "unknown" for each row except the row with the earliest date.

    Returns:
        pd.DataFrame: Wales EPC certificates
    """
    wales_epc["rank"] = wales_epc.groupby("UPRN")["INSPECTION_DATE"].rank(
        "dense", na_option="bottom"
    )
    df = wales_epc.copy()
    df["TRANSACTION_TYPE"] = df.apply(
        lambda row: "unknown"
        if row["TRANSACTION_TYPE"] == "new dwelling" and row["rank"] > 1
        else row["TRANSACTION_TYPE"],
        axis=1,
    )

    return df


def get_wales_new_builds_epc():
    """Get first EPC certificates for any property labelled as "new dwelling".

    Returns:
        pd.DataFrame: New build EPC certificates.
    """
    wales_epc_new = correct_new_dwelling_labels()

    wales_epc_new = (
        wales_epc_new.loc[wales_epc_new["TRANSACTION_TYPE"] == "new dwelling"][
            ["UPRN", "INSPECTION_DATE", "HP_INSTALLED"]
        ]
        .dropna(subset="INSPECTION_DATE")
        .sort_values("INSPECTION_DATE")
        .groupby("UPRN")
        .head(1)
        .reset_index(drop=True)
    )

    wales_epc_new["year"] = wales_epc_new["INSPECTION_DATE"].dt.year

    return wales_epc_new


def get_new_builds_hp_counts():
    """Get counts of new builds with HPs for each year.

    Returns:
        pd.DataFrame: New build HP counts.
    """
    wales_epc_new = get_wales_new_builds_epc()
    # Requires full year of data so remove most recent year if it doesn't have 12 months of data
    wales_epc_new["INSPECTION_DATE"] = pd.to_datetime(wales_epc_new["INSPECTION_DATE"])
    max_date = wales_epc_new["INSPECTION_DATE"].max()
    max_year = max_date.year
    if max_date != pd.to_datetime(f"{max_year}-12-31"):
        wales_epc_new = wales_epc_new.loc[
            wales_epc_new["INSPECTION_DATE"] < f"{max_year}-01-01"
        ]

    new_hp_counts = (
        wales_epc_new.groupby(["year", "HP_INSTALLED"])
        .size()
        .reset_index()
        .pivot(index="year", columns="HP_INSTALLED")
    )

    new_hp_counts.columns = new_hp_counts.columns.droplevel(0)
    new_hp_counts.columns.name = None
    new_hp_counts = new_hp_counts.rename(columns={False: "Other", True: "Heat pump"})

    new_hp_counts["n"] = new_hp_counts.sum(axis=1)
    new_hp_counts["prop_hp"] = new_hp_counts["Heat pump"] / new_hp_counts["n"]

    new_hp_counts = new_hp_counts.reset_index()

    new_hp_counts = pd.melt(
        new_hp_counts, id_vars="year", value_vars=["Other", "Heat pump"]
    )
    new_hp_counts["year"] = pd.to_datetime(new_hp_counts["year"], format="%Y")

    new_hp_counts = new_hp_counts.rename(columns={"variable": "Heating system"})

    return new_hp_counts


def get_new_builds_hp_cumsums():
    """Get cumulative total of new build HPs.

    Returns:
        pd.DataFrame: New build HPs cumulative totals.
    """
    wales_epc_new = get_wales_new_builds_epc()

    new_hps = wales_epc_new.loc[wales_epc_new["HP_INSTALLED"]].reset_index(drop=True)
    new_hps_sums = (
        new_hps.sort_values("INSPECTION_DATE")
        .groupby("INSPECTION_DATE")["HP_INSTALLED"]
        .sum()
    )

    idx = pd.date_range(new_hps_sums.index.min(), new_hps_sums.index.max())
    new_hps_sums.index = pd.DatetimeIndex(new_hps_sums.index)
    new_hps_sums = new_hps_sums.reindex(idx, fill_value=0)
    new_hps_cumsums = (
        new_hps_sums.cumsum()
        .reset_index()
        .rename(columns={"index": "Date", "HP_INSTALLED": "Number of EPCs"})
    )

    return new_hps_cumsums


def identify_mcs_with_multiple_epc():
    """
    Creates a list of UPRNs that appear more than once in the MCS-EPC `most_relevant` dataset. UPRNs that appear more than once
    indicate a single MCS installation joined to multiple EPC records.

    Returns:
        List of duplicate UPRNs.
    """
    mcs_epc_most_relevant = get_data.get_mcs_and_joined_data(
        epc_version="most_relevant"
    )
    mcs_epc_most_relevant["count"] = 1
    uprn_count = mcs_epc_most_relevant.groupby(["UPRN"])["count"].sum().reset_index()
    duplicate_uprns = uprn_count[uprn_count["count"] > 1]["UPRN"].to_list()

    return duplicate_uprns


def mcs_epc_first_records():
    """Get first records from fully joined MCS-EPC dataset. Note: all rows with UPRNs associated with multiple MCS installations
    in the dataset are removed to avoid double counting.

    Returns:
        pd.DataFrame: MCS records joined with first EPC.
    """
    mcs_epc = get_data.get_mcs_epc_domestic()
    duplicate_uprns = identify_mcs_with_multiple_epc()
    logger.warning(
        f"{len(duplicate_uprns)} duplicate UPRNs identified. Removing all rows with a duplicate UPRN from MCS-EPC fully joined dataset."
    )
    mcs_epc = mcs_epc.loc[~mcs_epc.UPRN.isin(duplicate_uprns)]

    regions = get_data.get_countries()

    mcs_epc = mcs_epc.merge(regions, on="postcode", how="left")
    if mcs_epc.country.isna().sum() > 0:
        logger.warning(
            f"{mcs_epc.country.isna().sum()} joined MCS-EPC records have no country match. "
            f"Potential loss of data when filtering for Wales."
        )
    mcs_epc = mcs_epc.loc[mcs_epc["country"] == "Wales"].reset_index(drop=True)

    first_records = (
        mcs_epc.sort_values("INSPECTION_DATE").groupby("original_mcs_index").head(1)
    )

    return first_records


# PROCESSING JOINED MCS-EPC


def add_hp_when_built_column(first_records):
    """Add a column to a DataFrame indicating that the property had a HP when it was built.

    Args:
        first_records (pd.DataFrame): MCS records joined to first EPC records.

    Returns:
        pd.DataFrame: Dataset with added "assumed_hp_when_built" column.
    """

    first_records["diff_epc_to_mcs"] = (
        first_records["commission_date"] - first_records["INSPECTION_DATE"]
    ).dt.days

    # Assume dwelling was built with HP if:
    # - first EPC shows it as a new dwelling
    # - time difference between EPC inspection when dwelling was built and HP installation is less than 1 year
    first_records["assumed_hp_when_built"] = (
        first_records["TRANSACTION_TYPE"] == "new dwelling"
    ) & (first_records["diff_epc_to_mcs"] < 365)

    return first_records


def get_mcs_retrofits():
    """Get dataset of MCS installations assumed to be retrofits (domestic and EPC indicates no HP when built or not joined to EPC)

    Returns:
        pd.DataFrame: MCS retrofit records.
    """
    first_records = mcs_epc_first_records()
    first_records = add_hp_when_built_column(first_records)

    hp_when_built_indices = first_records.loc[first_records["assumed_hp_when_built"]][
        "original_mcs_index"
    ]
    # note: for properties not joined to EPC, assumed_hp_when_built is False
    # this makes sense because if they had been built with a HP we would expect them to appear in EPC
    # due to new build EPC requirements

    enhanced_mcs = get_enhanced_mcs()
    mcs_retrofits = enhanced_mcs.loc[~enhanced_mcs.index.isin(hp_when_built_indices)]

    return mcs_retrofits


def generate_age_data(wales_df):
    """Generate table of proportion of properties in each age band.
    Also includes average energy efficiency for each age band.

    Args:
        wales_df (pd.DataFrame): EPC data with "CONSTRUCTION_AGE_BAND" column.

    Returns:
        pd.DataFrame: Age band proportions and efficiencies.
    """
    age_props = (
        wales_df.loc[
            wales_df.CONSTRUCTION_AGE_BAND != "unknown"
        ].CONSTRUCTION_AGE_BAND.value_counts(normalize=True)
        * 100
    )
    age_props = age_props.reset_index()
    age_props = age_props.rename(
        columns={
            "index": "CONSTRUCTION_AGE_BAND",
            "CONSTRUCTION_AGE_BAND": "percentage",
        }
    )
    ages_efficiencies = (
        wales_df.groupby("CONSTRUCTION_AGE_BAND")["CURRENT_ENERGY_EFFICIENCY"]
        .mean()
        .reset_index()
    )
    age_data = age_props.merge(ages_efficiencies, on="CONSTRUCTION_AGE_BAND")
    age_data["CONSTRUCTION_AGE_BAND"] = age_data["CONSTRUCTION_AGE_BAND"].replace(
        {"England and Wales: before 1900": "Pre-1900"}
    )
    age_data = (
        age_data.set_index("CONSTRUCTION_AGE_BAND")
        .loc[
            [
                "Pre-1900",
                "1900-1929",
                "1930-1949",
                "1950-1966",
                "1965-1975",
                "1976-1983",
                "1983-1991",
                "1991-1998",
                "1996-2002",
                "2003-2007",
                "2007 onwards",
            ]
        ]
        .reset_index()
    )
    age_data["CURRENT_ENERGY_EFFICIENCY"] = age_data["CURRENT_ENERGY_EFFICIENCY"].round(
        1
    )
    age_data["cumul_prop"] = age_data["percentage"].cumsum()

    return age_data


def get_installations_per_year():
    """
    Get MCS installations per year for Wales.
    Returns:
        pandas.DataFrame of MCS installations per year in Wales.

    """
    mcs = get_enhanced_mcs()
    mcs["n"] = 1
    mcs["year"] = pd.to_datetime(mcs["commission_date"]).dt.year
    installations_by_year = mcs.groupby("year")["n"].sum().reset_index()

    # Sort by date ascending
    installations_by_year = installations_by_year.sort_values("year")
    installations_by_year = installations_by_year.rename(
        columns={"commission_date": "date"}
    )

    return installations_by_year


def mean_installations_per_year(min_year, max_year):
    """
    Get mean average MCS installations in Wales per year for given date range.
    Args:
        min_year: Minimum year (exclusive)
        max_year: Maximum year (exclusive)

    Returns:
        int: Mean average MCS installations per year.
    """
    installations_by_year = get_installations_per_year()
    subset = installations_by_year[
        (installations_by_year["year"] > min_year)
        & (installations_by_year["year"] < max_year)
    ]

    return subset["n"].mean()


def median_installations_per_year(min_year, max_year):
    """
    Get median average MCS installations in Wales per year for given date range.
    Args:
        min_year: Minimum year (exclusive)
        max_year: Maximum year (exclusive)

    Returns:
        int: Median average MCS installations per year.
    """
    installations_by_year = get_installations_per_year()
    subset = installations_by_year[
        (installations_by_year["year"] > min_year)
        & (installations_by_year["year"] < max_year)
    ]

    return subset["n"].median()


def get_total_rural_and_urban_properties():
    """
    Get total count of properties in Wales in urban vs rural locations.

    Returns:
        dict: Percent of rural and urban properties in Wales.
    """
    rural = get_data.get_rurality()
    dwellings = get_data.get_dwelling_data()

    df = dwellings.merge(rural, how="left", on="lsoa_code")
    df = df[df["country"] == "W"]
    rurality = df.groupby("rural_2")["total_dwellings"].sum().to_dict()
    rurality_pct_dict = {
        "Rural": (rurality["Rural"] / (rurality["Rural"] + rurality["Urban"])) * 100,
        "Urban": (rurality["Urban"] / (rurality["Rural"] + rurality["Urban"])) * 100,
    }

    return rurality_pct_dict


def get_total_on_off_gas_postcodes():
    """
    Get total count of postcodes in Wales which are on- vs off-gas.

    Returns:
        dict: Percent of on- and off-gas postcodes in Wales.
    """

    og = get_data.get_offgas()
    oa = get_data.get_postcode_to_oa()

    postcodes_og = oa.merge(og, how="left", on="postcode")

    # LSOA code used to get country code and filter for Wales
    postcodes_og["country"] = postcodes_og["lsoa_code"].apply(lambda x: str(x)[0])
    wales_og = postcodes_og[postcodes_og["country"] == "W"]

    # Any postcodes not in off gas dataset have NA values in 'off_gas' col
    # We assume the remaining postcodes are on gas and fillna with 'on gas'
    wales_og["off_gas"] = (
        wales_og["off_gas"].fillna("On gas").replace({True: "Off gas"})
    )

    # Calculate % of postcodes on and off gas
    wales_og_dict = wales_og["off_gas"].value_counts(dropna=False).to_dict()
    wales_postcodes_og_pct_dict = {
        "Off gas": (
            wales_og_dict["Off gas"]
            / (wales_og_dict["Off gas"] + wales_og_dict["On gas"])
        )
        * 100,
        "On gas": (
            wales_og_dict["On gas"]
            / (wales_og_dict["Off gas"] + wales_og_dict["On gas"])
        )
        * 100,
    }

    return wales_postcodes_og_pct_dict
