"""Visualisation module for vinskraper."""

import pandas as pd
import plotly.graph_objects as go


def graph_best_prices(state):
    for idx, product in state['data']['best'].to_dict().items():
        if product['prisendring'] == 0.0:
            break

        dates = [pd.Timestamp(price.split(' ')[1])
                 for price in product.keys()
                 if price.startswith('pris ')]
        prices = [product[f'pris {date.strftime("%Y-%m-%d")}'] for date in dates]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates + [pd.Timestamp.now()],
            y=prices + [product['pris']],
            mode='lines',
            line={'shape': 'hv', 'width': 3, 'color': state['plot']['colours']['green']},
            name=product['navn'],
        ))

        fig.update_layout(
            title='Prisutvikling',
            plot_bgcolor=state['plot']['colours']['white'],
            height=350,
        )
        fig.update_xaxes(
            showgrid=False,
            tickangle=45, tickvals=dates, ticktext=[date.strftime('%y-%m-%d') for date in dates]
        )
        fig.update_yaxes(showgrid=False)

        state['plot']['best'][idx] = fig
