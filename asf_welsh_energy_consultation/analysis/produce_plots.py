# File: asf_welsh_energy_consultation/analysis/produce_plots.py
"""
Script to produce plots.
"""

import altair as alt

from asf_welsh_energy_consultation.getters.get_data import get_electric_tenure
from asf_welsh_energy_consultation.pipeline.process_data import *
from asf_welsh_energy_consultation.utils.formatting import format_number
from asf_welsh_energy_consultation.getters.get_data import load_wales_df, load_wales_hp
from asf_welsh_energy_consultation.pipeline.augmenting import generate_age_data
from asf_welsh_energy_consultation.pipeline.plotting import (
    proportions_bar_chart,
    age_prop_chart,
    time_series_comparison,
)

from nesta_ds_utils.viz.altair.formatting import setup_theme

alt.data_transformers.disable_max_rows()
setup_theme()

output_folder = "outputs/figures/"

if not os.path.isdir(output_folder):
    os.makedirs(output_folder)


if __name__ == "__main__":
    # ======================================================
    # MCS installations, by off-gas status

    installations_by_gas_status = cumsums_by_variable("off_gas", "Gas status")

    installations_by_gas_status_chart = time_series_comparison(
        data=installations_by_gas_status,
        title=[
            "Fig. 4: Cumulative number of MCS certified heat pump installations in Welsh homes",
            "located in off- and on-gas postcodes",
        ],
        y_var="Number of heat pumps:Q",
        y_title="Number of heat pump installations",
        color_var="Gas status:N",
    ).configure_title(fontSize=20)

    installations_by_gas_status_chart.save(
        output_folder + "installations_by_gas_status.html"
    )

    # ======================================================
    # MCS installations, by rurality

    installations_by_rurality = cumsums_by_variable("rurality_2_label", "Rurality")

    installations_by_rurality_chart = time_series_comparison(
        data=installations_by_rurality,
        title=[
            "Cumulative number of MCS certified heat pump installations",
            "in Welsh homes located in rural vs urban postcodes",
        ],
        y_var="Number of heat pumps:Q",
        y_title="Number of heat pump installations",
        color_var="Rurality:N",
        domain_max=installations_by_rurality.date.max(),
    )

    installations_by_rurality_chart.save(
        output_folder + "installations_by_rurality.html"
    )

    # ======================================================
    # Proportions of new builds that have heat pumps

    new_build_hp_proportion = get_new_hp_counts()

    new_build_hp_proportion_chart = (
        alt.Chart(
            new_build_hp_proportion,
            title="New-build EPCs registered for Welsh properties, split by heating system",
        )
        .mark_bar(size=20)
        .encode(
            x=alt.X(
                # domain ensures good margin at left/right of chart
                "year",
                title="Year",
                scale=alt.Scale(domain=["2007-07-01", "2023-06-01"]),
            ),
            y=alt.Y("sum(value)", title="Number of EPCs"),
            # want heat pumps to be at the bottom of each bar - hacky but works
            color=alt.Color("Heating system"),
            order=alt.Order("Heating system"),
        )
        .properties(width=600, height=300)
    )

    new_build_hp_proportion_chart.save(output_folder + "new_build_hp_proportion.html")

    # ======================================================
    # Cumulative number of new builds with heat pumps

    new_build_hp_cumulative = get_new_hp_cumsums()

    new_build_hp_cumulative_chart = (
        alt.Chart(
            new_build_hp_cumulative,
            title=[
                "Cumulative total of EPC registrations for new builds",
                "with heat pumps in Wales since 2008",
            ],
        )
        .mark_line()
        .encode(
            x="Date",
            y="Number of EPCs",
        )
        .properties(width=600, height=300)
    )

    new_build_hp_cumulative_chart.save(output_folder + "new_build_hp_cumulative.html")

    # ======================================================
    # Cumulative MCS retrofits

    ret = get_mcs_retrofits()
    ret_cumsums = cumsums_by_variable("country", "wales_col", data=ret)
    # this function works without separating by category - 'wales_col' is a whole column of "Wales" (not used)

    cumulative_retrofits_chart = (
        alt.Chart(
            ret_cumsums,
            title="Cumulative number of MCS certified heat pump retrofits in Wales",
        )
        .mark_line()
        .encode(
            x=alt.X(
                "date",
                title="Date",
                scale=alt.Scale(domain=["2015-01-01", ret_cumsums.date.max()]),
            ),
            y="Number of heat pumps",
        )
        .properties(width=600, height=300)
    )

    cumulative_retrofits_chart.save(output_folder + "cumulative_retrofits.html")

    # ======================================================
    # Split of properties on electric heating by tenure

    electric_tenure = get_electric_tenure()
    N = electric_tenure["n"].sum()

    electric_tenure_chart = (
        alt.Chart(
            electric_tenure,
            title="Fig. 2: Properties in Wales with only electric heating, split by tenure (N = "
            + format_number(N)
            + ")",
        )
        .mark_bar()
        .encode(
            x=alt.X("tenure", title="Tenure", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("n", title="Number of properties"),
        )
        .configure(lineBreak="\n")
        .properties(width=600, height=300)
    ).configure_title(fontSize=20)

    electric_tenure_chart.save(output_folder + "electric_tenure.html")

    # ======================================================
    # Original plots and stats

    wales_df = load_wales_df(from_csv=False)
    wales_hp = load_wales_hp(wales_df)

    # English plots

    # Key statistics
    print("Number of heat pumps:", len(wales_hp))
    print("Number of properties in EPC:", len(wales_df))
    print(
        "Estimated percentage of properties with a heat pump:",
        "{:.2%}".format(len(wales_hp) / len(wales_df)),
    )
    print(wales_hp.TENURE.value_counts(normalize=True))

    epc_c_or_above_and_good_walls = wales_df.loc[
        wales_df["CURRENT_ENERGY_RATING"].isin(["A", "B", "C"])
        & wales_df["WALLS_ENERGY_EFF"].isin(["Good", "Very Good"])
    ]

    epc_c_or_above_and_good_walls_and_roof = epc_c_or_above_and_good_walls.loc[
        epc_c_or_above_and_good_walls["ROOF_ENERGY_EFF"].isin(["Good", "Very Good"])
    ]

    print(
        "Number of EPC C+ properties with good or very good wall insulation:",
        len(epc_c_or_above_and_good_walls),
    )
    print(
        "As a proportion of properties in EPC:",
        len(epc_c_or_above_and_good_walls) / len(wales_df),
    )

    print(
        "\nNumber of EPC C+ properties with good or very good wall and roof insulation:",
        len(epc_c_or_above_and_good_walls_and_roof),
    )
    print(
        "As a proportion of properties in EPC:",
        len(epc_c_or_above_and_good_walls_and_roof) / len(wales_df),
    )

    # Tenure of Welsh HPs
    proportions_bar_chart(
        wales_hp,
        "TENURE",
        "Fig. 3: Tenure of Welsh properties with heat pumps",
        "Tenure",
        "Percentage of properties",
        filename="hp_tenure",
        x_type="tenure",
        expand_y=True,
    )

    # EPC, all
    proportions_bar_chart(
        # only one unknown EPC property so fine to just remove it
        wales_df.loc[wales_df.CURRENT_ENERGY_RATING != "unknown"],
        "CURRENT_ENERGY_RATING",
        "Fig. 5: EPC ratings of all Welsh properties",
        "Energy efficiency rating",
        "Percentage of properties",
        filename="epc_all",
        x_type="other",
    )

    # EPC, private sector with HPs
    proportions_bar_chart(
        wales_hp.loc[wales_hp.TENURE.isin(["Owner-occupied", "Privately rented"])],
        "CURRENT_ENERGY_RATING",
        [
            "Fig. 6: EPC ratings of owner-occupied and privately rented",
            "Welsh properties with heat pumps",
        ],
        "Energy efficiency rating",
        "Percentage of properties",
        filename="epc_hp_private",
        x_type="other",
    )

    # EPCs, private sector with retrofitted HPs
    proportions_bar_chart(
        wales_hp.loc[
            wales_hp.TENURE.isin(["Owner-occupied", "Privately rented"])
            & (wales_hp.CONSTRUCTION_AGE_BAND != "2007 onwards")
        ],
        "CURRENT_ENERGY_RATING",
        [
            "Fig. 7: EPC ratings of owner-occupied and privately rented",
            "Welsh properties with heat pumps, built pre-2007",
        ],
        "Energy efficiency rating",
        "Percentage of properties",
        filename="epc_hp_private_retrofit",
        x_type="other",
    )

    age_data = generate_age_data(wales_df)
    age_prop_chart(
        age_data, "Fig. 9: Construction age bands and energy efficiencies", "age_prop"
    )

    ## Welsh plots

    welsh_replacements = {
        "TENURE": {
            "Owner-occupied": "Perchen-feddiannaeth",
            "Socially rented": "Rhentu cymdeithasol",
            "Privately rented": "Rhentu preifat",
            "Unknown": "Anhysbys",
        },
        "CONSTRUCTION_AGE_BAND": {
            "England and Wales: before 1900": "Cyn 1900",
            "Pre-1900": "Cyn 1900",
            "2007 onwards": "2007 ymlaen",
            "unknown": "Anhysbys",
        },
    }

    for df in [wales_df, wales_hp, age_data]:
        for col in ["TENURE", "CONSTRUCTION_AGE_BAND"]:
            if col in df.columns:
                df[col] = df[col].replace(welsh_replacements[col])

    # Tenure of Welsh HPs
    proportions_bar_chart(
        wales_hp,
        "TENURE",
        "Ffig. 4: Deiliadaeth eiddo â phympiau gwres yng Nghymru",
        "Deiliadaeth",
        "Canran yr eiddo",
        filename="hp_tenure_welsh",
        x_type="tenure",
        expand_y=True,
        language="welsh",
    )

    # EPC, all
    proportions_bar_chart(
        wales_df.loc[wales_df.CURRENT_ENERGY_RATING != "unknown"],
        "CURRENT_ENERGY_RATING",
        "Ffig. 6: Sgoriau EPC holl eiddo Cymru",
        "Sgôr effeithlonrwydd ynni",
        "Canran yr eiddo",
        filename="epc_all_welsh",
        x_type="other",
        language="welsh",
    )

    # EPC, private sector with HPs
    proportions_bar_chart(
        wales_hp.loc[wales_hp.TENURE.isin(["Perchen-feddiannaeth", "Rhentu preifat"])],
        "CURRENT_ENERGY_RATING",
        [
            "Ffig. 7: Sgoriau EPC eiddo perchen-feddiannaeth a",
            "rhentu preifat Cymru sydd â phympiau gwres",
        ],
        "Sgôr effeithlonrwydd ynni",
        "Canran yr eiddo",
        filename="epc_hp_private_welsh",
        x_type="other",
        language="welsh",
    )

    # EPCs, private sector with retrofitted HPs
    proportions_bar_chart(
        wales_hp.loc[
            wales_hp.TENURE.isin(["Perchen-feddiannaeth", "Rhentu preifat"])
            & (wales_hp.CONSTRUCTION_AGE_BAND != "2007 ymlaen")
        ],
        "CURRENT_ENERGY_RATING",
        [
            "Ffig. 8: Sgoriau EPC eiddo perchen-feddiannaeth a rhentu prifat",
            "Cymru sydd â phympiau gwres, a adeiladwyd cyn 2007",
        ],
        "Sgôr effeithlonrwydd ynni",
        "Canran yr eiddo",
        filename="epc_hp_private_retrofit_welsh",
        x_type="other",
        language="welsh",
    )

    # Ages and EPC ratings
    age_prop_chart(
        age_data,
        "Ffig. 9: Bandiau oedran adeiladu ac effeithlonrwydd ynni",
        "age_prop_welsh",
        language="welsh",
    )
