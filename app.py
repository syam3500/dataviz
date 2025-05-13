import dash
from dash import dcc, html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from prophet import Prophet
import pandas as pd
import matplotlib.pyplot as plt
import unicodedata

# Read and prepare the dataset

station_data = pd.read_csv("avg_data_day.csv")
station_data = station_data.dropna(subset=["lat", "lon"]).fillna(0)

# Merge stations into areas of madrid
metadata = pd.read_csv("informacion_estaciones_red_calidad_aire.csv", sep=";")


# Clean and normalize station names
def clean_text(s):
    if isinstance(s, str):
        s = s.strip().lower()
        s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("utf-8")
        return s
    return s


# Clean and merge station names
station_data["station_clean"] = station_data["name"].apply(clean_text)
metadata["station_clean"] = metadata["ESTACION"].apply(clean_text)
merged = station_data.merge(metadata, on="station_clean", how="left")

# Aggregate data by station and month
cig_aggregated_data = (
    station_data.groupby(["name", "month", "year"])
    .agg({"Cigarettes": "mean"})
    .reset_index()
)
cig_aggregated_data = cig_aggregated_data.dropna(subset=["Cigarettes"])
cig_aggregated_data = cig_aggregated_data[cig_aggregated_data["Cigarettes"] != 0]


# Calculate the global maximum for Cigarette Equivalents
global_max_value = cig_aggregated_data["Cigarettes"].max()

pollutants = ["BEN", "CO", "NO_2", "SO_2", "O_3", "PM25", "PM10"]

# Group by year and calculate the average for each pollutant
average_data_month = (
    station_data.groupby(["year", "month"])[pollutants].mean().reset_index()
)
average_data = station_data.groupby("year")[pollutants].mean().reset_index()
baseline_data = average_data[average_data["year"] == 2001]

# Calculate percentage values relative to the baseline year
for pollutant in pollutants:
    average_data[f"{pollutant}_percentage"] = (
        average_data[pollutant] / baseline_data[pollutant].values[0]
    ) * 100

# Reshape the data for Plotly
plot_data = average_data.melt(
    id_vars=["year"],
    value_vars=[f"{pollutant}_percentage" for pollutant in pollutants],
    var_name="Pollutant",
    value_name="Percentage",
)

# Thresholds for each pollutant
pollutant_thresholds = {
    "BEN": 5,
    "CO": 1,
    "NO_2": 20,
    "PM10": 20,
    "PM25": 10,
    "SO_2": 20,
    "O_3": 60,
}

# Find global min and max for Cigarettes
global_x_min = cig_aggregated_data["Cigarettes"].min()
global_x_max = cig_aggregated_data["Cigarettes"].max()

# Initialize a dictionary to store forecasts for each pollutant
forecasts = {}

# Generate forecasts for each pollutant using Prophet
for pollutant in pollutants:
    df = average_data_month[["year", "month", pollutant]].dropna()
    df["ds"] = pd.to_datetime(df[["year", "month"]].assign(day=1))
    df["y"] = df[pollutant]
    df = df[["ds", "y"]]

    from prophet import Prophet

    model = Prophet(interval_width=0.95)
    model.fit(df)
    future = model.make_future_dataframe(periods=12 * (2030 - 2018), freq="ME")
    forecast = model.predict(future)
    forecast["observed"] = df["y"].reset_index(drop=True)  # Observed values
    forecasts[pollutant] = forecast

# Create the Dash app
app = dash.Dash(__name__)
server = app.server  # for render

