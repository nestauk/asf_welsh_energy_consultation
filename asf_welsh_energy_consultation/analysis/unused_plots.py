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
