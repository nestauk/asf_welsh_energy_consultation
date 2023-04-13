import pandas as pd

from asf_welsh_energy_consultation.getters.get_data import *


# PROCESSING MCS


def get_enhanced_mcs():
    """Get dataset of domestic MCS installations with attached off-gas, country and rurality fields.

    Returns:
        pd.DataFrame: Dataset as described above.
    """
    mcs = get_mcs_domestic()
    og = get_offgas()
    countries = get_countries()
    rural = get_rurality()

    # join with off-gas data
    mcs = mcs.merge(og, on="postcode", how="left")
    mcs["off_gas"] = mcs["off_gas"].fillna("On gas").replace({True: "Off gas"})

    # join with regions in order to filter to Wales
    mcs = mcs.merge(countries, on="postcode", how="left")
    mcs = mcs.loc[mcs["country"] == "Wales"].reset_index(drop=True)
    # 1203 records with no match - 273 are Northern Ireland which leaves 918
    # Some will be new postcodes (new build developments)
    # and some may be expired postcodes
    # In future, implement new solution that uses outward codes

    # join with rurality data
    mcs = mcs.merge(rural, on="postcode", how="left")
    # only 13 postcodes lost in this merge

    # add custom rurality column
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
mcs = get_enhanced_mcs()


def cumsums_by_variable(variable, new_var_name, data=mcs):
    """Process data into a form giving the cumulative total of
    installations on each date for each category of a variable.

    Args:
        variable (str): Variable to split by.
        new_var_name (str): Name of variable in processed dataset.
        data (pd.DataFrame, optional): Base data. Defaults to mcs.

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

wales_epc = get_wales_epc()


def get_wales_epc_new():
    """Get first EPC certificates for any property labelled as "new dwelling".

    Returns:
        pd.DataFrame: New build EPC certificates.
    """
    wales_epc_new = (
        wales_epc.loc[wales_epc["TRANSACTION_TYPE"] == "new dwelling"][
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


def new_hp_counts():
    """Get counts of new builds with HPs for each year.

    Returns:
        pd.DataFrame: New build HP counts.
    """
    wales_epc_new = get_wales_epc_new()
    # 2023 not yet complete so drop any post-2022 data
    wales_epc_new = wales_epc_new.loc[wales_epc_new["INSPECTION_DATE"] < "2023-01-01"]

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

    new_builds = new_hp_counts.reset_index()

    new_builds = pd.melt(new_builds, id_vars="year", value_vars=["Other", "Heat pump"])
    new_builds["year"] = pd.to_datetime(new_builds["year"], format="%Y")

    new_builds = new_builds.rename(columns={"variable": "Heating system"})

    return new_builds


def get_new_hp_cumsums():
    """Get cumulative total of new build HPs.

    Returns:
        pd.DataFrame: New build HPs cumulative totals.
    """
    wales_epc_new = get_wales_epc_new()

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


def mcs_epc_first_records():
    """Get first records from fully joined MCS-EPC dataset.

    Returns:
        pd.DataFrame: MCS records joined with first EPC.
    """
    mcs_epc = get_mcs_epc_domestic()
    regions = get_countries()

    mcs_epc = mcs_epc.merge(regions, on="postcode", how="left")
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

    mcs = get_enhanced_mcs()
    mcs_retrofits = mcs.loc[~mcs.index.isin(hp_when_built_indices)]

    return mcs_retrofits