# App layout
app.layout = html.Div(
    [
        html.H1("Interactive Pollution Dashboard", style={"textAlign": "center"}),
        dcc.Tabs(
            [
                dcc.Tab(
                    label="Map of Madrid",
                    children=[
                        html.Div(
                            [
                                html.Label("Select Pollutant for Map:"),
                                dcc.Dropdown(
                                    id="map-dropdown",
                                    options=[
                                        {"label": pollutant, "value": pollutant}
                                        for pollutant in pollutants
                                    ],
                                    value="PM10",  # Default pollutant
                                ),
                                dcc.Graph(id="map-graph"),
                            ]
                        )
                    ],
                ),
                dcc.Tab(
                    label="Line Chart of Pollutants",
                    children=[
                        html.Div(
                            [
                                html.Label("Select Pollutant for Line Chart:"),
                                dcc.Dropdown(
                                    id="line-dropdown",
                                    options=[{"label": "All", "value": "All"}]
                                    + [
                                        {"label": pollutant, "value": pollutant}
                                        for pollutant in pollutants
                                    ],
                                    value="All",  # Default to "All"
                                ),
                                dcc.Dropdown(
                                    id="view-dropdown",
                                    options=[
                                        {
                                            "label": "Percentage Change (%)",
                                            "value": "Percentage",
                                        },
                                        {
                                            "label": "Concentration (µg/m³)",
                                            "value": "Concentration",
                                        },
                                    ],
                                    value="Percentage",  # Default: Percentage view
                                ),
                                dcc.Graph(id="line-graph"),
                            ]
                        )
                    ],
                ),
                dcc.Tab(
                    label="Seasonal Pollution Patterns",
                    children=[
                        html.Div(
                            [
                                html.Label("Select Pollutant for Seasonal Trend:"),
                                dcc.Dropdown(
                                    id="seasonal-dropdown",
                                    options=[
                                        {"label": pollutant, "value": pollutant}
                                        for pollutant in pollutants
                                    ],
                                    value="PM10",  # Default pollutant
                                ),
                                dcc.Graph(id="seasonal-graph"),
                            ]
                        )
                    ],
                ),
                dcc.Tab(
                    label="Forecast chart of Pollutants",
                    children=[
                        html.Div(
                            [
                                html.Label("Select Pollutant for Line Chart:"),
                                dcc.Dropdown(
                                    id="forecast-dropdown",
                                    options=[
                                        {"label": pollutant, "value": pollutant}
                                        for pollutant in pollutants
                                    ],
                                    value="PM10",  # Default to "All"
                                ),
                                dcc.Graph(id="forecast-graph"),
                            ]
                        )
                    ],
                ),
                dcc.Tab(
                    label="Cig chart of Pollutants",
                    children=[
                        html.Div(
                            [
                                dcc.Dropdown(
                                    id="month-dropdown",
                                    options=[{"label": "All Months", "value": "all"}]
                                    + [
                                        {"label": month_name, "value": i}
                                        for i, month_name in enumerate(
                                            [
                                                "January",
                                                "February",
                                                "March",
                                                "April",
                                                "May",
                                                "June",
                                                "July",
                                                "August",
                                                "September",
                                                "October",
                                                "November",
                                                "December",
                                            ],
                                            start=1,
                                        )
                                    ],
                                    value="all",  # Default: "All Months"
                                ),
                                html.Label("Select Year:"),
                                dcc.Dropdown(
                                    id="year-dropdown",
                                    options=[
                                        {"label": str(year), "value": year}
                                        for year in cig_aggregated_data["year"].unique()
                                    ],
                                    value=cig_aggregated_data["year"].unique()[
                                        0
                                    ],  # Default: First available year
                                ),
                                dcc.Graph(id="cigarette-graph"),
                            ]
                        )
                    ],
                ),
                dcc.Tab(
                    label="Pollutants in Area's of Madrid",
                    children=[
                        html.Div(
                            [
                                html.Label("Select Pollutant:"),
                                dcc.Dropdown(
                                    id="station-type-pollutant-dropdown",
                                    options=[
                                        {"label": pollutant, "value": pollutant}
                                        for pollutant in pollutants
                                        if pollutant
                                        not in [
                                            "CO",
                                            "PM10",
                                        ]  # Exclude CO and PM10 bcs it was giving errors.
                                    ],
                                    value="PM25",
                                ),
                                dcc.Graph(id="station-type-bar-graph"),
                            ]
                        )
                    ],
                ),
            ]
        ),
    ]
)


