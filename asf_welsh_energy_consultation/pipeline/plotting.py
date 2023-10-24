# File: asf_welsh_energy_consultation/pipeline/plotting.py
"""
Defines plotting functions.
"""

import pandas as pd
import altair as alt
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import os
import logging

from asf_welsh_energy_consultation.config import translation_config
from asf_welsh_energy_consultation import config_file
from nesta_ds_utils.viz.altair.formatting import setup_theme

logger = logging.getLogger(__name__)

fig_output_path = {
    "english": "outputs/figures/english/",
    "welsh": "outputs/figures/welsh/",
}

for file_path in fig_output_path.values():
    if not os.path.isdir(file_path):
        os.makedirs(file_path)

# Enable Nesta theme for altair figures
setup_theme()


def time_series_comparison(
    data,
    title,
    y_var,
    y_title,
    color_var,
    filename,
    output_dir,
    x_var="date:T",
    x_title="Date",
    domain_min=None,
    domain_max=None,
    width=600,
    height=300,
):
    """Generic function for plotting a line chart by category (represented by color_var).

    Args:
        data (pd.DataFrame): Base data. Needs to be structured as a column of consecutive dates,
            a column indicating categories and a column with cumulative values.
        title (str/list): Chart title.
        y_var (str): y variable.
        y_title (str): y-axis title.
        color_var (str): Variable to split by.
        filename (str): Filename for saving chart.
        output_dir (str): Directory to save chart to.
        x_var (str, optional): x variable. Defaults to "date:T".
        x_title (str, optional): x-axis title. Defaults to "Date".
        domain_min (str, optional): x-axis minimum. Defaults to "2015-01-01".
        domain_max (str, optional): x-axis maximum. Defaults to max date of series.
        width (int, optional): Chart width. Defaults to 600.
        height (int, optional): Chart height. Defaults to 300.

    Returns:
        alt.Chart: Saves generated altair chart.
    """
    if domain_min is None:
        domain_min = config_file["plots"]["time_series_min_default"]
        logger.info(f"Time series comparison using {domain_min} as min date")
    if domain_max is None:
        domain_max = data.date.max()
        logger.info(f"Time series comparison using {domain_max} as max date")
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

    chart = chart.configure_title(fontSize=20)
    chart.save(os.path.join(output_dir, f"{filename}.html"))
    logger.info(f"Saved: {os.path.join(output_dir, filename)}.html")


def proportions_bar_chart(
    base_data,
    field,
    title,
    x_label,
    y_label,
    filename,
    expand_y=False,
    x_type="good",
    language="english",
):
    """Create a generic bar chart of proportions of properties in a given category.

    Args:
        base_data (pd.DataFrame): EPC data.
        field (str): Feature name.
        title (str): Chart title.
        x_label (str): x axis label.
        y_label (str): y axis label.
        filename (str): Filename.
        expand_y (bool, optional): Whether to extend the y axis beyond altair's default. Defaults to False.
        x_type (str, optional): Type of x variable (to control formatting).
            Can be "good" (insulation quality), "tenure", or otherwise assumed to be A-G energy efficiencies.
            Defaults to "good".
        language (str, optional): Language of chart text. Defaults to "english".
    """
    source = pd.DataFrame({"count": base_data[field].value_counts()}).reset_index()

    if x_type == "good":
        order = translation_config.quality_list[language]
    elif x_type == "tenure":
        order = translation_config.tenure_list[language]
    else:
        order = ["A", "B", "C", "D", "E", "F", "G"]

    N_count = "{:,}".format(len(base_data))

    chart = (
        alt.Chart(source)
        .transform_joinaggregate(
            Total="sum(count)",
        )
        .transform_calculate(PercentOfTotal="datum.count / datum.Total")
        .mark_bar()
        .encode(
            x=alt.X("index", sort=order, title=x_label, axis=alt.Axis(labelAngle=0)),
            y=alt.Y(
                shorthand="PercentOfTotal:Q",
                axis=alt.Axis(format=".0%"),
                title=y_label,
                scale=alt.Scale(domain=[0, 0.5]) if expand_y is True else alt.Scale(),
            ),
        )
        .configure_bar(
            color="#0000ff",
        )
        .properties(
            width=500,
            height=300,
            # add N to title (just append to end if string, otherwise append to last in list of strings)
            title=title + " (N = " + N_count + ")"
            if type(title) == str
            else title[:-1] + [title[-1] + " (N = " + N_count + ")"],
        )
    ).configure_title(fontSize=20)

    chart.save(fig_output_path[language] + filename + ".html")

    logger.info(f"Saved: {os.path.join(fig_output_path[language], filename)}.html")


# matplotlib only cycles through 10 colours, so manually defining 11 here to cover all age categories
colors = [
    "#000000",
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
]


def age_prop_chart(base_data, title, filename, language="english"):
    """Create single-column bar chart with property ages, proportions and average energy efficiencies.

    Args:
        base_data (pd.DataFrame): EPC data.
        title (str): Chart title.
        filename (str): Filename.
        language (str, optional): Language of chart text. Defaults to "english".
    """

    text_labels = [
        translation_config.energy_efficiency_text[language] + str(val)
        for val in base_data["CURRENT_ENERGY_EFFICIENCY"]
    ]
    prop_labels = [str(round(val, 1)) + "%" for val in base_data["percentage"]]
    width = 1

    fig, ax = plt.subplots()
    fig.set_figheight(10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

    # create initial bar
    ax.bar(
        x=" ",
        height=base_data.loc[0, "percentage"],
        width=width,
        label=base_data.loc[0, "CONSTRUCTION_AGE_BAND"],
        color=colors[0],
    )

    # plot remaining bars on top
    for i in range(1, len(colors)):
        ax.bar(
            x=" ",
            height=base_data.loc[i, "percentage"],
            width=width,
            bottom=base_data.loc[i - 1, "cumul_prop"],
            label=base_data.loc[i, "CONSTRUCTION_AGE_BAND"],
            color=colors[i],
        )

    # format y axis
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(100))
    ax.set_ylabel(
        translation_config.housing_stock_text[language], fontweight="bold", fontsize=12
    )
    ax.set_title(title, fontweight="bold", fontsize=14, pad=20)

    # put legend in top right
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        reversed(handles),
        reversed(labels),
        loc="upper right",
        bbox_to_anchor=(1.6, 1),
        fontsize=10,
        title=translation_config.age_band_text[language],
        title_fontproperties={"weight": "bold"},
    )

    # put text in centres of bars
    rects = ax.patches

    for rect, label in zip(rects, text_labels):
        height = rect.get_height()
        ax.text(
            rect.get_x() + rect.get_width() / 2,
            rect.get_y() + height / 2,
            label,
            ha="center",
            va="center",
            color="white",
            fontsize=12,
        )

    for rect, label in zip(rects, prop_labels):
        height = rect.get_height()
        ax.text(
            rect.get_x() + rect.get_width() + 0.01,
            rect.get_y() + height / 2,
            label,
            ha="left",
            va="center",
            fontsize=12,
        )

    # format axes
    plt.tick_params(
        axis="x",  # changes apply to the x-axis
        which="both",  # both major and minor ticks are affected
        bottom=False,  # ticks along the bottom edge are off
        top=False,  # ticks along the top edge are off
        labelbottom=False,
    )  # labels along the bottom edge are off

    plt.tight_layout()

    plt.savefig(fig_output_path[language] + filename + ".png", bbox_inches="tight")

    logger.info(f"Saved: {os.path.join(fig_output_path[language], filename)}.png")
