import os
import pandas as pd
import matplotlib.pyplot as plt


def plot_selected(df, columns, start_index, end_index):
    data_to_plot = df.ix[start_index:end_index, columns]
    plot_data(data_to_plot, title='Selected Data')


'''Return CSV file path given ticker symbol'''
def symbol_to_path(symbol, base_dir='data'):
    return os.path.join(base_dir, "{}.csv".format(str(symbol)))


''' Read stock data from given file'''
def get_data(filePath, dates):
    df = pd.DataFrame(index=dates)

    df_temp = pd.read_csv(filePath, index_col='Date',
                          parse_dates=True,
                          na_values=['nan'])

    df = df.join(df_temp)  # use default how='left'
    fill_missing_values(df)
    return df


def normalize_data(df):
    return df / df.ix[0, :]


def plot_data(df, title='Stock Prices'):
    ax = df.plot(title=title, fontsize=8)
    ax.set_xlabel('Date')
    ax.set_ylabel('Price')
    plt.show()


def fill_missing_values(df_data):
    """Fill missing values in data frame, in place."""
    df_data.fillna(method='ffill', inplace='TRUE')
    #df_data.fillna(method='bfill', inplace='TRUE')


def compute_daily_returns(df):
    # using pandas
    daily_returns = (df / df.shift(1)) - 1
    daily_returns.ix[0, :] = 0  # set daily returns for row 0 to 0
    return daily_returns

'''
def test_run():
    # Define a date range
    dates = pd.date_range('2010-01-01', '2010-12-31')
    symbols = ['GOOG', 'IBM', 'GLD']

    df = get_data(symbols, dates)
    #print df

    # Slice by row range (dates) using DataFrame.ix[] selector
    #print df.ix['2010-01-01':'2010-01-31']

    # Slice by column (symbols)
    #print df['GOOG']            # single label selects a single column
    #print df[['IBM', 'GLD']]    # a list of labels selects multiple columns


    # Slice by row and column
    print(df.ix['2010-03-10':'2010-03-15', ['SPY', 'IBM']])

    #plot_data(df)
    #plot_selected(df, symbols, '2010-03-10', '2010-8-15')
    plot_data(normalize_data(df))

test_run()

'''