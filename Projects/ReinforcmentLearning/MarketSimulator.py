import pandas as pd
from Projects.ReinforcmentLearning.DynaQLearner import Action, Portfolio

class MarketSimulator:
    market_df = pd.DataFrame()
    price_df = pd.DataFrame()
    policy = {}
    initial_cash = 0
    portfolio = None
    moves = {}

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

    def validate_data(self):
        cols = self.market_df.columns
        policy_df = pd.DataFrame(self.policy)
        policy_cols = policy_df.columns

        if set(cols) != set(policy_cols):
            raise AssertionError("Market and Policy metadata differ. " +
                                 "Policy must be trained on a dataset with same metadata.")

    def run(self):
        for index, row in self.market_df.iloc[20:25].iterrows():
            print(row.to_dict())
        pass

