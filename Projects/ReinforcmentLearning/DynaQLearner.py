'''
Add pydocs w/ pycharm
Add verbose/persist options for console logging and logging to disk
    logger class modified by persist and verbose
    logger.log()
'''

import pandas as pd
import json
import random

class DynaQLearner:
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
    alpha = .1
    gamma = .9
    p_explore = .1
    q_table = {}    # state_str: {action: q-value}

    # Reward function variables
    price_df = None
    initial_cash = 0
    cash = 0
    stock = 0
    initial_portfolio_value = 0

    # State advancement variables
    state_df = None
    state = None
    actions = []
    num_states = 0
    state_index = 0

    # Learning model
    history_table = {}  # key: state_index, value: {key: state, value: Set(actions)}

    # Reward model
    asset_table = {}  # key: state_index, value: {key: state, value: (cash, stock, portfolio_value)}
    asset_cash_index = 0
    asset_stock_index = 1
    asset_portfolio_value_index = 2

    def __init__(self,
                 state_df: pd.DataFrame,
                 price_df: pd.DataFrame,
                 initial_cash: int=5,
                 alpha: float=.9,
                 gamma: float=.9,
                 p_explore: float=.1):
        # Assign parameter values
        self.state_df = state_df
        self.price_df = price_df
        self.initial_cash = initial_cash
        self.alpha = alpha
        self.gamma = gamma
        self.p_explore = p_explore

        self.initialize_state()
        self.asset_table[self.state_index] = {self.state_str(self.state): (self.initial_cash, 0, self.initial_cash)}

    def initialize_state(self):
        self.num_states = self.state_df.shape[0]
        self.state_index = 0
        self.cash = self.initial_cash
        self.stock = 0
        self.initial_portfolio_value = self.get_portfolio_value(self.state_index, self.cash, self.stock)
        self.state = self.state_df.iloc[self.state_index]
        self.state['hasCash'] = True
        self.state['hasStock'] = False
        self.actions = self.get_possible_actions(self.state)

    def train(self, iterations: int = 100, dyna_iterations: int = 500):
        for iteration in range(iterations):
            print(iteration)
            self.initialize_state()
            while self.next_state_exists():
                prev_state = self.state.copy()
                action, action_type = self.get_action()
                reward = self.go_to_next_state(action)
                self.update_q(prev_state, action, self.state, reward)

            # Dynamically set the number of dyna iterations
            # number_of_states * estimated_num_actions_per_state * 2
            dyna_iterations = len(self.q_table) * 2 * 2
            self.dyna_planning(dyna_iterations)
            #print(self.q_table)

    def update_q(self, state: pd.Series, action: str, next_state: pd.Series, reward: float):
        # Bellman Equation
        # q[s][a] = q[s][a] + alpha[r + g*max_a'(q[s'][a']) - q[s][a]]
        q = self.q_table[self.state_str(state)][action]
        self.q_table[self.state_str(state)][action] =\
            q + self.alpha * (reward + self.gamma * (self.get_max_q_value(next_state)) - q)

    def get_portfolio_value(self, state_index: int, cash: float, stock: float):
        return cash + stock * self.price_df.iloc[state_index]['close']

    def reward(self, prev_portfolio_value, current_portfolio_value):
        # Cumulative return based on portfolio value
        return (current_portfolio_value - prev_portfolio_value) / prev_portfolio_value

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

        next_state['hasCash'] = has_cash
        next_state['hasStock'] = has_stock

        return next_state

    def go_to_next_state(self, action: str):
        self.update_history_table(self.state_index, self.state, action)
        prev_portfolio_value = self.get_portfolio_value(self.state_index, self.cash, self.stock)

        self.cash, self.stock = self.apply_action_to_portfolio(self.state_index, action, self.cash, self.stock)

        # Advance to next state
        self.state = self.get_next_state(self.state, action)
        self.state_index += 1
        self.actions = self.get_possible_actions(self.state)
        current_portfolio_value = self.get_portfolio_value(self.state_index, self.cash, self.stock)

        # Calculate and return reward for entering this state
        reward = self.reward(prev_portfolio_value, current_portfolio_value)

        # Update asset table
        self.update_asset_table(self.state_index, self.state, self.cash, self.stock, current_portfolio_value)

        return reward

    def update_history_table(self, state_index: int, state: pd.Series, action: str):
        state_str = self.state_str(state)
        if state_index not in self.history_table:
            self.history_table[state_index][state_str] = {action}
        elif state_str not in self.history_table[state_index]:
            self.history_table[state_index][state_str] = {action}
        else:
            self.history_table[state_index][state_str].add(action)

    def get_possible_actions(self, state: pd.Series):
        actions = [self.HOLD]

        if state['hasCash']:
            actions.append(self.BUY)

        if state['hasStock']:
            actions.append(self.SELL)

        self.initialize_q_values(state, actions)

        return actions

    def get_action(self):
        action_type = 'exploit'
        action = self.get_exploitation_action(self.state)

        if random.uniform(0, 1) < self.p_explore:
            action_type = 'explore'
            action = self.get_exploration_action(action)

        return action, action_type

    def get_exploitation_action(self, state: pd.Series):
        action_values = self.q_table[self.state_str(state)]
        return max(action_values, key=action_values.get)

    def get_exploration_action(self, exploit_action: str):
        actions = self.actions.copy()
        actions.remove(exploit_action)
        return random.choice(actions)

    def initialize_q_values(self, state: pd.Series, actions: list):
        state_str = self.state_str(state)

        for action in actions:
            # Initialize with tiny value
            if state_str not in self.q_table:
                self.q_table[state_str] = {}
            if action not in self.q_table[state_str]:
                self.q_table[state_str][action] = random.uniform(0, 1) / 1000000000

    def get_max_q_value(self, state: pd.Series):
        action = self.get_exploitation_action(state)
        return self.q_table[self.state_str(state)][action]

    def update_asset_table(self, state_index: int, state: pd.Series, cash: float, stock: float, portfolio_value: float):
        state_str = self.state_str(state)
        if state_index in self.asset_table and state_str in self.asset_table[state_index]:
            current_value = self.asset_table[state_index][self.asset_portfolio_value_index]
            if portfolio_value > current_value:
                self.asset_table[state_index] = (cash, stock, portfolio_value)
        else:
            self.asset_table[state_index][state_str] = (cash, stock, portfolio_value)

    def state_str(self, state: pd.Series):
        return json.dumps(state.to_dict(), sort_keys=True)

    def str_to_state(self, state_str: str):
        return pd.Series(json.loads(state_str))

    def dyna_planning(self, iterations):
        print('\tDyna iterations: ', iterations)
        for i in range(iterations):
            # Get random state, but exclude final state (state of last index)
            state_index = random.choice(self.history_table.keys())
            state = random.choice(self.history_table[state_index].keys())
            state_str = self.state_str(state)
            action = random.choice(self.history_table[state_index][state_str].keys())

            reward = self.simulate_go_to_next_state(state_index, state, action)
            next_state = self.state_df[state_index + 1]

            self.update_q(state, action, next_state, reward)

    def simulate_go_to_next_state(self, state_index: int, state: pd.Series, action: str):
        state_str = self.state_str(state)

        # Get assets from the best case scenario for this state_index
        # and apply the simulated action to get assets for the next state
        cash, stock, portfolio_value = self.asset_table[state_index][state_str]
        next_cash, next_stock = self.apply_action_to_portfolio(state_index, action, cash, stock)

        # Calculate portfolio amount for next state and update asset table
        # if this is the new best case
        next_state_index = state_index + 1
        next_state = self.get_next_state(state, action)
        next_portfolio_value = self.get_portfolio_value(next_state_index, next_cash, next_stock)
        self.update_asset_table(next_state_index, next_state, next_cash, next_stock, next_portfolio_value)

        # Calculate reward for taking this simulated action
        reward = self.reward(portfolio_value, next_portfolio_value)

        return reward

    def apply_action_to_portfolio(self, state_index, action, cash, stock):
        # Apply action to portfolio
        stock_price = self.price_df.iloc[state_index]['close']
        if action == self.BUY:
            stock_to_buy = int(cash / stock_price)
            stock += stock_to_buy
            cash -= stock_to_buy * stock_price
        elif action == self.SELL:
            cash += stock * stock_price
            stock = 0
        else:  # HOLD
            pass  # Do Nothing

        return cash, stock

    def export_q_table(self, file_name: str):
        with open(file_name, 'w+') as f:
            f.write(json.dumps(self.q_table))

    def export_policy(self, file_name: str):
        policy = {}
        for state in self.q_table:
            policy[state] = max(self.q_table[state], key=self.q_table[state].get)

        with open(file_name, 'w+') as f:
            f.write(json.dumps(policy, sort_keys=True))

