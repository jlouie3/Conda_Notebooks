import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import Projects.ReinforcmentLearning.Strategy as Strategy


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
# Choose strategy to use
# state_df = Strategy.alpha(data)
state_df = Strategy.beta(data)
print(state_df.head())
reward_df = data[['close']]
########################
########################

# from Projects.ReinforcmentLearning.Q_Learner import Q_Learner
# q_learner = Q_Learner(state_df=state_df.iloc[20:25], reward_df=reward_df.iloc[20:25])
# q_learner.train(50, 400)
# q_learner.export_policy('policy.txt')

train_data = state_df.loc['2013-01-01':'2016-12-31']
test_data = state_df.loc['2017-01-01':'2017-12-31']
train_price_data = reward_df.loc['2013-01-01':'2016-12-31']
test_price_data = reward_df.loc['2017-01-01':'2017-12-31']

# from Projects.ReinforcmentLearning.DynaQLearner import DynaQLearner
# #d_q_learner = DynaQLearner(state_df=state_df.iloc[20:25], price_df=reward_df.iloc[20:25], p_explore=.2)
# d_q_learner = DynaQLearner(state_df=train_data, price_df=train_price_data, p_explore=.2)
# d_q_learner.train(100, 400)
# d_q_learner.export_policy('output' + os.sep + 'policy.txt')
# d_q_learner.export_q_table('output' + os.sep + 'q_table.txt')


with open('output' + os.sep + 'policy.txt', 'r') as f:
    policy = json.loads(f.readline())
from Projects.ReinforcmentLearning.MarketSimulator import MarketSimulator
market_sim = MarketSimulator(test_data, test_price_data, policy, 5)
market_sim.run()
market_sim.plot_moves()
pass
