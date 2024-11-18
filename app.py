from faicons import icon_svg
import faicons as fa
import plotly.express as px
from shinywidgets import render_plotly, render_widget, output_widget
import random
from shiny import reactive, render
from datetime import datetime
import pandas as pd
from shiny import reactive, render, req
from shiny.express import input, ui, render
from collections import deque
from scipy import stats
from statsmodels.api import OLS, add_constant


UPDATE_INTERVAL_SECS: int = 10
DEQUE_SIZE: int = 10
reactive_value_wrapper = reactive.value(deque(maxlen=DEQUE_SIZE))

# Import icons from faicons ----------------------------------------------------------------------
ICONS = {
    "mars": fa.icon_svg("mars"),
    "venus": fa.icon_svg("venus"),
    "currency-dollar": fa.icon_svg("dollar-sign"),
    "gear": fa.icon_svg("gear")
}

tips = px.data.tips()  # Load tipping dataset

# Page title -------------------------------------------------------------------------------------
ui.page_opts(title="Tipping Analysis Dashboard", fillable=True)

# Sidebar with Inputs ----------------------------------------------------------------------------
with ui.sidebar(open="open"):
    ui.h5("Filters and Options")

    # Filter for dining time
    ui.input_radio_buttons(
        "selected_time",
        "Select Dining Time",
        choices=["Dinner", "Lunch"],
        selected="Dinner",
        inline=True
    )

    # Filter for gender
    ui.input_checkbox_group(
        "selected_gender",
        "Select Gender",
        ["Male", "Female"],
        selected=["Male", "Female"],
        inline=True
    )

    # Filter for smoker status
    ui.input_checkbox_group(
        "selected_smoker",
        "Smoker?",
        ["Yes", "No"],
        selected=["Yes", "No"],
        inline=True
    )

    # Range slider for total bill
    ui.input_slider("total_bill_range", "Total Bill Range ($)", 0, 50, (10, 30))

    # Range slider for group size
    ui.input_slider("size_range", "Group Size", 1, 6, (2, 4))

# Metrics Section --------------------------------------------------------------------------------
with ui.layout_columns(fill=False):
    # Total tips for girls
    with ui.value_box(
        showcase=ICONS["venus"],
        theme="bg-gradient-pink-purple", height=200
    ):
        "Girls' Total Tips"
        @render.text
        def display_gtip():
            _, df, _ = reactive_tips_combined()
            return f"${df['girlamnt'].sum():.2f}"

    # Total tips for boys
    with ui.value_box(
        showcase=ICONS["mars"],
        theme="bg-gradient-blue-green", height=200
    ):
        "Boys' Total Tips"
        @render.text
        def display_btip():
            _, df, _ = reactive_tips_combined()
            return f"${df['boyamnt'].sum():.2f}"

# Data Table and Visualizations ------------------------------------------------------------------
with ui.layout_columns(fill=False):
    # Data Table
    with ui.card():
        "Filtered Tipping Data"
        @render.data_frame
        def tipping_df():
            return render.DataTable(filtered_data(), selection_mode='row')

    # Scatterplot with regression line
    with ui.card(full_screen=True):
        ui.card_header("Scatterplot: Total Bill vs Tip")
        @render_plotly
        def scatterplot_with_regression():
            filtered = filtered_data()
            fig = px.scatter(
                filtered,
                x="total_bill",
                y="tip",
                color="sex",
                trendline="ols",
                labels={"total_bill": "Total Bill ($)", "tip": "Tip ($)"},
                title="Scatterplot: Total Bill vs Tip with Regression"
            )
            return fig

    # Heatmap for size vs tip
    with ui.card(full_screen=True):
        ui.card_header("Heatmap: Group Size vs Tip")
        @render_plotly
        def heatmap_size_vs_tip():
            filtered = filtered_data()
            fig = px.density_heatmap(
                filtered,
                x="size",
                y="tip",
                color_continuous_scale="Viridis",
                labels={"size": "Group Size", "tip": "Tip ($)"},
                title="Heatmap: Group Size vs Tip"
            )
            return fig

# Tabbed Trend Charts ---------------------------------------------------------------------------
with ui.navset_pill(id="tabbed_graphs"):
    # Girls' Tips Trend Chart
    with ui.nav_panel("Girls Trend"):
        @render_plotly
        def girls_trend_chart():
            _, df, _ = reactive_tips_combined()
            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                return px.line(
                    df,
                    x="timestamp",
                    y="girlamnt",
                    line_shape="spline",
                    title="Girls' Tips Over Time",
                    labels={"timestamp": "Time", "girlamnt": "Tips ($)"},
                    color_discrete_sequence=["pink"]
                )

    # Boys' Tips Trend Chart
    with ui.nav_panel("Boys Trend"):
        @render_plotly
        def boys_trend_chart():
            _, df, _ = reactive_tips_combined()
            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                return px.line(
                    df,
                    x="timestamp",
                    y="boyamnt",
                    line_shape="spline",
                    title="Boys' Tips Over Time",
                    labels={"timestamp": "Time", "boyamnt": "Tips ($)"},
                    color_discrete_sequence=["blue"]
                )

# Reactive Functions -----------------------------------------------------------------------------
@reactive.calc
def filtered_data():
    req(input.selected_time(), input.selected_gender(), input.selected_smoker())
    filtered_tips = tips[
        (tips["time"] == input.selected_time()) &
        (tips["sex"].isin(input.selected_gender())) &
        (tips["smoker"].isin(input.selected_smoker())) &
        (tips["total_bill"].between(*input.total_bill_range())) &
        (tips["size"].between(*input.size_range()))
    ]
    return filtered_tips

def reactive_tips_combined():
    reactive.invalidate_later(UPDATE_INTERVAL_SECS)
    tip_value_girls = round(random.uniform(1, 50), 1)
    tip_value_boys = round(random.uniform(1, 50), 1)
    timestamp_value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = {"girlamnt": tip_value_girls, "boyamnt": tip_value_boys, "timestamp": timestamp_value}
    reactive_value_wrapper.get().append(new_entry)
    deque_snapshot = reactive_value_wrapper.get()
    df = pd.DataFrame(deque_snapshot)
    return deque_snapshot, df, new_entry
