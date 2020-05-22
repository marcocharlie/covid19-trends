import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from warnings import filterwarnings
import plotly.io as pio


filterwarnings('ignore')


def clean_data(df):
    # filter data
    df = df[["denominazione_regione","totale_casi","data"]].rename(
        columns={"denominazione_regione":"region","totale_casi":"total_cases", "data":"date"})

    df["date"] = df["date"].str[0:10]

    # get weekly absolute growth of cases with groupby on region
    df = df.assign(new_weekly_cases = lambda x : x.groupby("region",group_keys=False).apply(
        lambda i: i["total_cases"] - i["total_cases"].shift(7) ))

    # data cleaning
    df.loc[(df["date"] < "2020-03-31")&(df["total_cases"] < 10), "total_cases"] = np.nan
    df.loc[(df["date"] < "2020-03-31")&(df["new_weekly_cases"] < 10), "new_weekly_cases"] = np.nan
    
    return df


# reference date
today = datetime.now()
yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
today = today.strftime("%Y-%m-%d")

data_url_filepath = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni.csv"

df = pd.read_csv(data_url_filepath, error_bad_lines=False)

# clean data
df = clean_data(df)

reference_date = df.tail(1)["date"].values[0]

# range data
days = list(df["date"].unique())
regions = list(df["region"].unique())

xm = df["total_cases"].min()
xM = df["total_cases"].max()

ym = df["new_weekly_cases"].min()
yM = df["new_weekly_cases"].max()


## add config
config = {
    "scrollZoom": True,
    "displayModeBar": True,
}

## add play and pause buttons
visible_lines = [True for i in range(len(regions))]
plot_title = "Italian regions Trajectory of COVID-19 Cases (%s)" %reference_date

buttons = [
    {
        "label": "Play",
        "method": "animate",
        "args": [None, 
              {
                  "frame":{"duration": 200, "redraw": False},
                  "transition": {"duration": 300, "easing": "quadratic-in-out"},
                  "fromcurrent": True
              }
             ]
    },
    {
        "label": "Pause",
        "method": "animate",
        "args": [[None], # None must be in list
                 {
                     "frame":{"duration": 0, "redraw": False},
                     "transition": {"duration": 0},
                     "mode": "immediate"
                 }
                ]
    }
]

dropdowns = [
    {
        "label": "Log Scale",
        "method": "update",
        "args": [{"visible": visible_lines},
                 {"title": "%s - Logarithm" %plot_title,
                  "xaxis": {"title":"Total Cases", "type": "log", "autorange": False, "range":[np.log10(xm*1.2), np.log10(xM*2)]},
                  "yaxis": {"title": "New Weekly Cases", "type": "log", "autorange": False, "range":[np.log10(ym*1.2), np.log10(yM*2)]}}]
    },
    {
        "label": "Linear Scale",
        "method": "update",
        "args": [{"visible": visible_lines},
                 {"title": plot_title,
                  "xaxis": {"title": "Total Cases", "type": "linear", "autorange": False, "range":[xm, xM+50000]},
                  "yaxis": {"title": "New Weekly Cases", "type": "linear", "autorange": False, "range":[ym, yM+50000]}}]
    }
]

# add menu
menu = [
    {
        "type": "buttons", 
        "buttons": buttons, 
        "showactive": True,
        "direction": "left",
        "y": 0, "x": 0.1,
        "yanchor": "top",
        "xanchor": "right",
        "pad": {"t": 87, "r": 10}        
    },
    {
       "type": "dropdown", 
        "active": 0,
        "buttons": dropdowns, 
        "showactive": True,
        "direction": "down",
        "y": 1.2, "x": 0.1,
        "yanchor": "top",
        "xanchor": "right",
        #"pad": {"t": 57, "r": 10} 
    }
]

# add Source
annotations = []
annotations.append({"xref":"paper", "yref":"paper", "x":0.5, "y":-0.15,
                    "xanchor":"center", "yanchor": "top",
                    "text":"Dati forniti dal Ministero della Salute - Elaborazione e gestione dati a cura del Dipartimento della Protezione Civile",
                    "font":{"family":"Arial", "size":12, "color":"rgb(150,150,150)"},
                    "showarrow":False})


# add slider
sliders = [{
    "active": 0,
    "yanchor": "top", "xanchor": "left",
    "currentvalue": {
        "font": {"size": 20},
        #"prefix": "Day:",
        "visible": True,
        "xanchor": "right",
        #"active": 0
    },
    "transition": {"duration": 50, "easing": "cubic-in-out"},
    "pad": {"b": 10, "t": 50},
    "len": 0.9,
    "x": 0.1, "y": -0.1,
    "steps": [],
    "visible": True
}]


# make data
plot_data = []

for region in regions:
    temp_df = df[df["region"] == region]
    trace = go.Scatter(x=temp_df["total_cases"][:2], #initializing line
                       y=temp_df["new_weekly_cases"][:2], #initializing line
                       mode="lines",
                       line=dict(width=2.5),
                       name=region)

    plot_data.append(trace)


# make frames
numerosity = len(days)
#traces = [i for i in range(len(regions))] # one line for each region
frames = []

#for day in range(1, numerosity-1):
for i, day in enumerate(days):

    frame_dict = {
        #"traces": traces, 
        "data": [],
        "name": day
    }

    for region in regions:

        #df_by_day_and_region = df[(df["date"] == day) & (df["region"] == region)]

        region_data = {
            "type":"scatter",
            "mode": "lines+text",
            "text": [None for i in range(0,i)]+[region],
            "textposition": "bottom right",
            "x": df[df["region"]==region]["total_cases"][:i+1],
            "y": df[df["region"]==region]["new_weekly_cases"][:i+1],
            "name": region,
            #"customdata": [day]
        }

        frame_dict["data"].append(region_data)

    frames.append(frame_dict)

    slider_step = {
        "args": [
            [day],
            {
                "frame": {"duration": 50, "redraw": False},
                "mode": "immediate",
                "transition": {"duration": 50}
            }
        ],
        "label": day, 
        "method": "animate", 
        #"value": day
    }

    sliders[0]["steps"].append(slider_step)


# complete layout
layout = go.Layout(
    width=1050,
    height=700,
    showlegend=False,
    annotations=annotations,
    hovermode="closest",
    updatemenus=menu,
    sliders=sliders,
    xaxis =dict(title="Total Cases", type="log", range=[np.log10(xm*1.2), np.log10(xM*2)], autorange=False),
    yaxis =dict(title="New Weekly Cases", type="log", range=[np.log10(ym*1.2), np.log10(yM*2)], autorange=False),
    title=dict(text="%s - Logarithm" %plot_title, y=0.90, x=0.5, xanchor="center", yanchor="top")
)

# show plot

fig = go.Figure(data=plot_data, frames=frames, layout=layout)
#fig.show(config=config)

pio.write_html(fig, file="index.html", auto_open=True)
