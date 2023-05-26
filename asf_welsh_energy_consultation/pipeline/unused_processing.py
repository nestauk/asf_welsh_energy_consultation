def cumsums_by_variable(variable, new_var_name, data=mcs, capacity=None):
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


def mcs_epc_capacities():
    first_records = mcs_epc_first_records()
    first_records = add_hp_when_built_column(first_records)

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


# mask clear capacity outliers and convert to MW
# mcs["capacity"] = mcs["capacity"].mask(mcs["capacity"] > 100)
# mcs["capacity_mw"] = mcs["capacity"] / 1000

# mcs_epc["capacity"] = mcs_epc["capacity"].mask(mcs_epc["capacity"] > 100)
