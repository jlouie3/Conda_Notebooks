import pandas as pd
from sklearn.model_selection import KFold
from sklearn.metrics import accuracy_score, roc_curve, auc

# Modeling libraries
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC


def train_and_score_classifier(classifier, df: pd.DataFrame, labels: pd.DataFrame, pos_label: int, n_folds: int=5, shuffle: bool=True):
    """
    Trains and scores a binary classification problem using the machine learning model that was passed in.
    Trains using kfolds data selection. Each fold creates a train/test dataset which is the evaluated using
    accuary and AUC metrics. Accuracy and AUC are averaged across the kfolds before being returned.

    :param classifier: instantiated classifier object to train and score
    :param df: data used to train and score the classifier
    :param labels: labels corresponding to the training data (must be a dataframe of integers
    :param pos_label: label value considered 'positive' (used for scoring)
    :param n_folds: number of folds to use when splitting the input data into test/train groups
    :param shuffle: flag indicating to randomly split data during kfolds
    :return: returns average values of classification accuracy and AUC
    """

    kf = KFold(n_splits=n_folds, shuffle=shuffle)

    acc_scores = []
    auc_scores = []
    for train, test in kf.split(df):
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
    avg_acc = sum(acc_scores) / len(acc_scores)
    avg_auc = sum(auc_scores) / len(auc_scores)

    return avg_acc, avg_auc
