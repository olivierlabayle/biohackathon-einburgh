import plotly.express as px


def plot_growth_bar(growth_rate, theme="dark"):
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


def plot_sensitivity(df, nutrient_name, theme="dark"):
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
