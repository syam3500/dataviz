import dash
from dash import dcc, html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from prophet import Prophet
import pandas as pd
import matplotlib.pyplot as plt

# Read and prepare the dataset

station_data = pd.read_csv("avg_data_day.csv")
station_data = station_data.dropna(subset=['lat', 'lon']).fillna(0)

# Aggregate data by station and month
cig_aggregated_data = station_data.groupby(['name', 'month', 'year']).agg({'Cigarettes': 'mean'}).reset_index()
cig_aggregated_data = cig_aggregated_data.dropna(subset=['Cigarettes'])
cig_aggregated_data = cig_aggregated_data[cig_aggregated_data['Cigarettes'] != 0]


# Calculate the global maximum for Cigarette Equivalents
global_max_value = cig_aggregated_data['Cigarettes'].max()

pollutants = ["BEN", "CO", "NO_2", "SO_2", "O_3", "PM25", "PM10"]

# Group by year and calculate the average for each pollutant
average_data_month = station_data.groupby(['year', 'month'])[pollutants].mean().reset_index()
average_data = station_data.groupby('year')[pollutants].mean().reset_index()
baseline_data = average_data[average_data['year'] == 2001]

# Calculate percentage values relative to the baseline year
for pollutant in pollutants:
    average_data[f'{pollutant}_percentage'] = (
        average_data[pollutant] / baseline_data[pollutant].values[0]
    ) * 100

# Reshape the data for Plotly
plot_data = average_data.melt(
    id_vars=['year'],
    value_vars=[f'{pollutant}_percentage' for pollutant in pollutants],
    var_name='Pollutant',
    value_name='Percentage'
)

# Thresholds for each pollutant
pollutant_thresholds = {
    "BEN": 5,
    "CO": 1,
    "NO_2": 20,
    "PM10": 20,
    "PM25": 10,
    "SO_2": 20,
    "O_3": 60
}

# Find global min and max for Cigarettes
global_x_min = cig_aggregated_data['Cigarettes'].min()
global_x_max = cig_aggregated_data['Cigarettes'].max()

# Initialize a dictionary to store forecasts for each pollutant
forecasts = {}

