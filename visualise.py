"""Visualisation module for vinskraper."""

from typing import Optional

import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go


# Colour scheme for the application.
# Used for the style of the application and the plots.
_COLOUR = {
    'black': '#06070E',
    'white': '#FFFFFF',

    'red': '#8E3B46',
    'green': '#136F63',
    'greenish': '#F3F7F4',
}


def graph(record, columns) -> Optional[str]:
    """
    Return a JSON-string of the plotly graph for the given record.

    Parameters
    ----------
    record : dict
        The record to plot.
    columns : List[str]
        The (price) columns to plot.
    """
    prices = [record[price] for price in columns] + [record[columns[-1]]]
    dates = [pd.Timestamp(price.split(' ')[1]) for price in columns] + [pd.Timestamp.now()]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        name=record['navn'],

        x=dates,
        y=prices,

        mode='lines',
        line={'shape': 'hv', 'width': 3, 'color': _COLOUR['green']},

        fill='tozeroy',
        fillcolor=_COLOUR['greenish'],
    ))

    fig.update_layout(
        plot_bgcolor=_COLOUR['white'],
        height=300,

        margin={
            't': 10,
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

    return pio.to_json(fig)
