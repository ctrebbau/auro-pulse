import pandas as pd
import dash
from dash import dcc, html
from dash import dash_table
from dash.dependencies import Input, Output
from dash import html
import plotly.express as px
import dash_bootstrap_components as dbc
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from db_utils import *

from datetime import datetime, timedelta

today = datetime.today().date()
seven_days_prior = today - timedelta(days=7)
statuses = fetch_statuses()
managers = fetch_managers()
# Initialize the Dash app

BOOTSTRAP_THEME = dbc.themes.BOOTSTRAP
app = dash.Dash(__name__, external_stylesheets=[BOOTSTRAP_THEME])
app.title = "Vehicle Status Dashboard"

# Navbar for the title
navbar_title = html.Nav(
    className="navbar navbar-expand-lg navbar-dark bg-dark mb-2",
    children=[
        html.Div(
            className="container-fluid",
            children=[
                html.Span("Vehicle Status Dashboard", className="navbar-brand")
            ]
        )
    ]
)

company_filter = html.Nav(
    className="navbar navbar-expand-lg mb-2",
    children=[
        html.Div(
            className="container-fluid",
            children=[
                html.Div(
                    dcc.Dropdown(
                        id='company-dropdown',
                        options=[
                            {'label': 'Auro', 'value': 'auro'},
                            {'label': 'Cibeles', 'value': 'cibeles'},
                            {'label': 'Gestionados', 'value': 'gestionados'},
                            {'label': 'All', 'value': 'all'}
                        ],
                        value='all',
                        clearable=False,
                        placeholder="Select company"
                    ), className="d-inline-block w-100"  # Added margin
                )
            ]
        )
    ]
)


# Navbar for status selection
status_filter = html.Nav(
    className="navbar navbar-expand-lg mb-2",
    children=[
        html.Div(
            className="container-fluid",
            children=[
                html.Div(
                    dcc.Dropdown(
                        id='status-dropdown',
                        options=[],  # Populated dynamically
                        value=[],
                        multi=True,
                        clearable=True,
                        placeholder="Select statuses"
                    ), className="d-inline-block w-100"  # Full width
                )
            ]
        )
    ]
)

# Navbar for manager
manager_filter = html.Nav(
    className="navbar navbar-expand-lg mb-2",
    children=[
        html.Div(
            className="container-fluid",
            children=[
                html.Div(
                    dcc.Dropdown(
                        id='manager-dropdown',
                        options=[],  # Populated dynamically
                        value=[],
                        multi=True,
                        clearable=True,
                        placeholder="Select managers"
                    ), className="d-inline-block w-100"  # Full width
                )
            ]
        )
    ]
)

# Navbar for date range picker
date_range_picker = html.Nav(
    className="navbar navbar-expand-lg mb-2",
    children=[
        html.Div(
            className="container-fluid",
            children=[
                html.Div(
                    dcc.DatePickerRange(
                        id='date-picker-range',
                        start_date=seven_days_prior,
                        end_date=today,
                        display_format='YYYY-MM-DD'
                    ), className="d-inline-block w-100"  # Full width
                )
            ]
        )
    ]
)

# Navbar for radio buttons
navbar_options = html.Nav(
    className="navbar navbar-expand-lg mb-2",
    children=[
        html.Div(
            className="container-fluid",
            children=[
                html.Div(
                    dcc.RadioItems(
                        id='count-proportion-radio',
                        options=[
                            {'label': 'Count', 'value': 'count'},
                            {'label': 'Proportion', 'value': 'proportion'}
                        ],
                        value='proportion',
                        inline=True
                    ), className="d-inline-block me-2"  # Added margin
                ),
                html.Div(
                    dcc.RadioItems(
                        id='log-scale-radio',
                        options=[
                            {'label': 'Linear Scale', 'value': 'linear'},
                            {'label': 'Logarithmic Scale', 'value': 'log'}
                        ],
                        value='linear',
                        inline=True,
                        style={'display': 'none'}
                    ), className="d-inline-block" 
                )
            ]
        )
    ]
)

app.layout = html.Div([
    navbar_title,
    manager_filter,
    company_filter,
    status_filter,
    date_range_picker,
    navbar_options,
    dbc.Row(id='graphs-container', children=[])
])


@app.callback(
    [Output('manager-dropdown', 'options'),
     Output('status-dropdown', 'options')],
    Input('company-dropdown', 'value')
)
def set_dropdown_options(selected_company):
    managers = fetch_managers()
    statuses = fetch_statuses()
    manager_options = [
        {'label': manager, 'value': manager} for manager in managers['name']
    ]
    status_options = [
        {'label': status, 'value': status} for status in statuses['status']
    ]
    return manager_options, status_options


