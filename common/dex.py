import pandas as pd
import numpy as np
from functools import reduce

def get_data_quality_report(df: pd.DataFrame):
    """
    Create data quality report for both continuous and categorical features

    :param df: dataframe to analyze
    :return: data quality report for continuous features, data quality report for categorical features
    :rtype: pd.Dataframe, pd.Dataframe
    """

    '''
    COMMON DQR CHARACTERISTICS
    '''
    # Total number of rows in dataset
    num_rows = df.shape[0]

    # Number of records as nulls
    nulls = df.isnull().sum()
    nulls.name = 'nulls'

    # Percent of records as nulls
    nulls_pct = nulls / num_rows
    nulls_pct.name = 'nulls pct'

    # Number of unique values in each column
    cardinality = df.nunique()
    cardinality.name = 'cardinality'

    '''
    CREATE DQR FOR NUMERIC/CONTINUOUS FEATURES
    '''
    # Baseline describe function (filters out non-numeric fields)
    continuous_dqr = df.describe()
    continuous_cols = list(continuous_dqr.columns)

    # Modify or add supplemental rows
    continuous_dqr.loc['count'] = num_rows
    continuous_dqr = continuous_dqr.append(nulls[continuous_cols])
    continuous_dqr = continuous_dqr.append(nulls_pct[continuous_cols])
    continuous_dqr = continuous_dqr.append(cardinality[continuous_cols])

    '''
    CREATE DQR FOR CATEGORICAL FEATURES
    '''
    categorical_cols = [col_name for col_name in df.dtypes.where(df.dtypes == 'category').dropna().index if col_name != df.index.name]
    categorical_df = df[categorical_cols]

    # Calculate mode data for each column and aggregate results into single dataframe
    categorical_mode_list = []
    for col in categorical_df:
        categorical_mode_list.append(get_mode_and_second_mode(categorical_df[col]))
    categorical_mode = reduce(lambda x, y: x.merge(y, left_index=True, right_index=True), categorical_mode_list)

    # Aggregate all categorical data quality rows
    categorical_dqr = pd.DataFrame()
    categorical_dqr = categorical_dqr.append(pd.Series([num_rows for col in categorical_df.columns], name='count', index=categorical_df.columns))
    categorical_dqr = categorical_dqr.append(categorical_mode)
    categorical_dqr = categorical_dqr.append(nulls[categorical_cols])
    categorical_dqr = categorical_dqr.append(nulls_pct[categorical_cols])
    categorical_dqr = categorical_dqr.append(cardinality[categorical_cols])

    '''
    Identify columns that were not listed as continuous or categorical
    '''
    error_cols = list(set(df.columns).difference(set(continuous_cols + categorical_cols)))

    return continuous_dqr, categorical_dqr, error_cols


def get_mode_and_second_mode(s: pd.Series):
    """
    Returns mode, second mode if available, and counts/percentage for both
    :param s: pd.Series to analyze
    :return: pd.DataFrame containing mode and 2nd mode information
    """
    counts = s.value_counts()
    mode_col = counts.index[0]
    mode_counts = counts.iloc[0]
    mode_pct = mode_counts / s.size

    if counts.index.size < 2:
        second_mode_col = np.NaN
        second_mode_counts = np.NaN
        second_mode_pct = np.NaN
    else:
        second_mode_col = counts.index[1]
        second_mode_counts = counts.iloc[1]
        second_mode_pct = second_mode_counts / s.size
    mode_df = pd.DataFrame(
        {
            s.name: [mode_col, mode_counts, mode_pct, second_mode_col, second_mode_counts, second_mode_pct]
        },
        index=['mode', 'mode count', 'mode pct', '2nd mode', '2nd mode count', '2nd mode pct']
    )

    return mode_df


def set_columns_to_category_dtype(df: pd.DataFrame, cols=None):
    # if no columns are passed in, infer categorical columns
    if cols is None:
        cols_to_change = [col_name for col_name in df.dtypes.where(df.dtypes == 'object').dropna().index if col_name != df.index.name]
        for col in cols_to_change:
            df[col] = df[col].astype('category')
    else:
        for col in cols:
            df[col] = df[col].astype('category')