# Callback to update the map based on dropdown selection
@app.callback(
    dash.dependencies.Output("map-graph", "figure"),
    [dash.dependencies.Input("map-dropdown", "value")],
)
def update_map(selected_pollutant):
    aggregated_data = (
        station_data.groupby(["name", "lat", "lon", "year"])
        .agg({selected_pollutant: "mean"})
        .reset_index()
    )

    min_val = aggregated_data[selected_pollutant].min()
    max_val = aggregated_data[selected_pollutant].max()

    fig = px.scatter_map(
        aggregated_data,
        lat="lat",
        lon="lon",
        color=selected_pollutant,
        size=selected_pollutant,
        hover_name="name",
        animation_frame="year",
        title=f"Pollution Levels by Station ({selected_pollutant})",
        color_continuous_scale=[
            (0.0, "#3B4CC0"),  # Low values are dark blue
            (0.5, "#F4A259"),  # Medium values are orange
            (1.0, "#D7263D"),  # High values are dark red
        ],
        range_color=(min_val, max_val),  # Adjust range to fit pollutant levels
    )
    fig.update_layout(height=900)
    return fig


# Callback to update the line chart based on dropdown selection
@app.callback(
    dash.dependencies.Output("line-graph", "figure"),
    [
        dash.dependencies.Input("line-dropdown", "value"),
        dash.dependencies.Input("view-dropdown", "value"),
    ],
)
def update_line_chart(selected_pollutant, selected_view):
    if selected_view == "Percentage":
        if selected_pollutant == "All":
            # Show all pollutants in the same chart (percentage view)
            fig = px.line(
                plot_data,
                x="year",
                y="Percentage",
                color="Pollutant",
                color_discrete_sequence=px.colors.qualitative.Safe,
                title="Yearly Change in Pollutant Levels (Baseline = 100%)",
                labels={
                    "year": "Year",
                    "Percentage": f"% of Baseline (100%)",
                },
            )
        else:
            # Show selected pollutant as percentage
            fig = px.line(
                average_data,
                x="year",
                y=f"{selected_pollutant}_percentage",
                title=f"Yearly Change in {selected_pollutant} Levels (Baseline = 100%)",
                labels={
                    "year": "Year",
                    f"{selected_pollutant}_percentage": f"% of Baseline (100%)",
                },
            )
            fig.update_traces(line_color="rgb(136, 204, 238)")
    else:  # If "Concentration" is selected
        if selected_pollutant == "All":
            # Show all pollutants in their raw concentration levels
            fig = px.line(
                average_data.melt(
                    id_vars=["year"],
                    value_vars=pollutants,
                    var_name="Pollutant",
                    value_name="Concentration",
                ),
                x="year",
                y="Concentration",
                color="Pollutant",
                color_discrete_sequence=px.colors.qualitative.Safe,
                title="Yearly Change in Pollutant Concentrations",
                labels={
                    "year": "Year",
                    "Concentration": "Pollutant Concentration (µg/m³)",
                },
            )
        else:
            # Show selected pollutant in concentration format
            fig = px.line(
                average_data,
                x="year",
                y=selected_pollutant,
                title=f"Yearly Change in {selected_pollutant} Levels (Concentration)",
                labels={
                    "year": "Year",
                    selected_pollutant: f"{selected_pollutant} Concentration (µg/m³)",
                },
            )
            fig.update_traces(line_color="rgb(136, 204, 238)")

    fig.update_layout(transition_duration=500)
    fig.update_layout(showlegend=False)
    fig.update_layout(
        height=600,
        xaxis=dict(
            showgrid=False,
        ),
        yaxis=dict(
            showgrid=False,
        ),
        plot_bgcolor="white",
    )

    return fig


