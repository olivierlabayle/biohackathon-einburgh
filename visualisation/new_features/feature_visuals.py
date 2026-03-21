"""
feature_visuals.py
------------------
Theme-aware versions of plot_growth_bar() and plot_sensitivity().

These are drop-in replacements for the functions in code4.py (visuals.py).
The only difference is the added `theme` parameter ('dark' | 'light'),
which switches between plotly_dark / plotly_white templates and adjusts
font colours to match the GEMtimise colour scheme.

HOW TO INTEGRATE into code1.py (app):
  Option A — replace code4.py entirely:
    Rename this file to visuals.py (overwrite the original).
    No import changes needed in code1.py.

  Option B — keep code4.py unchanged, import from here instead:
    from feature_visuals import plot_growth_bar, plot_sensitivity
    Then pass theme=_ui_theme wherever the charts are rendered.

Colour palette:
    Orange accent : #f97316
    Dark bg       : #000000  |  Light bg: #ffffff
    Dark text     : #ffffff  |  Light text: #000000
"""

import plotly.express as px


def plot_growth_bar(growth_rate: float, theme: str = "dark"):
    """
    Bar chart of predicted biomass growth rate.

    Args:
        growth_rate: FBA objective value (h⁻¹).
        theme: 'dark' or 'light'. Defaults to 'dark'.

    Returns:
        plotly.graph_objects.Figure
    """
    template = "plotly_dark" if theme == "dark" else "plotly_white"
    font_color = "#ffffff" if theme == "dark" else "#000000"

    fig = px.bar(
        x=["Current Strategy"],
        y=[growth_rate],
        labels={"x": "", "y": "Growth Rate (h⁻¹)"},
        title="Predicted Biomass Yield",
        color_discrete_sequence=["#f97316"],
        template=template,
    )
    fig.update_layout(
        yaxis_range=[0, 1.5],
        font_color=font_color,
        title_font_color=font_color,
    )
    return fig


def plot_sensitivity(df, nutrient_name: str, theme: str = "dark"):
    """
    Line chart of growth rate vs. nutrient uptake flux.

    Args:
        df: DataFrame with columns 'Flux' and 'Growth Rate'.
        nutrient_name: Label used in the chart title.
        theme: 'dark' or 'light'. Defaults to 'dark'.

    Returns:
        plotly.graph_objects.Figure
    """
    template = "plotly_dark" if theme == "dark" else "plotly_white"
    font_color = "#ffffff" if theme == "dark" else "#000000"

    fig = px.line(
        df,
        x="Flux",
        y="Growth Rate",
        title=f"Sensitivity: {nutrient_name} vs Growth",
        template=template,
    )
    fig.update_traces(line_color="#f97316", line_width=3)
    fig.update_layout(font_color=font_color, title_font_color=font_color)
    return fig
