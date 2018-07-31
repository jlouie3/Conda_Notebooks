import os
import json
import numpy as np
import pandas as pd


def get_rolling_mean(values, window):
    """Return rolling mean of given values, using specified window size."""
    return values.rolling(center=False, window=window).mean()


def get_rolling_std(values, window):
    """Return rolling standard deviation of given values, using specified window size."""
    return values.rolling(center=False, window=window).std()


def get_bollinger_bands(rm, rstd, b=2):
    """Return upper and lower Bollinger Bands."""
    upper_band = rm + b*rstd
    lower_band = rm - b*rstd
    return upper_band, lower_band


def get_momentum(values, window):
    momentum = values - values.shift(window)
    return momentum


def alpha(data: pd.DataFrame):
    """
    Strategy version alpha.

    State members:
        Bollinger bands: nearest .5 * N * std_dev
        Momentum: 1-day momentum

    :return: state_df: pd.DataFrame of transformed data
    """

    # Define state features
    window = 20

    data['rm'] = get_rolling_mean(data['close'], window)
    data['rstd'] = get_rolling_std(data['close'], window)
    data['ubb_1.5'], data['lbb_1.5'] = get_bollinger_bands(data['rm'], data['rstd'], b=1.5)
    data['ubb_2.0'], data['lbb_2.0'] = get_bollinger_bands(data['rm'], data['rstd'], b=2)
    data['ubb_2.5'], data['lbb_2.5'] = get_bollinger_bands(data['rm'], data['rstd'], b=2.5)
    data['mom_2'] = get_momentum(data['close'], window=2)
    data['rstd_5'] = get_rolling_std(data['close'], 2)

    state_df = pd.DataFrame(data={
        'bb_.5': np.floor(((data['close'] - data['rm']) / data['rstd']) * 2) / 2,  # Floors rolling std to nearest half
        'momentum': pd.Series(['up' if x > 0 else 'down' if x < 0 else 'same' for x in data['mom_2']],
                              index=data.index),
        'hasCash': None,
        'hasStock': None
    })

    return state_df


def beta(data: pd.DataFrame):
    """
    Strategy version alpha.

    State members:
        Bollinger bands: +/- (2 * std_dev)
        Momentum: 1-day momentum

    :return: state_df: pd.DataFrame of transformed data
    """

    # Define state features
    window = 20

    data['rm'] = get_rolling_mean(data['close'], window)
    data['rstd'] = get_rolling_std(data['close'], window)
    data['ubb_1.5'], data['lbb_1.5'] = get_bollinger_bands(data['rm'], data['rstd'], b=1.5)
    data['ubb_2.0'], data['lbb_2.0'] = get_bollinger_bands(data['rm'], data['rstd'], b=2)
    data['ubb_2.5'], data['lbb_2.5'] = get_bollinger_bands(data['rm'], data['rstd'], b=2.5)
    data['mom_2'] = get_momentum(data['close'], window=2)
    data['rstd_5'] = get_rolling_std(data['close'], 2)

    data['bb_2'] = data.apply(lambda row: "1" if row['close'] > row['ubb_2.0'] else "-1" if row['close'] < row['lbb_2.0'] else "0",
                              axis=1)

    state_df = pd.DataFrame(data={
        'bb_2': data['bb_2'],
        'momentum': pd.Series(['up' if x > 0 else 'down' if x < 0 else 'same' for x in data['mom_2']],
                              index=data.index),
        'hasCash': None,
        'hasStock': None
    })

    return state_df
