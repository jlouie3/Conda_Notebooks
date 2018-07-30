import pandas as pd
import json
import copy
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
        self.validate_data()
        self.initial_portfolio = Portfolio(self.initial_cash, 0, 0, self.price_df)
        self.portfolio = copy.deepcopy(self.initial_portfolio)

    def validate_data(self):
        cols = self.market_df.columns
        policy_df = pd.DataFrame(self.policy)
        policy_cols = policy_df.columns

        if set(cols) != set(policy_cols):
            raise AssertionError("Market and Policy metadata differ. " +
                                 "Policy must be trained on a dataset with same metadata.")

    def run(self):
        for index, row in self.market_df.iterrows():
            state_str = json.dumps(row.to_dict(), sort_keys=True)

            try:
                action = self.policy[state_str]
                self.moves[index] = action
                self.portfolio.apply_action(self.state_index, action, self.price_df)
            except KeyError:
                # If state not found, do nothing
                pass

            self.state_index += 1

    def results(self):
        result_str = "Policy results:"
        result_str += "\n\tInitial Portfolio:\t" + str(self.initial_portfolio)
        result_str += "\n\tFinal Portfolio:\t" + str(self.portfolio)
        result_str += "\n\tStock performance: \t" + \
                      str(percentage_gain(self.price_df[0], self.price_df[-1]))
        result_str += "\n\tPolicy performance: \t" + \
                      str(percentage_gain(self.initial_portfolio.value, self.portfolio.value))


def percentage_gain(initial_value, final_value):
    return ((final_value - initial_value) / initial_value) * 100

