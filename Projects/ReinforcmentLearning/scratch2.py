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
    # Learning variables
    p_explore = .1
    q_table = QTable()

    # Reward function variables
    price_df = pd.DataFrame()
    portfolio = None
    initial_cash = 0

    # State advancement variables
    state_df = pd.DataFrame()
    state = None
    num_states = 0

    # Learning model
    history_table = HistoryTable()

    # Reward model
    asset_table = AssetTable()

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
        self.p_explore = p_explore

        self.q_table.alpha = alpha
        self.q_table.gamma = gamma

        self.initialize_state()
        self.asset_table.add_or_update(self.state, self.portfolio)

    def initialize_state(self):
        self.num_states = self.state_df.shape[0]

        # Initial state conditions
        state_index = 0
        state_data = self.state_df.iloc[state_index]
        has_cash = True
        has_stock = False
        self.state = State(state_index, state_data, has_cash, has_stock, self.q_table)

        # Initial portfolio
        self.portfolio = Portfolio(self.initial_cash, 0, self.state, self.price_df)

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
            # print(self.q_table)

    def get_action(self):
        action_type = 'exploit'
        action = self.get_exploitation_action()

        if random.uniform(0, 1) < self.p_explore:
            action_type = 'explore'
            action = self.get_exploration_action(action)

        return action, action_type

    def get_exploitation_action(self):
        action_values = self.q_table.table[self.state.state_str]
        return max(action_values, key=action_values.get)

    def get_exploration_action(self, exploit_action: str):
        actions = self.state.actions.copy()
        actions.remove(exploit_action)
        return random.choice(actions)

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
        return self.state.state_index < self.num_states - 1

    def get_next_state(self, state_index: int, state: pd.Series, action: str):
        next_state = self.state_df.iloc[state_index+1]

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
        # Log state/action pair as state is being left
        self.history_table.add(self.state, action)

        prev_portfolio_value = self.portfolio.value
        self.apply_action_to_portfolio(action)

        # CONTINUE HERE

        # Advance to next state
        self.state = self.get_next_state(self.state_index, self.state, action)
        self.state_index += 1
        self.actions = self.get_possible_actions(self.state)
        current_portfolio_value = self.get_portfolio_value(self.state_index, self.cash, self.stock)

        # Calculate and return reward for entering this state
        reward = self.reward(prev_portfolio_value, current_portfolio_value)

        # Update asset table
        self.update_asset_table(self.state_index, self.state, self.cash, self.stock, current_portfolio_value)

        return reward

    def state_str(self, state: pd.Series):
        return json.dumps(state.to_dict(), sort_keys=True)

    def str_to_state(self, state_str: str):
        return pd.Series(json.loads(state_str))

    def dyna_planning(self, iterations):
        print('\tDyna iterations: ', iterations)
        for i in range(iterations):
            # Get random state, but exclude final state (state of last index)
            state_index = random.choice(list(self.history_table.keys()))
            state_str = random.choice(list(self.history_table[state_index].keys()))
            state = self.str_to_state(state_str)
            action = random.choice(list(self.history_table[state_index][state_str]))

            next_state, reward = self.simulate_go_to_next_state(state_index, state, state_str, action)

            self.update_q(state, action, next_state, reward)

    def simulate_go_to_next_state(self, state_index: int, state: pd.Series, state_str: str, action: str):
        # Get assets from the best case scenario for this state_index
        # and apply the simulated action to get assets for the next state
        cash, stock, portfolio_value = self.asset_table[state_index][state_str]
        next_cash, next_stock = self.apply_action_to_portfolio(state_index, action, cash, stock)

        # Calculate portfolio amount for next state and update asset table
        # if this is the new best case
        next_state_index = state_index + 1
        next_state = self.get_next_state(state_index, state, action)
        next_portfolio_value = self.get_portfolio_value(next_state_index, next_cash, next_stock)
        self.update_asset_table(next_state_index, next_state, next_cash, next_stock, next_portfolio_value)

        # Calculate reward for taking this simulated action
        reward = self.reward(portfolio_value, next_portfolio_value)

        return next_state, reward

    def apply_action_to_portfolio(self, action):
        # Apply action to portfolio
        stock_price = self.price_df.iloc[self.state.state_index]['close']
        if action == Action.BUY:
            stock_to_buy = int(self.portfolio.cash / stock_price)
            self.portfolio.stock += stock_to_buy
            self.portfolio.cash -= stock_to_buy * stock_price
        elif action == Action.SELL:
            self.portfolio.cash += self.portfolio.stock * stock_price
            self.portfolio.stock = 0
        else:  # HOLD
            pass  # Do Nothing


    def export_q_table(self, file_name: str):
        with open(file_name, 'w+') as f:
            f.write(json.dumps(self.q_table))

    def export_policy(self, file_name: str):
        policy = {}
        for state in self.q_table:
            policy[state] = max(self.q_table[state], key=self.q_table[state].get)

        with open(file_name, 'w+') as f:
            f.write(json.dumps(policy, sort_keys=True))


