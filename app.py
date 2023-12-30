import dash
from dash import Dash, Input, Output, dcc, html, State
import dash_bootstrap_components as dbc
from datetime import datetime
import json
import plotly.graph_objs as go


DATA_FILE = 'sleep_data.json'

class SleepEntry:
    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time

    def to_json(self):
        return {'start_time': self.start_time.isoformat(), 'end_time': self.end_time.isoformat()}

    @classmethod
    def from_json(cls, json_data):
        return cls(datetime.fromisoformat(json_data['start_time']), datetime.fromisoformat(json_data['end_time']))

class SleepData:
    def __init__(self):
        self.sleep_entries = []

    def add_entry(self, start_time, end_time):
        self.sleep_entries.append(SleepEntry(start_time, end_time))

    def save(self):
        with open(DATA_FILE, 'w') as f:
            json.dump([entry.to_json() for entry in self.sleep_entries], f)

    def load(self):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                self.sleep_entries = [SleepEntry.from_json(entry_data) for entry_data in data]
        except FileNotFoundError:
            pass


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])



app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Label("Start time (YYYY-MM-DD HH:MM):"),
            dcc.Input(id='start-input', type='text', value=''),
        ]),
        dbc.Col([
            html.Label("End time (YYYY-MM-DD HH:MM):"),
            dcc.Input(id='end-input', type='text', value=''),
        ]),
        dbc.Col([
            dbc.Button("Add", id='add-button', n_clicks=0),
        ]),
    ]),
    dbc.Row(id='visualize-rows'),
    html.Div(id='bar-chart')
], fluid=True)


@app.callback(
    Output('visualize-rows', 'children'),
    [Input('add-button', 'n_clicks')],
    [
        dash.dependencies.State('start-input', 'value'),
        dash.dependencies.State('end-input', 'value')
    ]
)
def add_sleep_entry(n_clicks, start_str, end_str):
    sleep_data = SleepData()
    sleep_data.load()

    if n_clicks > 0:
        try:
            start_time = datetime.strptime(start_str, '%Y-%m-%d %H:%M')
            end_time = datetime.strptime(end_str, '%Y-%m-%d %H:%M')

            if start_time >= end_time:
                raise ValueError("Start time must be before end time.")

            sleep_data.add_entry(start_time, end_time)
            sleep_data.save()

        except ValueError as e:
            print(str(e))

    return visualize_data_chart(sleep_data)

def visualize_data_chart(sleep_data):
    dates = []
    sleep_ranges = []

    for sleep_entry in sleep_data.sleep_entries:
        start_hour = sleep_entry.start_time.hour + sleep_entry.start_time.minute / 60
        end_hour = sleep_entry.end_time.hour + sleep_entry.end_time.minute / 60
        dates.append(sleep_entry.start_time.date())
        sleep_ranges.append((start_hour, end_hour))

    # create the bar chart with 24-hour bars    
    data = go.Bar(x=dates, 
                  y=[end_hour - start_hour for start_hour, end_hour in sleep_ranges],
                  base=[start_hour for start_hour, end_hour in sleep_ranges],
                  text=dates,
                  marker={'color': 'blue'},
                  name='Sleep Duration')

    return dcc.Graph(
        id='sleep-duration-bar-chart',
        figure={
            'data': [data],
            'layout': go.Layout(
                title='Sleep Duration per Day',
                xaxis={'title': 'Date', 'tickformat': '%Y-%m-%d'}, 
                yaxis={'title': 'Hour of the Day',
                       'range': [0, 24],  
                       'tickvals': list(range(25)), 
                       'ticktext': [f"{hour:02d}:00" for hour in range(25)]},  
                barmode='stack',
            )
        },
        style={'height': '1000px'} 
    )

if __name__ == "__main__":
    app.run_server(debug=True)