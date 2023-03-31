import altair as alt

from asf_welsh_energy_consultation.pipeline.process_data import (
    cumsums_by_variable,
    get_average_capacity,
    new_hp_counts,
    get_new_hp_cumsums,
    capacities_by_built_form,
)

from nesta_ds_utils.viz.altair.formatting import setup_theme

alt.data_transformers.disable_max_rows()
setup_theme()


output_folder = "outputs/figures/"


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


# cumulative numbers of hps
installations_by_gas_status = cumsums_by_variable("off_gas", "Gas status")

installations_by_gas_status_chart = time_series_comparison(
    data=installations_by_gas_status,
    title=[
        "Cumulative numbers of MCS certified heat pump installations in",
        "Welsh homes located in off- and on-gas postcodes",
    ],
    y_var="Number of heat pumps:Q",
    y_title="Number of heat pumps",
    color_var="Gas status:N",
)

installations_by_gas_status_chart.save(
    output_folder + "installations_by_gas_status.png"
)


# cumulative total capacity
total_capacity_by_gas_status = cumsums_by_variable(
    "off_gas", "Gas status", capacity="capacity_mw"
)

total_capacity_by_gas_status_chart = time_series_comparison(
    data=total_capacity_by_gas_status,
    title=[
        "Cumulative total capacity of MCS certified heat pump installations",
        "in Welsh homes located in off- and on-gas postcodes",
    ],
    y_var="Total capacity:Q",
    y_title="Total installed capacity (MW)",
    color_var="Gas status:N",
)

total_capacity_by_gas_status_chart.save(
    output_folder + "total_capacity_by_gas_status.png"
)


# average capacity
# ...

# rurality counts
installations_by_rurality = cumsums_by_variable("rurality_2_label", "Rurality")

installations_by_rurality_chart = time_series_comparison(
    data=installations_by_rurality,
    title=[
        "Cumulative numbers of MCS certified heat pump installations",
        "in Welsh homes located in rural vs urban postcodes",
    ],
    y_var="Number of heat pumps:Q",
    y_title="Number of heat pumps",
    color_var="Rurality:N",
)

installations_by_rurality_chart.save(output_folder + "installations_by_rurality.png")


# installations_by_precise_rurality = cumsums_by_variable("rurality_7", "Rurality")

# installations_by_precise_rurality_chart = time_series_comparison(
#     data=installations_by_precise_rurality,
#     title=["Cumulative numbers of MCS certified heat pump installations", "in Welsh homes by rurality of postcode"],
#     y_var="Number of heat pumps:Q",
#     y_title="Number of heat pumps",
#     color_var="Rurality:N"
# )

# installations_by_precise_rurality_chart.save(output_folder + "installations_by_precise_rurality.png")

# check! any reasons why this wouldn't be accurate? e.g. postcodes ceasing to exist or not existing yet


new_build_hp_proportion = new_hp_counts()

new_build_hp_proportion_chart = (
    alt.Chart(
        new_build_hp_proportion,
        title="New-build EPCs registed for Welsh properties, split by heating system",
    )
    .mark_bar(size=20)
    .encode(
        x=alt.X(
            "year", title="Year", scale=alt.Scale(domain=["2007-07-01", "2022-06-01"])
        ),
        y=alt.Y("sum(value)", title="Number of EPCs"),
        color=alt.Color("Heating system"),
        order=alt.Order("Heating system"),
    )
    .properties(width=600, height=300)
)

new_build_hp_proportion_chart.save(output_folder + "new_build_hp_proportion.png")


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


# difference in average capacity for new builds vs retrofits
# ...


# difference in average capacity by built form

built_form_capacities = capacities_by_built_form().reset_index()

built_form_capacities["label"] = "n=" + built_form_capacities["count"].astype(str)

bars = (
    alt.Chart(
        built_form_capacities,
        title=[
            "Mean capacity of MCS-certified heat pumps in Wales",
            "by property type (houses and bungalows only)",
        ],
    )
    .mark_bar()
    .encode(
        x=alt.X(
            "BUILT_FORM:N",
            title="Property type",
            axis=alt.Axis(labelAngle=0),
            sort="-y",
        ),
        y=alt.Y("mean:Q", title="Mean capacity (kW)", scale=alt.Scale(domain=[0, 14])),
    )
)

text = bars.mark_text(dy=-10).encode(text="label")

built_form_capacities_chart = (bars + text).properties(width=600, height=300)

built_form_capacities_chart.save(output_folder + "built_form_capacities.png")
