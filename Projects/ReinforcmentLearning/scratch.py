import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


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


# Read data
filePath = 'data/spy_5yrs.csv'
# data = fin.get_data(filePath,)
data = pd.read_csv(filePath)

# Remove first row (bad data)
data = data.iloc[1:]
data.index = data['date']

# Sort data by index (ascending)
data = data.loc[sorted(data.index)]

# Take only the daily close data and normalize it
data = pd.DataFrame(data['close'])
data['close'] = data['close']/data['close'].iloc[0]
data.head()


########################
########################

# Define state features
window = 20

data['rm'] = get_rolling_mean(data['close'], window)
data['rstd'] = get_rolling_std(data['close'], window)
data['ubb_1.5'], data['lbb_1.5'] = get_bollinger_bands(data['rm'],data['rstd'],b=1.5)
data['ubb_2.0'], data['lbb_2.0'] = get_bollinger_bands(data['rm'],data['rstd'],b=2)
data['ubb_2.5'], data['lbb_2.5'] = get_bollinger_bands(data['rm'],data['rstd'],b=2.5)
data['mom_2'] = get_momentum(data['close'], window=2)
data['rstd_5'] = get_rolling_std(data['close'], 2)

state_df = pd.DataFrame(data={
    'bb_.5': np.floor(((data['close'] - data['rm']) / data['rstd']) * 2) / 2, # Floors rolling std to nearest half
    'momentum': pd.Series(['up' if x>0 else 'down' if x<0 else 'same' for x in data['mom_2']],index=data.index),
    'hasCash': None,
    'hasStock': None
})

reward_df = data[['close']]
########################
########################

# from Projects.ReinforcmentLearning.Q_Learner import Q_Learner
# q_learner = Q_Learner(state_df=state_df.iloc[20:25], reward_df=reward_df.iloc[20:25])
# q_learner.train(50, 400)
# q_learner.export_policy('policy.txt')

from Projects.ReinforcmentLearning.DynaQLearner import DynaQLearner
q_learner = DynaQLearner(state_df=state_df.iloc[20:25], price_df=reward_df.iloc[20:25])
q_learner.train(50, 400)
q_learner.export_policy('policy.txt')
