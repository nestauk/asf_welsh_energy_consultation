# File: asf_welsh_energy_consultation/analysis/produce_plots.py
"""
Script to produce plots.
"""

import altair as alt

from asf_welsh_energy_consultation.getters.get_data import get_electric_tenure
from asf_welsh_energy_consultation.pipeline.process_data import *

from nesta_ds_utils.viz.altair.formatting import setup_theme

alt.data_transformers.disable_max_rows()
setup_theme()


output_folder = "outputs/figures/"

if not os.path.isdir(output_folder):
    os.makedirs(output_folder)


def time_series_comparison(
    data,
    title,
    y_var,
    y_title,
    color_var,
    x_var="date:T",
    x_title="Date",
    domain_min="2015-01-01",
    domain_max="2023-01-01",
    width=600,
    height=300,
):
    """Generic function for plotting a line chart by category (represented by color_var).

    Args:
        data (pd.DataFrame): Base data. Needs to be structured as a column of consecutive dates,
            a column indicating categories and a column with cumulative values.
        title (str/list): Chart title.
        y_var (str): y variable.
        y_title (str): y axis title.
        color_var (str): Variable to split by.
        x_var (str, optional): x variable. Defaults to "date:T".
        x_title (str, optional): x axis title. Defaults to "Date".
        domain_min (str, optional): x axis minimum. Defaults to "2015-01-01".
        domain_max (str, optional): x axis maximum. Defaults to "2023-01-01".
        width (int, optional): Chart width. Defaults to 600.
        height (int, optional): Chart height. Defaults to 300.

    Returns:
        alt.Chart: Base altair chart.
    """
    chart = (
        alt.Chart(
            data,
            title=title,
        )
        .mark_line()
        .encode(
            x=alt.X(
                x_var, title=x_title, scale=alt.Scale(domain=[domain_min, domain_max])
            ),
            y=alt.Y(y_var, title=y_title),
            color=color_var,
        )
        .properties(width=width, height=height)
    )

    return chart


if __name__ == "__main__":
    # ======================================================
    # MCS installations, by off-gas status

    installations_by_gas_status = cumsums_by_variable("off_gas", "Gas status")

    installations_by_gas_status_chart = time_series_comparison(
        data=installations_by_gas_status,
        title=[
            "Cumulative number of MCS certified heat pump installations in",
            "Welsh homes located in off- and on-gas postcodes",
        ],
        y_var="Number of heat pumps:Q",
        y_title="Number of heat pump installations",
        color_var="Gas status:N",
    )

    installations_by_gas_status_chart.save(
        output_folder + "installations_by_gas_status.png"
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
    )

    installations_by_rurality_chart.save(
        output_folder + "installations_by_rurality.png"
    )

    # ======================================================
    # Proportions of new builds that have heat pumps

    new_build_hp_proportion = new_hp_counts()

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
                scale=alt.Scale(domain=["2007-07-01", "2022-06-01"]),
            ),
            y=alt.Y("sum(value)", title="Number of EPCs"),
            # want heat pumps to be at the bottom of each bar - hacky but works
            color=alt.Color("Heating system"),
            order=alt.Order("Heating system"),
        )
        .properties(width=600, height=300)
    )

    new_build_hp_proportion_chart.save(output_folder + "new_build_hp_proportion.png")

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

    new_build_hp_cumulative_chart.save(output_folder + "new_build_hp_cumulative.png")

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
                scale=alt.Scale(domain=["2015-01-01", "2023-01-01"]),
            ),
            y="Number of heat pumps",
        )
        .properties(width=600, height=300)
    )

    cumulative_retrofits_chart.save(output_folder + "cumulative_retrofits.png")

    # ======================================================
    # Split of properties on electric heating by tenure

    electric_tenure = get_electric_tenure()

    electric_tenure_chart = (
        alt.Chart(
            electric_tenure,
            title="Properties in Wales with only electric heating, split by tenure",
        )
        .mark_bar()
        .encode(
            x=alt.X("tenure", title="Tenure", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("n", title="Number of properties"),
        )
        .configure(lineBreak="\n")
        .properties(width=600, height=300)
    )

    electric_tenure_chart.save(output_folder + "electric_tenure.png")