class Action:
    BUY = 'buy'
    SELL = 'sell'
    HOLD = 'hold'


class State:
    state_index = None
    state_str = None
    data = pd.Series()
    actions = []
    portfolio = None

    def __init__(self, state_index: int, data: pd.Series, has_cash: bool, has_stock: bool, q_table: QTable):
        self.state_index = state_index
        self.data = data
        self.data['hasCash'] = has_cash
        self.data['hasStock'] = has_stock
        self.get_state_string()
        self.get_valid_actions()
        q_table.initialize_values_for_state(self)

    def get_state_string(self):
        return json.dumps(self.data.to_dict(), sort_keys=True)

    def get_valid_actions(self):
        actions = [Action.HOLD]

        if self.data['hasCash']:
            actions.append(Action.BUY)

        if self.data['hasStock']:
            actions.append(Action.SELL)

        return actions


class Portfolio:
    cash = 0
    stock = 0
    value = 0

    def __init__(self, cash, stock, state: State, price_df: pd.DataFrame):
        self.cash = cash
        self.stock = stock
        self.calculate_portfolio_value(state, price_df)

    def calculate_portfolio_value(self, state: State, price_df: pd.DataFrame):
        price = price_df.iloc[state.state_index]
        self.value = self.cash + self.stock * price


class HistoryTable:
    table = {}  # key: state_index, value: {key: state_str, value: {actions}}

    def __init__(self):
        pass

    def add(self, state: State, action: str):
        if state.state_index not in self.table:
            self.table[state.state_index] = {state.state_str: {action}}
        elif state.state_str not in self.table[state.state_index]:
            self.table[state.state_index][state.state_str] = {action}
        else:
            self.table[state.state_index][state.state_str].add(action)

    def get_random_state_action(self):
        state_index = random.choice(list(self.table.keys()))
        state_str = random.choice(list(self.table[state_index].keys()))
        action = random.choice(list(self.table[state_index][state_str]))
        return state_index, state_str, action


class AssetTable:
    table = {}  # key: state_index, value: {key: state, value: (cash, stock, portfolio_value)}

    def __init__(self):
        pass

    def add_or_update(self, state: State, portfolio: Portfolio):
        if state.state_index not in self.table:
            self.table[state.state_index] = {state.state_str: portfolio}
        else:
            if state.state_str not in self.table[state.state_index]:
                self.table[state.state_index] = {state.state_str: portfolio}
            else:
                current_value = self.table[state.state_index][state.state_str].value
                if portfolio.value > current_value:
                    self.table[state.state_index][state.state_str] = portfolio


class QTable:
    table = {}  # key: state_str, value: {key: action, value: q-value}
    alpha = .1
    gamma = .9

    def __init__(self, alpha: float, gamma: float):
        self.alpha = alpha
        self.gamma = gamma

    def initialize_values_for_state(self, state: State):
        for action in state.actions:
            # Initialize with tiny value
            if state.state_str not in self.table:
                self.table[state.state_str] = {}
            if action not in self.table[state.state_str]:
                self.table[state.state_str][action] = random.uniform(0, 1) / 1000000000

    def update(self, state: State, action: str, next_state: State, reward: float):
        # Bellman Equation
        # q[s][a] = q[s][a] + alpha[r + g*max_a'(q[s'][a']) - q[s][a]]
        q = self.table[state.state_str][action]
        self.table[state.state_str][action] = \
            q + self.alpha * (reward + self.gamma * (self.get_max_q(next_state)) - q)

    def get_max_q(self, state: State):
        return max(list(self.table[state.state_str].values()))