@app.callback(
    dash.dependencies.Output("forecast-graph", "figure"),
    [dash.dependencies.Input("forecast-dropdown", "value")],
)
def update_forecast(selected_pollutant):
    forecast = forecasts[selected_pollutant]

    # Get the year when the observed data ends (e.g., 2018)
    cutoff_year = 2018
    cutoff_date = pd.Timestamp(f"{cutoff_year}-12-31")  # Set to the end of 2018

    fig = go.Figure()

    # Add the forecast lines (without observed data)
    fig.add_trace(
        go.Scatter(
            x=forecast["ds"],
            y=forecast["yhat"],
            mode="lines",
            name="Expected Case (Forecast)",
            line=dict(
                color="rgb(136, 204, 238)", width=3
            ),  # Make forecast line thicker
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast["ds"],
            y=forecast["yhat_lower"],
            mode="lines",
            name="Lower Bound",
            line=dict(dash="dot", color="gray"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast["ds"],
            y=forecast["yhat_upper"],
            mode="lines",
            name="Upper Bound",
            line=dict(dash="dot", color="gray"),
        )
    )

    # Highlight the transition from observed to forecasted data with a vertical dashed line
    fig.add_shape(
        type="line",
        x0=cutoff_date,
        x1=cutoff_date,
        y0=forecast["yhat"].min(),
        y1=forecast["yhat"].max(),
        line=dict(color="blue", dash="dash", width=2),
        name="Forecast Start",
    )

    # Add a horizontal line for the pollutant threshold
    threshold = pollutant_thresholds[selected_pollutant]
    fig.add_shape(
        type="line",
        x0=forecast["ds"].min(),
        x1=forecast["ds"].max(),
        y0=threshold,
        y1=threshold,
        line=dict(color="red", dash="dash", width=2),
        name=f"Pollution Reference Line ({selected_pollutant})",
    )

    # Add an annotation to indicate that data after 2018 is a forecast
    fig.add_annotation(
        x=cutoff_date,
        y=forecast["yhat"].max(),
        text="Start of Forecast",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        ax=20,
        ay=-30,
        font=dict(size=12, color="blue"),
        align="left",
    )

    # Update layout for better accessibility and aesthetics
    fig.update_layout(
        title=f"Forecast of {selected_pollutant} Levels with 95% Confidence Intervals",
        xaxis_title="Date",
        yaxis_title="Pollutant Levels",
        transition_duration=500,
        height=600,
        plot_bgcolor="white",  # Set background color to white
        xaxis=dict(
            title="Date",
            showgrid=False,
            gridwidth=1,
            gridcolor="lightgray",
            tickangle=45,  # Rotate date labels for readability
        ),
        yaxis=dict(
            title="Pollutant Concentration",
            showgrid=False,
            gridwidth=1,
            gridcolor="lightgray",
        ),
        hovermode="closest",  # Make hover more interactive
        margin=dict(t=50, b=50, l=50, r=50),  # Add margin for better aesthetics
    )

    return fig


@app.callback(
    dash.dependencies.Output("cigarette-graph", "figure"),
    [
        dash.dependencies.Input("month-dropdown", "value"),
        dash.dependencies.Input("year-dropdown", "value"),
    ],
)
def update_graph(selected_month, selected_year):
    # Filter data based on selected year and month
    if selected_month == "all":  # If "All Months" is selected
        filtered_data = cig_aggregated_data[
            cig_aggregated_data["year"] == selected_year
        ]
    else:  # If a specific month is selected
        filtered_data = cig_aggregated_data[
            (cig_aggregated_data["month"] == selected_month)
            & (cig_aggregated_data["year"] == selected_year)
        ]

    x_coords = filtered_data["month"]  # Months for x-axis
    y_coords = filtered_data["name"]  # Station names for y-axis
    values = filtered_data["Cigarettes"]  # Cigarette equivalents for hover and text

    # Create a figure
    fig = go.Figure()

    # Add text annotations for rounded values
    fig.add_trace(
        go.Scatter(
            x=x_coords,
            y=y_coords,
            mode="text",  # Display text annotations
            text=values.map(lambda x: f"{x:.2f}"),  # Round values and convert to string
            textfont=dict(size=12, color="black"),
            name=f"{'All Months' if selected_month == 'all' else f'Month {selected_month}'}, Year {selected_year}",
            textposition="bottom center",
            hovertemplate=(
                "Station: %{y}<br>"
                "Month: %{x}<br>"
                "Average Daily Cigarette Equivalent : %{text}<extra></extra>"
            ),
        )
    )

    # Add images scaled to the global max value
    image_url = "https://pngimg.com/d/cigarette_PNG4761.png"
    for i, value in enumerate(values):
        fig.add_layout_image(
            dict(
                source=image_url,
                x=x_coords.iloc[i],  # Month as X-coordinate
                y=y_coords.iloc[i],  # Station name as Y-coordinate
                xref="x",
                yref="y",
                sizex=value / global_max_value * 2,  # Use global max for uniform sizing
                sizey=1,
                xanchor="center",
                yanchor="bottom",
                opacity=0.8,
            )
        )

    # Update layout
    fig.update_layout(
        title=f"Cigarette Comparison for {'All Months' if selected_month == 'all' else f'Month {selected_month}'}, Year {selected_year}",
        xaxis=dict(
            title="Month",
            tickvals=list(range(1, 13)),
            ticktext=[
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ],
        ),  # Month names as x-axis labels
        yaxis=dict(title="Station Name"),
        height=900,
        showlegend=False,
    )

    return fig


@app.callback(
    dash.dependencies.Output("seasonal-graph", "figure"),
    [dash.dependencies.Input("seasonal-dropdown", "value")],
)
def update_seasonal_chart(selected_pollutant):
    # Group data by year and month, then compute the monthly average
    seasonal_data = (
        station_data.groupby(["year", "month"])[selected_pollutant].mean().reset_index()
    )

    min_val = seasonal_data[selected_pollutant].min()
    max_val = seasonal_data[selected_pollutant].max()

    fig = px.line(
        seasonal_data,
        x="month",
        y=selected_pollutant,
        animation_frame="year",
        markers=True,  # Makes points visible
        title=f"Seasonal Pattern of {selected_pollutant} Concentration Over the Years",
        labels={
            "month": "Month",
            selected_pollutant: f"{selected_pollutant} Concentration (µg/m³)",
            "year": "Year",
        },
    )
    fig.update_traces(line_color="rgb(136, 204, 238)")

    fig.update_layout(
        yaxis=dict(
            range=[min_val * 0.9, max_val * 1.1],
        ),  # Adding buffer to avoid tight limits
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(1, 13)),
            ticktext=[
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ],
            showgrid=False,
        ),
        height=600,
        showlegend=False,
        plot_bgcolor="white",  # Set background color to white
    )

    return fig


@app.callback(
    dash.dependencies.Output("station-type-bar-graph", "figure"),
    [dash.dependencies.Input("station-type-pollutant-dropdown", "value")],
)
def update_station_type_bar_chart(selected_pollutant):
    merged[selected_pollutant] = pd.to_numeric(
        merged[selected_pollutant], errors="coerce"
    )
    grouped = merged.groupby("NOM_TIPO")[selected_pollutant].mean().reset_index()

    fig = px.bar(
        grouped,
        x="NOM_TIPO",
        y=selected_pollutant,
        title=f"Average {selected_pollutant} Concentration in Madrid (2001-2018)",
        labels={
            "NOM_TIPO": "Station Type",
            selected_pollutant: f"Average {selected_pollutant} (µg/m³)",
        },
        color="NOM_TIPO",
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig.update_layout(height=800, plot_bgcolor="white")
    return fig


# Run the app
if __name__ == "__main__":
    app.run(debug=False)