# Generate forecasts for each pollutant using Prophet
for pollutant in pollutants:
    df = average_data_month[['year', 'month', pollutant]].dropna()
    df['ds'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
    df['y'] = df[pollutant]
    df = df[['ds', 'y']]
    
    from prophet import Prophet
    model = Prophet(interval_width=0.95)
    model.fit(df)
    future = model.make_future_dataframe(periods=12 * (2030 - 2018), freq='ME')
    forecast = model.predict(future)
    forecast['observed'] = df['y'].reset_index(drop=True)  # Observed values
    forecasts[pollutant] = forecast

# Create the Dash app
app = dash.Dash(__name__)
server = app.server # for render

# App layout
app.layout = html.Div([
    html.H1("Interactive Pollution Dashboard", style={'textAlign': 'center'}),
    
    dcc.Tabs([
        dcc.Tab(label='Map of Madrid', children=[
            html.Div([
                html.Label("Select Pollutant for Map:"),
                dcc.Dropdown(
                    id='map-dropdown',
                    options=[{'label': pollutant, 'value': pollutant} for pollutant in pollutants],
                    value='PM10'  # Default pollutant
                ),
                dcc.Graph(id='map-graph')
            ]),
        ]),
        dcc.Tab(label='Line Chart of Pollutants', children=[
            html.Div([
                html.Label("Select Pollutant for Line Chart:"),
                dcc.Dropdown(
                    id='line-dropdown',
                    options=[{'label': 'All', 'value': 'All'}] + 
                            [{'label': pollutant, 'value': pollutant} for pollutant in pollutants],
                    value='All'  # Default to "All"
                ),
                dcc.Graph(id='line-graph')
            ]),
        ]),
        dcc.Tab(label='Forecast chart of Pollutants', children=[
            html.Div([
                html.Label("Select Pollutant for Line Chart:"),
                dcc.Dropdown(
                    id='forecast-dropdown',
                    options=[{'label': pollutant, 'value': pollutant} for pollutant in pollutants],
                    value='PM10'  # Default to "All"
                ),
                dcc.Graph(id='forecast-graph')
            ]),
        ]),
        dcc.Tab(label='Cig chart of Pollutants', children=[
            html.Div([
            dcc.Dropdown(
                    id='month-dropdown',
                    options=[{'label': 'All Months', 'value': 'all'}] + [{'label': month_name, 'value': i} for i, month_name in enumerate([
                'January', 'February', 'March', 'April', 'May', 'June', 
                'July', 'August', 'September', 'October', 'November', 'December'
            ], start=1)
        ],
        value='all'  # Default: "All Months"
    ),
    html.Label("Select Year:"),
    dcc.Dropdown(
        id='year-dropdown',
        options=[{'label': str(year), 'value': year} for year in cig_aggregated_data['year'].unique()],
        value=cig_aggregated_data['year'].unique()[0]  # Default: First available year
    ),
    dcc.Graph(id='cigarette-graph')
]),
]), ]), ])

# Callback to update the map based on dropdown selection
@app.callback(
    dash.dependencies.Output('map-graph', 'figure'),
    [dash.dependencies.Input('map-dropdown', 'value')]
)
def update_map(selected_pollutant):
    fig = px.scatter_map(
        station_data,
        lat="lat",
        lon="lon",
        color=selected_pollutant,
        size=selected_pollutant,
        hover_name="name",
        animation_frame="year",
        title=f"Pollution Levels by Station ({selected_pollutant})",
        color_continuous_scale=[
        (0.0, "green"),  # Low values are green
        (0.5, "yellow"),  # Medium values are yellow
        (1.0, "red")  # High values are red
    ],
    range_color=(0, 50)  # Adjust range to fit pollutant levels
    )
    fig.update_layout(height=900)
    return fig

# Callback to update the line chart based on dropdown selection
@app.callback(
    dash.dependencies.Output('line-graph', 'figure'),
    [dash.dependencies.Input('line-dropdown', 'value')]
)
def update_line_chart(selected_pollutant):
    if selected_pollutant == 'All':
        # Show all pollutants in the same chart
        fig = px.line(
            plot_data,
            x='year',
            y='Percentage',
            color='Pollutant',
            title="Yearly Change in Pollutant Levels (Baseline = 100%)",
            labels={'year': 'Year', 'Percentage': 'Percentage of Baseline (100%)'}
        )
    else:
        # Show only the selected pollutant
        fig = px.line(
            average_data,
            x='year',
            y=f'{selected_pollutant}_percentage',
            title=f"Yearly Change in {selected_pollutant} Levels (Baseline = 100%)",
            labels={'year': 'Year', f'{selected_pollutant}_percentage': 'Percentage of Baseline (100%)'}
        )

    fig.update_layout(transition_duration=500)
    fig.update_layout(showlegend=False)
    fig.update_layout(height=900)

    return fig

@app.callback(
    dash.dependencies.Output('forecast-graph', 'figure'),
    [dash.dependencies.Input('forecast-dropdown', 'value')]
)
def update_forecast(selected_pollutant):
    forecast = forecasts[selected_pollutant]
    
    fig = go.Figure()
    
    # Add observed data points
    if 'observed' in forecast:
        fig.add_trace(go.Scatter(
            x=forecast['ds'][:len(forecast['observed'])],
            y=forecast['observed'],
            mode='markers',
            name='Observed Data',
            marker=dict(color='blue', size=6)
        ))

    # Add forecast lines
    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat'],
        mode='lines',
        name='Expected Case (Forecast)',
        line=dict(color='orange')
    ))
    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat_lower'],
        mode='lines',
        name='Lower Bound',
        line=dict(dash='dot', color='gray')
    ))
    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat_upper'],
        mode='lines',
        name='Upper Bound',
        line=dict(dash='dot', color='gray')
    ))

    # Add a horizontal line for the pollutant threshold
    threshold = pollutant_thresholds[selected_pollutant]
    fig.add_shape(
        type="line",
        x0=forecast['ds'].min(),
        x1=forecast['ds'].max(),
        y0=threshold,
        y1=threshold,
        line=dict(color='red', dash='dash'),
        name=f"Threshold ({selected_pollutant})"
    )
    
    # Update layout
    fig.update_layout(
        title="Forecast",
        xaxis_title="Date",
        yaxis_title="Pollutant Levels",
        transition_duration=500,
        height=900
    )

    return fig


@app.callback(
    dash.dependencies.Output('cigarette-graph', 'figure'),
    [dash.dependencies.Input('month-dropdown', 'value'),
     dash.dependencies.Input('year-dropdown', 'value')])

def update_graph(selected_month, selected_year):
    # Filter data based on selected year and month
    if selected_month == 'all':  # If "All Months" is selected
        filtered_data = cig_aggregated_data[cig_aggregated_data['year'] == selected_year]
    else:  # If a specific month is selected
        filtered_data = cig_aggregated_data[
            (cig_aggregated_data['month'] == selected_month) & 
            (cig_aggregated_data['year'] == selected_year)
        ]
    
    x_coords = filtered_data['month']  # Months for x-axis
    y_coords = filtered_data['name']  # Station names for y-axis
    values = filtered_data['Cigarettes']  # Cigarette equivalents for hover and text

    # Create a figure
    fig = go.Figure()

    # Add text annotations for rounded values
    fig.add_trace(go.Scatter(
        x=x_coords,
        y=y_coords,
        mode='text',  # Display text annotations
        text=values.map(lambda x: f"{x:.2f}"),  # Round values and convert to string
        textfont=dict(size=12, color='black'),
        name=f"{'All Months' if selected_month == 'all' else f'Month {selected_month}'}, Year {selected_year}",
        textposition="bottom center",
        hovertemplate=(
            "Station: %{y}<br>"
            "Month: %{x}<br>"
            "Average Daily Cigarette Equivalent : %{text}<extra></extra>"
        )
    ))

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
                opacity=0.8
            )
        )

    # Update layout
    fig.update_layout(
        title=f"Cigarette Comparison for {'All Months' if selected_month == 'all' else f'Month {selected_month}'}, Year {selected_year}",
        xaxis=dict(title='Month', tickvals=list(range(1, 13)), ticktext=[
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
        ]),  # Month names as x-axis labels
        yaxis=dict(title='Station Name'),
        height=900,
        showlegend=False
    )

    return fig



# Run the app
if __name__ == '__main__':
    app.run(debug=False)
    