@app.callback(
    Output('log-scale-radio', 'style'),
    [Input('count-proportion-radio', 'value')]
)
def toggle_log_scale_radio(selected_option):
    if selected_option == 'count':
        return {'display': 'inline-block'}
    else:
        return {'display': 'none'}


@app.callback(
    Output('graphs-container', 'children'),
    [Input('company-dropdown', 'value'), 
     Input('date-picker-range', 'start_date'), 
     Input('date-picker-range', 'end_date'),
     Input('manager-dropdown', 'value'),
     Input('status-dropdown', 'value'),
     Input('count-proportion-radio', 'value'),
     Input('log-scale-radio', 'value')]
)
def update_line_graphs(selected_company, start_date, end_date, selected_managers, 
                  selected_statuses, plot_type, log_scale):
    if not selected_managers:
        return [html.Div("No manager selected. Please select a manager to "
                         "display the data.")]

    # Fetching data from the database
    df = select_company(
        company=selected_company, 
        from_date=start_date, 
        to_date=end_date
    )

    # Define a color map for statuses
    unique_statuses = df['status'].unique()
    colors = px.colors.qualitative.Plotly
    color_map = {
        status: colors[i % len(colors)] 
        for i, status in enumerate(unique_statuses)
    }

    rows = []
    graphs_per_row = 2  # Define how many graphs per row

    for i in range(0, len(selected_managers), graphs_per_row):
        managers_in_row = selected_managers[i:i + graphs_per_row]

        # Create a subplot for the graphs
        fig = make_subplots(
            rows=1, 
            cols=len(managers_in_row), 
            shared_yaxes=True, 
            subplot_titles=managers_in_row
        )

        for j, manager in enumerate(managers_in_row, start=1):
            manager_data = df[df['manager'] == manager]
            manager_data = proportion_data(manager_data)
            
            # Filter by selected statuses
            if selected_statuses:
                manager_data = manager_data[
                    manager_data['status'].isin(selected_statuses)
                ]
            manager_data = manager_data.drop(columns=['manager'])

            y_axis = (
                'proportion' if plot_type == 'proportion' else 'count'
            )
            y_scale = (
                'log' if plot_type == 'count' and log_scale == 'log' else 'linear'
            )

            # Show legend only for the last subplot in each row
            show_legend = j == len(managers_in_row)

            for status in unique_statuses:
                if status in manager_data['status'].unique():
                    status_data = manager_data[manager_data['status'] == status]
                    fig.add_trace(
                        go.Scatter(
                            x=status_data['date'], 
                            y=status_data[y_axis], 
                            mode='lines', 
                            name=status,
                            line=dict(color=color_map[status]),
                            showlegend=show_legend
                        ),
                        row=1, col=j
                    )

            fig.update_yaxes(type=y_scale, row=1, col=j)

        fig.update_layout(height=400)
        graph_row = dbc.Row([dbc.Col(dcc.Graph(figure=fig), width=12)])
        rows.append(graph_row)

        # Create and append the data tables for each manager
        table_row = []
        for manager in managers_in_row:
            manager_data = df[df['manager'] == manager]
            manager_data = proportion_data(manager_data)
            if selected_statuses:
                manager_data = manager_data[
                    manager_data['status'].isin(selected_statuses)
                    ]
            manager_data = manager_data.drop(columns=['manager'])
            columns_order = ['status', 'date', 'count', 'total_count', 'proportion']
            table_data = dash_table.DataTable(
                columns=[{"name": i, "id": i} for i in columns_order],
                data=manager_data.to_dict('records'),
                style_table={
                    'overflowY': 'scroll',
                    'maxHeight': '200px',
                    'overflowX': 'scroll'
                    },
            )

            table_row.append(
                dbc.Col(table_data, width=12 // len(managers_in_row))
                )

        rows.append(dbc.Row(table_row))

    return rows



def proportion_data(df):
    grouped_data = df.groupby(['date', 'manager', 'status']).size().reset_index(name='count')
    total_cars_per_manager_date = df.groupby(['date', 'manager']).size().reset_index(name='total_count')
    proportion_data = pd.merge(grouped_data, total_cars_per_manager_date, on=['date', 'manager'])
    proportion_data['proportion'] = proportion_data['count'] / proportion_data['total_count']
    proportion_data['proportion'] = proportion_data['proportion'].apply(lambda x: round(x, 2))
    return proportion_data
# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
