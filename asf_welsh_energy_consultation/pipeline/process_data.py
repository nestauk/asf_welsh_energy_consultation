import pandas as pd

from asf_welsh_energy_consultation.getters.get_data import *


def get_enhanced_mcs():
    mcs = get_mcs_domestic()
    og = get_offgas()
    regions = get_regions()
    rural = get_rurality()

    # join with off-gas data
    mcs = mcs.merge(og, on="postcode", how="left")
    mcs["off_gas"] = mcs["off_gas"].fillna("On gas").replace({True: "Off gas"})

    # join with regions in order to filter to Wales
    mcs = mcs.merge(regions, on="postcode", how="left")
    mcs = mcs.loc[mcs["country"] == "Wales"].reset_index(drop=True)

    # mask clear capacity outliers and convert to MW
    mcs["capacity"] = mcs["capacity"].mask(mcs["capacity"] > 100)
    mcs["capacity_mw"] = mcs["capacity"] / 1000

    # join with rurality data
    mcs = mcs.merge(rural, on="postcode", how="left")
    # TODO: check data missingness!

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


mcs = get_enhanced_mcs()


def cumsums_by_variable(variable, new_var_name, capacity=None):
    data = mcs

    # calculate total number of installations (or total capacity) for each date
    if capacity is not None:
        totals = data.groupby(["commission_date", variable])[capacity].sum()
    else:
        totals = data.groupby(["commission_date", variable]).size()

    totals = totals.reset_index().rename(columns={0: "sum"})

    idx = pd.date_range(
        totals["commission_date"].min(), totals["commission_date"].max()
    )

    totals = totals.pivot(index="commission_date", columns=variable).fillna(0)

    totals.index = pd.DatetimeIndex(totals.index)

    cumsums = totals.reindex(idx, fill_value=0).cumsum()
    cumsums.columns = cumsums.columns.droplevel(0)
    cumsums = cumsums.rename_axis(None, axis=1).reset_index(names="date")

    value_var = "Total capacity" if capacity else "Number of heat pumps"

    cumsums = pd.melt(
        cumsums,
        id_vars="date",
        value_vars=[col for col in cumsums.columns if col != "date"],
    ).rename(columns={"variable": new_var_name, "value": value_var})

    if capacity is None:
        cumsums[value_var] = cumsums[value_var].astype(int)

    cumsums = cumsums.loc[cumsums.date >= "2015-01-01"].reset_index(drop=True)

    return cumsums


def get_average_capacity():
    mcs_cap = mcs[["commission_date", "capacity"]]

    mcs_cap["capacity"] = mcs_cap["capacity"].mask(mcs_cap["capacity"] > 100)
    mcs_cap["commission_date"] = pd.to_datetime(mcs_cap["commission_date"])
    mcs_cap["year"] = mcs_cap["commission_date"].dt.year

    cap_medians = (
        mcs_cap.groupby(["year"])["capacity"]
        .agg(["median", "mean", "count"])
        .reset_index()
    )

    return cap_medians


wales_epc = get_wales_epc()


def get_wales_epc_new():
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
    wales_epc_new = get_wales_epc_new()

    new_hp_counts = (
        wales_epc_new.groupby(["year", "HP_INSTALLED"])
        .size()
        .reset_index()
        .pivot(index="year", columns="HP_INSTALLED")
    )

    new_hp_counts.columns = new_hp_counts.columns.droplevel(0)
    new_hp_counts.columns.name = None
    new_hp_counts = new_hp_counts.rename(columns={False: "n_not_hp", True: "n_hp"})

    new_hp_counts["n"] = new_hp_counts.sum(axis=1)
    new_hp_counts["prop_hp"] = new_hp_counts["n_hp"] / new_hp_counts["n"]

    new_builds = new_hp_counts.reset_index()

    new_builds = pd.melt(new_builds, id_vars="year", value_vars=["n_not_hp", "n_hp"])
    new_builds["year"] = pd.to_datetime(new_builds["year"], format="%Y")

    new_builds = new_builds.rename(columns={"variable": "Heating system"})
    new_builds["Heating system"] = new_builds["Heating system"].replace(
        {"n_hp": "Heat pump", "n_not_hp": "Other"}
    )

    return new_builds


def get_new_hp_cumsums():
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
    mcs_epc = get_mcs_epc()
    regions = get_regions()

    mcs_epc = mcs_epc.merge(regions, on="postcode", how="left")
    mcs_epc = mcs_epc.loc[mcs_epc["country"] == "Wales"].reset_index(drop=True)

    first_records = (
        mcs_epc.sort_values("INSPECTION_DATE").groupby("original_mcs_index").head(1)
    )

    return first_records


def mcs_epc_capacities():
    first_records = mcs_epc_first_records()

    first_records["diff_epc_to_mcs"] = (
        first_records["commission_date"] - first_records["INSPECTION_DATE"]
    ).dt.days

    # Assume dwelling was built with HP if:
    # - first EPC shows it as a new dwelling
    # - time difference between EPC inspection when dwelling was built and HP installation is less than 1 year
    first_records["assumed_hp_when_built"] = (
        first_records["TRANSACTION_TYPE"] == "new dwelling"
    ) & (first_records["diff_epc_to_mcs"] < 365)

    # assume that records without an EPC link are retrofits, as all new builds should be in EPC database

    capacities = first_records.groupby("assumed_hp_when_built")["capacity"].agg(
        ["mean", "median", "count"]
    )

    return capacities


def capacities_by_built_form():
    first_records = mcs_epc_first_records()

    built_form_capacities = (
        first_records.loc[
            (first_records["PROPERTY_TYPE"].isin(["House", "Bungalow"]))
            & (
                first_records["BUILT_FORM"].isin(
                    ["Detached", "End-Terrace", "Mid-Terrace", "Semi-Detached"]
                )
            )
        ]
        .groupby("BUILT_FORM")["capacity"]
        .agg(["mean", "median", "count"])
    )

    return built_form_capacities
