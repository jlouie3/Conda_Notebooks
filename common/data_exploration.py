import os
import pandas as pd
import numpy as np
from functools import reduce


#############################
#    DATAFRAME FUNCTIONS    #
#############################
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
    Apply formatting
    '''
    def two_decimal_precision(x):
        return "%.2F" % x
    continuous_dqr.loc['nulls pct'] = continuous_dqr.loc['nulls pct'].apply(two_decimal_precision)
    categorical_dqr.loc['nulls pct'] = categorical_dqr.loc['nulls pct'].apply(two_decimal_precision)
    categorical_dqr.loc['mode pct'] = categorical_dqr.loc['mode pct'].apply(two_decimal_precision)
    categorical_dqr.loc['2nd mode pct'] = categorical_dqr.loc['2nd mode pct'].apply(two_decimal_precision)

    '''
    Reorder rows
    '''
    continuous_dqr = continuous_dqr.reindex([
        'count',
        'nulls',
        'nulls pct',
        'std',
        'min',
        '25%',
        '50%',
        'mean',
        '75%',
        'max',
        'cardinality'])

    categorical_dqr = categorical_dqr.reindex([
        'count',
        'nulls',
        'nulls pct',
        'mode',
        'mode count',
        'mode pct',
        '2nd mode',
        '2nd mode count',
        '2nd mode pct',
        'cardinality'])

    '''
    Identify columns that were not listed as continuous or categorical
    '''
    error_cols = list(set(df.columns).difference(set(continuous_cols + categorical_cols)))

    return continuous_dqr, categorical_dqr, error_cols


def move_label_column_to_front(df: pd.DataFrame, label_name: str):
    columns = list(df.columns)
    columns.insert(0, columns.pop(columns.index(label_name)))
    return df[columns]


def set_columns_to_category_dtype(df: pd.DataFrame, cols: list=None):
    """
    Sets specified columns in df to 'category' dtype. If no columns are passed in, function will attempt to change all
    columns of 'object' dtype to 'category' dtype

    :param df: pd.DataFrame whose columns will be modified
    :param cols: list of column names to change type
    :return: None
    """
    # if no columns are passed in, infer categorical columns
    if cols is None:
        cols_to_change = [col_name for col_name in df.dtypes.where(df.dtypes == 'object').dropna().index if col_name != df.index.name]
        for col in cols_to_change:
            df[col] = df[col].astype('category')
    else:
        for col in cols:
            df[col] = df[col].astype('category')


def get_numeric_data(df: pd.DataFrame, auto_fillna: bool=True):
    """
    Returns all continuous/numeric data in dataframe

    :param df: pd.DataFrame to get numeric data from
    :param auto_fillna: flag to autofill null values with 0
    # :return: pd.DataFrame of all continuous/numeric data
    """
    if auto_fillna:
        return df.select_dtypes(include=[np.number]).fillna(0)
    else:
        return df.select_dtypes(include=[np.number])


def get_categorical_data(df: pd.DataFrame, auto_fillna: bool=True):
    """
    Returns all categorical data in dataframe

    :param df: pd.DataFrame to get categorical data from
    :param auto_fillna: flag to autofill null values with 'N/A' string
    # :return: pd.DataFrame of all categorical data
    """
    if auto_fillna:
        return df.select_dtypes(include=['category']).fillna('N/A')
    else:
        return df.select_dtypes(include=['category'])


def get_numeric_column_names(df: pd.DataFrame):
    """
    Get names of all columns containing numeric data

    :param df: pd.DataFrame to analyze
    :return: list of columns names containing numeric data
    """
    return df.columns[[str(dt) not in ['object', 'category'] for dt in df.dtypes]]


def get_categorical_column_names(df: pd.DataFrame):
    """
    Get names of all columns containing categorical data

    :param df: pd.DataFrame to analyze
    :return: list of columns names categorical numeric data
    """
    return df.columns[[str(dt) in ['object', 'category'] for dt in df.dtypes]]


def enumerate_categorical_columns(df: pd.DataFrame, columns: list=None):
    """
    Enumerates categorical values in specified columns. If no columns are specified, then all columns
    of 'object' or 'categorical' dtypes will be enumerated.

    :param df: pd.DataFrame to modify
    :param columns: list of column names to enumerate
    :return: pd.DataFrame of all enumerated data
    """
    if columns is None:
        columns = get_categorical_column_names(df)

    enumerated_data = []
    for column in columns:
        enumerated_data.append(enumerate_series(df[column]))

    enumerated_df = reduce(lambda x, y: x.merge(y, left_index=True, right_index=True), enumerated_data)
    return enumerated_df


##########################
#    SERIES FUNCTIONS    #
##########################

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


def enumerate_series(s: pd.Series):
    """
    Maps values in a pd.Series object to an integer value. Mapping is saved to a local file.
    :param s: series to be mapped
    :return: series with integer-mapped values
    """
    list_of_unique_values = list(s.unique())
    file = open(os.path.join(os.getcwd(), s.name + '_mapping.txt'), 'w')
    for val in list_of_unique_values:
        file.write(str(val) + '\t' + str(list_of_unique_values.index(val)) + os.linesep)
    file.close()

    return pd.to_numeric(s.apply(lambda x: list_of_unique_values.index(x)))


