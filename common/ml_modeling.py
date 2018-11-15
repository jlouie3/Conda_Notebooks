from decimal import Decimal
import pandas as pd
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.metrics import accuracy_score, roc_curve, auc, f1_score

# Modeling libraries
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC


def _get_min_significant_precision(df: pd.DataFrame):
    """
    Gets minimum decimal precision required to represent the minimum significance of a record in a dataframe. This
     is intended to be used within the realm of evaluating machine learning algorithms.

     Ex: DataFrame has 115 records. Significance of 1 record is 1/115 = 0.00869565. Therefore min precision required to
     capture this would be 4 decimal places (2 spots after the leading zeros)

    :param df: pd.DataFrame containing the data
    :return: Minimum number of decimal places required to represent the smallest piece of data in the dataset
    """

    # Count number of rows
    num_rows = df.shape[0]
    # Get significance of single row, save as string
    row_significance_string = str(1.0 / num_rows)
    # Parse string and count number of leading, significant zeros
    start_index = row_significance_string.index('.') + 1
    num_zeros = 0
    for char in row_significance_string[start_index:]:
        if char == '0':
            num_zeros += 1
        else:
            break
    # Final min precision is number of leading zeros + 2 places of significance
    precision = num_zeros + 2

    return precision

def train_and_score_classifier(classifier, df: pd.DataFrame, labels: pd.DataFrame, pos_label: int, n_folds: int=5, shuffle: bool=True, stratified_k_fold=False):
    """
    Trains and scores a binary classification problem using the machine learning model that was passed in.
    Trains using kfolds data selection. Each fold creates a train/test dataset which is the evaluated using
    accuary, AUC, and F1 score metrics. All metrics are averaged across the kfolds before being returned.

    :param classifier: instantiated classifier object to train and score
    :param df: data used to train and score the classifier
    :param labels: labels corresponding to the training data (must be a dataframe of integers
    :param pos_label: label value considered 'positive' (used for scoring)
    :param n_folds: number of folds to use when splitting the input data into test/train groups
    :param shuffle: flag indicating to randomly split data during kfolds
    :param stratified_k_fold: flag indicating to use stratified kfold which maintains the original ratio of classes with each fold
    :return: returns average values of classification accuracy, AUC, and F1 score
    """

    PRECISION = _get_min_significant_precision(df)

    if stratified_k_fold:
        kf = StratifiedKFold(n_splits=n_folds, shuffle=shuffle)
        folds = kf.split(df,labels)
    else:
        kf = KFold(n_splits=n_folds, shuffle=shuffle)
        folds = kf.split(df)

    acc_scores = []
    auc_scores = []
    f1_scores = []
    for train, test in folds:
        train_x = df.iloc[train]
        train_y = labels.iloc[train]
        test_x = df.iloc[test]
        test_y = labels.iloc[test]

        # Train the Model
        classifier.fit(train_x, train_y)

        # Make predictions
        predictions = classifier.predict(test_x)

        # Check raw accuracy
        acc_scores.append(accuracy_score(predictions, test_y))

        # Calculate AUC
        fpr, tpr, thresholds = roc_curve(test_y, predictions, pos_label=pos_label)
        auc_scores.append(auc(fpr, tpr))

        # Calculate F1 score
        f1_scores.append(f1_score(test_y, predictions, pos_label=pos_label))
    avg_acc = round(Decimal(sum(acc_scores) / len(acc_scores)), PRECISION)
    avg_auc = round(Decimal(sum(auc_scores) / len(auc_scores)), PRECISION)
    avg_f1 = round(Decimal(sum(f1_scores) / len(f1_scores)), PRECISION)

    return avg_acc, avg_auc, avg_f1





