'''
Add pydocs w/ pycharm
Add verbose/persist options for console logging and logging to disk
    logger class modified by persist and verbose
    logger.log()
'''

import pandas as pd
import json
import random


class Q_Learner:
    ###################
    # Define constants
    ###################

    # Possible actions
    BUY = 'buy'
    SELL = 'sell'
    HOLD = 'hold'

    #################
    # Define members
    #################
    # Learning variables
    alpha = .9
    gamma = .9
    p_explore = .1
    q_table = {}

    # Reward function variables
    reward_df = None
    cash = 0
    stock = 0
    initial_portfolio_value = 0
    portfolio_value = 0

    # State advancement variables
    state_df = None
    state = None
    actions = []
    num_states = 0
    state_index = 0

    def __init__(self,
                 state_df: pd.DataFrame,
                 reward_df: pd.DataFrame,
                 cash: int=5,
                 alpha: float=.9,
                 gamma: float=.9,
                 p_explore: float=.1):
        # Assign parameter values
        self.state_df = state_df
        self.reward_df = reward_df
        self.cash = cash
        self.alpha = alpha
        self.gamma = gamma
        self.p_explore = p_explore

        self.initialize_state()
        self.initial_portfolio = self.get_portfolio_value()

    def initialize_state(self):
        self.num_states = self.state_df.shape[0]
        self.state_index = 0
        self.state = self.state_df.iloc[self.state_index]
        self.actions = self.get_possible_actions(self.state)

    def train(self, iterations: int, dyna_iterations: int = 400):
        for iteration in range(iterations):
            self.initialize_state()
            while self.next_state_exists():
                prev_state = self.state.copy()
                action, action_type = self.get_action()
                reward = self.go_to_next_state(action)
                self.update_q(prev_state, action, self.state, reward)

    def update_q(self, state: pd.Series, action: str, next_state, reward):
        # Bellman Equation
        # q[s][a] = q[s][a] + alpha[r + g*max_a'(q[s'][a']) - q[s][a]]
        q = self.q_table[self.state_action_str(state, action)]
        self.q_table[self.state_action_str(state, action)] =\
            q + self.alpha * (reward + self.gamma * (self.get_max_q_value(next_state)) - q)

    def get_portfolio_value(self):
        return self.cash + self.stock * self.reward_df.iloc[self.state_index]['close']

    def reward(self):
        # Cumulative return based on portfolio value
        return self.get_portfolio_value() / self.initial_portfolio_value

    def next_state_exists(self):
        return self.state_index < self.num_states - 1

    def get_next_state(self, state: pd.Series, action: str):
        next_state = self.state_df.iloc[self.state_index+1]

        if action == self.BUY:
            has_cash = False
            has_stock = True
        elif action == self.SELL:
            has_cash = True
            has_stock = False
        else:  # HOLD
            has_cash = state['hasCash']
            has_stock = state['hasStock']

        if self.state_index < self.num_states:
            next_state['hasCash'] = has_cash
            next_state['hasStock'] = has_stock

        return next_state

    def go_to_next_state(self, action: str):
        # Apply action to portfolio
        stock_price = self.reward_df.iloc[self.state_index]['close']
        if action == self.BUY:
            stock_to_buy = int(self.cash / stock_price)
            self.stock += stock_to_buy
            self.cash -= stock_to_buy * stock_price
        elif action == self.SELL:
            self.cash += self.stock * stock_price
            self.stock = 0
        else:  # HOLD
            pass  # Do Nothing

        # Advance to next state
        self.state = self.get_next_state(self.state, action)
        self.state_index += 1
        self.actions = self.get_possible_actions(self.state)

        # Calculate and return reward for entering this state
        reward = self.reward()
        return reward

    def get_possible_actions(self, state: pd.Series):
        actions = [self.HOLD]

        if state.iloc[0]['hasCash']:
            actions.append(self.BUY)

        if state.iloc[0]['hasStock']:
            actions.append(self.SELL)

        self.initialize_q_values(state, self.actions)

        return actions

    def get_action(self):
        action_type = 'exploit'
        action = self.get_exploitation_action(self.state)

        if random.uniform(0, 1) < self.p_explore:
            action_type = 'explore'
            action = self.get_exploration_action(action)

        return action, action_type

    def get_exploitation_action(self, state: pd.Series):
        q_values = {}
        for action in self.actions:
            state_action_str = self.state_action_str(state, action)
            q_values[action] = self.q_table[state_action_str]

        # Return action that yields max q-value from this state
        return max(q_values, key=q_values.get)

    def get_exploration_action(self, exploit_action: str):
        actions = self.actions.copy()
        actions.remove(exploit_action)
        return random.choice(actions)

    def initialize_q_values(self, state: pd.Series, actions: list):
        for action in actions:
            state_action_str = self.state_action_str(state, action)

            # Initialize with tiny value
            if state_action_str not in self.q_table:
                self.q_table[state_action_str] = random.uniform(0, 1) / 1000000000

    def get_max_q_value(self, state: pd.Series):
        action = self.get_exploitation_action(state)
        return self.q_table[self.state_action_str(state, action)]

    def state_action_str(self, state: pd.Series, action: str):
        state_str = json.dumps(state.to_dict(), sort_keys=True)
        return str((state_str, action))
