import pandas as pd
import plotly.express as px  # (version 4.7.0)
import sqlite3
import dash  # (version 1.12.0) pip install dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from datetime import datetime

app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{
                    "name": "viewport",
                    "content": "width=device-width, initial-scale=1"},
                ], )


# ------------------------------------------------------------------------------
# Return data as HTML table
def generate_table(dataframe: pd.DataFrame, max_rows: int = 10) -> str:
    """
    :param dataframe: dataframe to show
    :param max_rows: max number of rows to display
    :return: the HTML table
    """
    table_header = []
    for col in dataframe.columns:
        table_header.append(html.Th(col))
    table_header = [html.Thead(html.Tr(table_header))]

    table_body = []
    for i in range(min(len(dataframe), max_rows)):
        row = []
        for col in dataframe.columns:
            row.append(html.Td(dataframe.iloc[i][col]))
        table_body.append(html.Tr(row))
    table_body = [html.Tbody(table_body)]

    return dbc.Table(table_header + table_body, bordered=True)


# -------------------------------------------------------------------------------
# Calculate age from data frame df_birth_date
def create_age_df(df_birth_date: pd.DataFrame) -> pd.DataFrame:
    df_age = df_birth_date.apply(
        lambda x: (datetime.now().date() - x) / 365.2425)
    #    # seems odd to use .days...
    return df_age.apply(lambda x: x.days)


# ------------------------------------------------------------------------------
# Import and clean data (importing csv into pandas)
db_con = sqlite3.connect('data.sqlite3')
db_cur = db_con.cursor()

sql = f'select * from respondents'
rows = db_cur.execute(sql)
columns = []
for column in db_cur.description:
    columns.append(column[0].lower())
df = pd.DataFrame(rows, columns=columns)
db_con.close()

for d in ['start_dt', 'status_dt', 'birth_date']:
    df[d] = pd.to_datetime(df[d]).dt.date
df['age'] = create_age_df(df['birth_date'])


# print(df.info())
# print(df.head(10))

# ------------------------------------------------------------------------------
#
def bld_options(df):
    """
    Build list of dicts from dataframe column names
    :param df:
    :return: HTML select as string
    """
    cols = df.columns.tolist()
    options = []
    for col in cols:
        options.append({"label": col, "value": col})
    return options


# ------------------------------------------------------------------------------
# App layout
app.layout = html.Div([
    dbc.Row(dbc.Col(html.H3('NPM Respondents Dash', style={'textAlign': 'center'}),
                    width={'size': 6, 'offset': 3},
                    ),
            ),
    dbc.Row(dbc.Col(generate_table(df), width={'size': 10, 'offset': 1}, )
            ),
    dbc.Row([
        dbc.Col(dbc.Label("X-axis"),
                width={'size': 1, 'offset': 1}),
        dbc.Col(dcc.Dropdown(id="select_option", options=bld_options(df),
                             multi=False,
                             value="sex", ),
                width=2),
        dbc.Col(dbc.Label("Select"),
                width={'size': 1, 'offset': 1}),
        dbc.Col(dcc.Dropdown(id="select_option2",
                             options=bld_options(df),
                             multi=False,
                             value="sex",
                             ),
                width=2),
    ], no_gutters=False
    ),
    dbc.Row(
        [
            dbc.Col(dcc.Graph(id='respondents_map', figure={}),
                    width={'size': 10, "offset": 1}
                    ),
        ]
    )
])


# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(
    Output(component_id='respondents_map', component_property='figure'),
    [
        Input('select_option', 'value'),
        Input('select_option2', 'value')
    ])
def update_graphs(option_selected, option2_selected):
    fig = px.histogram(df,  # dataframe
                       x=option_selected,  # x-values column
                       #                   nbins=10,        #number of bins
                       color=option2_selected
                       )
    # Plotly Express
    return fig  # , pv


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)
