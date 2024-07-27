"""Visualisation module for vinskraper."""

import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go


# Colour scheme for the application.
# Used for the style of the application and the plots.
_COLOUR = {
    'black': '#06070E',
    'white': '#FFFFFF',

    'red': '#8E3B46',
    'redish': '#f3ebec',
    'green': '#136F63',
    'greenish': '#F3F7F4',
}


def graph(
    df: pd.DataFrame,
    prices: list[str]
) -> pd.Series:
    """
    Creates the price plot for the given data.

    Parameters
    ----------
    df : pd.DataFrame
        The data to plot.
    prices : list[str]
        The columns to plot.

    Returns
    -------
    pd.Series
        The plots, with the same index as `df`.
    """
    dates = [pd.Timestamp(price.split(' ')[1]) for price in prices] + [pd.Timestamp.now()]

    figures = []

    for _, record in df.iterrows():
        diff = 0 if len(prices) < 2 else record[prices[-1]] - record[prices[-2]]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            name=record['navn'],

            x=dates,
            y=[record[price] for price in prices] + [record[prices[-1]]],

            mode='lines',
            line={
                'shape': 'hv',
                'width': 3,
                'color': _COLOUR['green'] if diff >= 0 else _COLOUR['red'],
            },

            fill='tozeroy',
            fillcolor=_COLOUR['greenish'] if diff >= 0 else _COLOUR['redish'],
        ))

        fig.update_layout(
            plot_bgcolor=_COLOUR['white'],
            height=300,

            margin={
                't': 20,
                'b': 0,
                'l': 0,
                'r': 0,
            },

            title={
                'text': '',
                'font': {
                    'family': 'Poppins, sans-serif',
                    'color': _COLOUR['black'],
                }
            },

            xaxis={
                'title': {
                    'text': '',
                    'font': {
                        'size': 16,
                        'weight': 'bold',
                        'family': 'Poppins, sans-serif',
                        'color': _COLOUR['black'],
                    },
                },
                'tickfont': {
                    'size': 12,
                    'family': 'Poppins, sans-serif',
                    'color': _COLOUR['black'],
                },
                'showgrid': False,
            },

            yaxis={
                'title': {
                    'text': '',
                    'font': {
                        'size': 16,
                        'weight': 'bold',
                        'family': 'Poppins, sans-serif',
                        'color': _COLOUR['black'],
                    },
                },
                'tickfont': {
                    'size': 12,
                    'family': 'Poppins, sans-serif',
                    'color': _COLOUR['black'],
                },
                'ticksuffix': ' kr',
                'tickvals': sorted(set(prices)),
                'showgrid': False,
            },
        )

        figures.append(pio.to_json(fig))

    return pd.Series(figures, index=df.index)
