import os
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

def normalize(df: pd.DataFrame, cols: list=None):
    """
    Normalizes specified dataframe columns using the MinMaxScaler
    
    :param df: pd.DataFrame containing data to be scaled
    :param cols: list of columns to be scaled
    :return: pd.DataFrame containing normalized data
    """
    if cols is None:
        features_to_normalize = df.columns
    else:
        features_to_normalize = cols
    
    scaler = MinMaxScaler()
    return pd.DataFrame(scaler.fit_transform(df[features_to_normalize]), columns=features_to_normalize)