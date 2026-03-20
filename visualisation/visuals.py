import plotly.express as px
import plotly.graph_objects as ob

def plot_growth_bar(growth_rate):
    fig = px.bar(
        x=["Current Strategy"],
        y=[growth_rate],
        labels={'x': '', 'y': 'Growth Rate (h⁻¹)'},
        title="Predicted Biomass Yield",
        color_discrete_sequence=['#2e7b5b']
    )
    fig.update_layout(yaxis_range=[0, 1.5])
    return fig

def plot_sensitivity(df, nutrient_name):
    fig = px.line(
        df, x="Flux", y="Growth Rate",
        title=f"Sensitivity: {nutrient_name} vs Growth",
        template="plotly_white"
    )
    fig.update_traces(line_color='#007bff', line_width=3)
    return fig