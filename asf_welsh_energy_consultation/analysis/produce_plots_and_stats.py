# File: asf_welsh_energy_consultation/analysis/produce_plots_and_stats.py
"""
Script to produce plots.
"""

import altair as alt
import os
import logging

from asf_welsh_energy_consultation import config_file
from asf_welsh_energy_consultation.config import translation_config
from asf_welsh_energy_consultation.getters.get_data import get_electric_tenure
from asf_welsh_energy_consultation.pipeline import process_data
from asf_welsh_energy_consultation.getters.get_data import load_wales_df, load_wales_hp
from asf_welsh_energy_consultation.pipeline.plotting import (
    proportions_bar_chart,
    age_prop_chart,
    time_series_comparison,
)

from nesta_ds_utils.viz.altair.formatting import setup_theme

logger = logging.getLogger(__name__)
alt.data_transformers.disable_max_rows()
# Enable Nesta theme for altair figures
setup_theme()

output_folder = "outputs/figures/"
time_series_min = config_file["plots"]["time_series_min_default"]

if not os.path.isdir(output_folder):
    os.makedirs(output_folder)


if __name__ == "__main__":
    # ======================================================
    # MCS installations, by off-gas status

    enhanced_combined = process_data.get_enhanced_combined()
    installations_by_gas_status = process_data.cumsums_by_variable(
        "off_gas", "Gas status", data=enhanced_combined
    )

    installations_by_gas_status_chart = time_series_comparison(
        data=installations_by_gas_status,
        title=[
            "Cumulative number of MCS certified heat pump installations in Welsh homes",
            "located in off- and on-gas postcodes",
        ],
        y_var="Number of heat pumps:Q",
        y_title="Number of heat pump installations",
        color_var="Gas status:N",
        filename="installations_by_gas_status",
        output_dir=output_folder,
    )

    # ======================================================
    # MCS installations, by rurality

    enhanced_combined = process_data.get_enhanced_combined()
    installations_by_rurality = process_data.cumsums_by_variable(
        "rurality_2_label", "Rurality", data=enhanced_combined
    )

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
        filename="installations_by_rurality",
        output_dir=output_folder,
    )

    # ======================================================
    # Proportions of new builds that have heat pumps

    new_build_hp_proportion = process_data.get_new_builds_hp_counts()
    max_date = new_build_hp_proportion["year"].max()

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
                scale=alt.Scale(domain=["2007-07-01", f"{max_date.year}-07-01"]),
            ),
            y=alt.Y("sum(value)", title="Number of EPCs"),
            # want heat pumps to be at the bottom of each bar - hacky but works
            color=alt.Color("Heating system"),
            order=alt.Order("Heating system"),
        )
        .properties(width=600, height=300)
    )

    new_build_hp_proportion_chart.save(output_folder + "new_build_hp_proportion.html")
    logger.info(f"Saved: {os.path.join(output_folder, 'new_build_hp_proportion.html')}")

    # ======================================================
    # Cumulative number of new builds with heat pumps

    new_build_hp_cumulative = process_data.get_new_builds_hp_cumsums()

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
    logger.info(f"Saved: {os.path.join(output_folder, 'new_build_hp_cumulative.html')}")

    # ======================================================
    # Cumulative MCS retrofits

    mcs_retrofits = process_data.get_mcs_retrofits()
    mcs_retrofit_cumsums = process_data.cumsums_by_variable(
        "country",
        "wales_col",
        data=mcs_retrofits,
        installation_date_col="commission_date",
    )
    # this function works without separating by category - 'wales_col' is a whole column of "Wales" (not used)

    cumulative_retrofits_chart = (
        alt.Chart(
            mcs_retrofit_cumsums,
            title="Cumulative number of MCS certified heat pump retrofits in Wales",
        )
        .mark_line()
        .encode(
            x=alt.X(
                "date",
                title="Date",
                scale=alt.Scale(
                    domain=[time_series_min, mcs_retrofit_cumsums.date.max()]
                ),
            ),
            y="Number of heat pumps",
        )
        .properties(width=600, height=300)
    )

    cumulative_retrofits_chart.save(output_folder + "cumulative_retrofits.html")
    logger.info(f"Saved: {os.path.join(output_folder, 'cumulative_retrofits.html')}")

    # ======================================================
    # Split of properties on electric heating by tenure

    electric_tenure = get_electric_tenure()
    N = electric_tenure["n"].sum()

    electric_tenure_chart = (
        alt.Chart(
            electric_tenure,
            title="Properties in Wales with only electric heating, split by tenure (N = "
            + "{:,}".format(N)
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
    logger.info(f"Saved: {os.path.join(output_folder, 'electric_tenure.html')}")

    # ======================================================
    # Original plots and stats

    wales_df = load_wales_df(from_csv=False)
    wales_hp = load_wales_hp(wales_df)

    # English plots

    # Key statistics
    intro = "Summary statistics for heat pumps in Wales\n\n"
    total_hp = f"Number of heat pumps: {len(wales_hp)}\n"
    total_epc = f"Number of properties in EPC: {len(wales_df)}\n"
    hp_perc = "Estimated percentage of properties with a heat pump: \
        {:.2%}\n\n".format(
        len(wales_hp) / len(wales_df)
    )

    tenure_value_counts = wales_hp.TENURE.value_counts(normalize=True).to_string()

    epc_c_or_above_and_good_walls = wales_df.loc[
        wales_df["CURRENT_ENERGY_RATING"].isin(["A", "B", "C"])
        & wales_df["WALLS_ENERGY_EFF"].isin(["Good", "Very Good"])
    ]

    epc_c_or_above_and_good_walls_and_roof = epc_c_or_above_and_good_walls.loc[
        epc_c_or_above_and_good_walls["ROOF_ENERGY_EFF"].isin(["Good", "Very Good"])
    ]

    epc_c_wall = f"\n\nNumber of EPC C+ properties with good or very good wall insulation: {len(epc_c_or_above_and_good_walls)}\n"

    epc_c_wall_proportion = f"As a proportion of properties in EPC: {len(epc_c_or_above_and_good_walls) / len(wales_df)}\n"

    epc_c_wall_roof = f"\n\nNumber of EPC C+ properties with good or very good wall and roof insulation: {len(epc_c_or_above_and_good_walls_and_roof)}\n"
    epc_c_wall_roof_proportion = f"As a proportion of properties in EPC: {len(epc_c_or_above_and_good_walls_and_roof) / len(wales_df)}"

    with open(os.path.join(output_folder, "stats.txt"), "w") as stats_txt:
        stats_txt.writelines(
            [
                intro,
                total_hp,
                total_epc,
                hp_perc,
                tenure_value_counts,
                epc_c_wall,
                epc_c_wall_proportion,
                epc_c_wall_roof,
                epc_c_wall_roof_proportion,
            ]
        )

    # Tenure of Welsh HPs
    proportions_bar_chart(
        wales_hp,
        "TENURE",
        "Tenure of Welsh properties with heat pumps",
        "Tenure",
        "Percentage of properties",
        filename="hp_tenure",
        x_type="tenure",
        expand_y=True,
    )

    # EPC, all
    unknown_vals = len(wales_df.loc[wales_df.CURRENT_ENERGY_RATING == "unknown"])
    if unknown_vals > 0:
        logger.warning(
            f"{unknown_vals} properties with unknown EPC ratings. These records will be removed from the count of EPC ratings for all Welsh properties."
        )
    proportions_bar_chart(
        wales_df.loc[wales_df.CURRENT_ENERGY_RATING != "unknown"],
        "CURRENT_ENERGY_RATING",
        "EPC ratings of all Welsh properties",
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
            "EPC ratings of owner-occupied and privately rented",
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
            "EPC ratings of owner-occupied and privately rented",
            "Welsh properties with heat pumps, built pre-2007",
        ],
        "Energy efficiency rating",
        "Percentage of properties",
        filename="epc_hp_private_retrofit",
        x_type="other",
    )

    age_data = process_data.generate_age_data(wales_df)
    age_prop_chart(
        age_data, "Construction age bands and energy efficiencies", "age_prop"
    )

    ## Welsh plots

    welsh_replacements = {
        "TENURE": dict(
            zip(
                translation_config.tenure_list["english"],
                translation_config.tenure_list["welsh"],
            )
        ),
        "CONSTRUCTION_AGE_BAND": translation_config.construction_age_band,
    }

    for df in [wales_df, wales_hp, age_data]:
        for col in ["TENURE", "CONSTRUCTION_AGE_BAND"]:
            if col in df.columns:
                df[col] = df[col].replace(welsh_replacements[col])

    # Tenure of Welsh HPs
    proportions_bar_chart(
        wales_hp,
        "TENURE",
        "Deiliadaeth eiddo â phympiau gwres yng Nghymru",
        "Deiliadaeth",
        "Canran yr eiddo",
        filename="hp_tenure_welsh",
        label_rotation=45,
        x_type="tenure",
        expand_y=True,
        language="welsh",
    )

    # EPC, all
    proportions_bar_chart(
        wales_df.loc[wales_df.CURRENT_ENERGY_RATING != "unknown"],
        "CURRENT_ENERGY_RATING",
        "Sgoriau EPC holl eiddo Cymru",
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
            "Sgoriau EPC eiddo perchen-feddiannaeth a",
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
            "Sgoriau EPC eiddo perchen-feddiannaeth a rhentu prifat",
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
        "Bandiau oedran adeiladu ac effeithlonrwydd ynni",
        "age_prop_welsh",
        language="welsh",
    )
