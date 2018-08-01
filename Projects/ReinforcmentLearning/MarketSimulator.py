import pandas as pd
import json
import copy
import matplotlib.pyplot as plt
from Projects.ReinforcmentLearning.DynaQLearner import Action, Portfolio


class MarketSimulator:
    market_df = pd.DataFrame()
    price_df = pd.DataFrame()
    policy = {}
    initial_cash = 0
    initial_portfolio = None
    portfolio = None
    moves = {}
    state_index = 0

    def __init__(self,
                 market_df: pd.DataFrame,
                 price_df: pd.DataFrame,
                 policy: dict,
                 initial_cash: int = 5):
        self.market_df = market_df
        self.price_df = price_df
        self.policy = policy
        self.initial_cash = initial_cash
        # self.validate_data()
        self.initial_portfolio = Portfolio(self.initial_cash, 0, 0, self.price_df)
        self.portfolio = copy.deepcopy(self.initial_portfolio)

    def validate_data(self):
        cols = self.market_df.columns
        policy_df = pd.DataFrame(self.policy)  # Error here
        policy_cols = policy_df.columns

        if set(cols) != set(policy_cols):
            raise AssertionError("Market and Policy metadata differ. " +
                                 "Policy must be trained on a dataset with same metadata.")

    def run(self):
        for index, row in self.market_df.iterrows():
            # Initializing state
            state = copy.deepcopy(row)
            update_state_assets(state, self.portfolio)
            state_str = json.dumps(state.to_dict(), sort_keys=True)

            # Get action and adjust assets based on action
            try:
                action = self.policy[state_str]
                if action == Action.BUY or action == Action.SELL:
                    self.moves[index] = (self.state_index, action)
                    self.portfolio.apply_action(self.state_index, action, self.price_df)
            except IndexError:
                # Known IndexError occurs because portfolio.apply_action() increments state index
                if self.state_index == self.price_df.size - 1:
                    pass
                else:
                    raise IndexError('Unexpected IndexError')
            except KeyError:
                # If state not found, do nothing
                pass

            self.state_index += 1

        self.portfolio.calculate_portfolio_value(self.state_index - 1, self.price_df)
        print(self.results())

    def results(self):
        result_str = "Policy results:"
        result_str += "\n\tInitial Portfolio:\t" + str(self.initial_portfolio)
        result_str += "\n\tFinal Portfolio:\t" + str(self.portfolio)
        result_str += "\n\tStock performance: \t" + \
                      str(percentage_gain(self.price_df.iloc[0]['close'], self.price_df.iloc[-1]['close']))
        result_str += "\n\tPolicy performance: \t" + \
                      str(percentage_gain(self.initial_portfolio.value, self.portfolio.value))
        return result_str

    def plot_moves(self):
        ax = self.price_df.plot()
        color = 'b'
        for key, val in self.moves.items():
            state_index, action = val
            if action == Action.BUY:
                color = 'g'
            elif action == Action.SELL:
                color = 'r'
            ax.axvline(state_index, color=color)
        plt.show()
        plt.clf()


def update_state_assets(state: pd.Series, portfolio: Portfolio):
    if portfolio.stock == 0:
        state['hasCash'] = True
        state['hasStock'] = False
    else:
        state['hasCash'] = False
        state['hasStock'] = True


def percentage_gain(initial_value, final_value):
    return ((final_value - initial_value) / initial_value) * 100

