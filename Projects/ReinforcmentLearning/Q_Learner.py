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
    alpha = .1
    gamma = .9
    p_explore = .1
    q_table = {}    # state_str: {action: q-value}

    # Reward function variables
    reward_df = None
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

    def __init__(self,
                 state_df: pd.DataFrame,
                 reward_df: pd.DataFrame,
                 initial_cash: int=5,
                 alpha: float=.9,
                 gamma: float=.9,
                 p_explore: float=.1):
        # Assign parameter values
        self.state_df = state_df
        self.reward_df = reward_df
        self.initial_cash = initial_cash
        self.alpha = alpha
        self.gamma = gamma
        self.p_explore = p_explore

        self.initialize_state()

    def initialize_state(self):
        self.num_states = self.state_df.shape[0]
        self.state_index = 0
        self.cash = self.initial_cash
        self.stock = 0
        self.initial_portfolio_value = self.get_portfolio_value()
        self.state = self.state_df.iloc[self.state_index]
        self.state['hasCash'] = True
        self.state['hasStock'] = False
        self.actions = self.get_possible_actions(self.state)

    def train(self, iterations: int = 100, dyna_iterations: int = 500):
        for iteration in range(iterations):
            self.initialize_state()
            while self.next_state_exists():
                prev_state = self.state.copy()
                action, action_type = self.get_action()
                reward = self.go_to_next_state(action)
                self.update_q(prev_state, action, self.state, reward)

                self.dyna_planning(dyna_iterations)
            print(self.q_table)

    def update_q(self, state: pd.Series, action: str, next_state: pd.Series, reward: float):
        # Bellman Equation
        # q[s][a] = q[s][a] + alpha[r + g*max_a'(q[s'][a']) - q[s][a]]
        q = self.q_table[self.state_str(state)][action]
        self.q_table[self.state_str(state)][action] =\
            q + self.alpha * (reward + self.gamma * (self.get_max_q_value(next_state)) - q)

    def get_portfolio_value(self):
        return self.cash + self.stock * self.reward_df.iloc[self.state_index]['close']

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
        prev_portfolio_value = self.get_portfolio_value()

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
        current_portfolio_value = self.get_portfolio_value()

        # Calculate and return reward for entering this state
        reward = self.reward(prev_portfolio_value, current_portfolio_value)
        return reward

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

    def state_str(self, state: pd.Series):
        return json.dumps(state.to_dict(), sort_keys=True)

    def dyna_planning(self, steps):
        for i in range(steps):
            states_visited = self.q_table.keys()
            state = random.choice(states_visited)

            actions_taken = self.q_table[state].keys()
            action = random.choice(actions_taken)

            next_state, reward = self.go_to_next_state(action)
            self.update_q(state, action, next_state, reward)

    def export_q_table(self):
        with open('q_table.txt') as f:
            f.write(json.dumps(self.q_table))

    def export_policy(self):
        policy = {}
        for state in self.q_table:
            policy[state] = max(self.q_table[state], keys=self.q_table[state].get)

        with open('policy.txt') as f:
            f.write(json.dumps(policy))
