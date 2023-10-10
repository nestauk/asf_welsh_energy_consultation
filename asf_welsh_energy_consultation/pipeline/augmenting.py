# File: asf_welsh_energy_consultation/pipeline/augmenting.py
"""
For processing/augmenting data.
"""


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
