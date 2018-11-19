from decimal import Decimal
import pandas as pd
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.metrics import accuracy_score, roc_curve, auc, precision_score, recall_score, f1_score

# Personal libraries
from util import Stopwatch

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

def train_and_score_classifier(classifier, df: pd.DataFrame, labels: pd.DataFrame, pos_label: int, n_folds: int=5, shuffle: bool=True, sampler=None, print_results: bool=True, description: str='Results'):
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
    :param sampler: sampling object used to resample data prior to training
    :param stratified_k_fold: flag indicating to use stratified kfold which maintains the original ratio of classes with each fold
    :param print_results: flag determining whether or not results should be printed
    :param description: description of model being trained; will be displayed if results are printed
    :return: returns average values of classification accuracy, AUC, and F1 score
    """

    PRECISION = _get_min_significant_precision(df)

    if sampler:
        kf = StratifiedKFold(n_splits=n_folds, shuffle=shuffle)
        folds = kf.split(df,labels)
    else:
        kf = KFold(n_splits=n_folds, shuffle=shuffle)
        folds = kf.split(df)

    acc_scores = []
    auc_scores = []
    precision_scores = []
    recall_scores = []
    f1_scores = []
    time_to_train_and_predict = []
    for train, test in folds:
        # Begin timer
        Stopwatch.start()
        
        # If resampling, apply it to training data
        if sampler:
            train_x,train_y = sampler.fit_resample(df.iloc[train], labels.iloc[train])
            train_x = pd.DataFrame(train_x)
            train_y = pd.Series(train_y)
        else:
            train_x = df.iloc[train]
            train_y = labels.iloc[train]
        test_x = df.iloc[test]
        test_y = labels.iloc[test]
        
        # Train the Model
        classifier.fit(train_x, train_y)

        # Make predictions
        predictions = classifier.predict(test_x)
        
        # End timer
        Stopwatch.stop()
        time_to_train_and_predict.append(Stopwatch.get_time_elapsed())
        
        # Check raw accuracy
        acc_scores.append(accuracy_score(predictions, test_y))

        # Calculate AUC
        fpr, tpr, thresholds = roc_curve(test_y, predictions, pos_label=pos_label)
        auc_scores.append(auc(fpr, tpr))
        
        # Calculate Precision
        precision_scores.append(precision_score(test_y, predictions, pos_label=pos_label))
        
        # Calculate Recall
        recall_scores.append(recall_score(test_y, predictions, pos_label=pos_label))
        
        # Calculate F1 score
        f1_scores.append(f1_score(test_y, predictions, pos_label=pos_label))
        
    avg_acc = round(Decimal(sum(acc_scores) / len(acc_scores)), PRECISION)
    avg_auc = round(Decimal(sum(auc_scores) / len(auc_scores)), PRECISION)
    avg_precision = round(Decimal(sum(precision_scores) / len(precision_scores)), PRECISION)
    avg_recall = round(Decimal(sum(recall_scores) / len(recall_scores)), PRECISION)
    avg_f1 = round(Decimal(sum(f1_scores) / len(f1_scores)), PRECISION)
    avg_time = sum(time_to_train_and_predict)/len(time_to_train_and_predict)
    
    if print_results:
        horizontal_bar = '=' * (len(description)+4)
        description_line = '= ' + description + ' ='
        print(horizontal_bar)
        print(description_line)
        print(horizontal_bar)
        print('Accuracy:\t', avg_acc)
        print('AUC:\t\t', avg_auc)
        print('Precision:\t', avg_precision)
        print('Recall:\t\t', avg_recall)
        print('F1:\t\t', avg_f1)
        print('Average time to train: ', Stopwatch.get_formatted_time(avg_time))
        print('\n')
    
    metrics = {"accuracy": avg_acc,
               "auc": avg_auc,
               "precision": avg_precision,
               "recall": avg_recall,
               "f1": avg_f1,
               "average_training_time": avg_time}
    
    return classifier, metrics

def show_precision_recall_curve(classifier, x_test: pd.DataFrame, y_test: pd.DataFrame):
    """
    Displays precision-recall curve for a trained classifier and test dataset
    1. Use decision function or prediction probability estimate function to get the score
    2. Get average precision
    3. Get precision-recall curve and graph it
    
    :param classifier: Classifier to be evaluated
    :param x_test: Test dataset used to get prediction score
    :param y_test: Test labels used to generate precision-recall curve
    """
    
    # Get prediction probability estimate
    if hasattr(classifier,"predict_proba"):
        y_score = pd.DataFrame(classifier.predict_proba(x_test))[1]
    elif hasattr(classifier,"decision_function"):
        y_score = pd.DataFrame(classifier.decision_function(x_test))
    else:
        raise Exception("Classifier with unknown function for finding decision function/prediction probability estimates.")
    
    # Get precision-recall curve
    average_precision = average_precision_score(y_test, y_score)
    precision, recall, _ = precision_recall_curve(y_test, y_score)

    # Plot the precision-recall curve
    # In matplotlib < 1.5, plt.fill_between does not have a 'step' argument
    step_kwargs = ({'step': 'post'}
                   if 'step' in signature(plt.fill_between).parameters
                   else {})
    plt.step(recall, precision, color='b', alpha=0.2,
             where='post')
    plt.fill_between(recall, precision, alpha=0.2, color='b', **step_kwargs)

    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.ylim([0.0, 1.05])
    plt.xlim([0.0, 1.0])
    plt.title('2-class Precision-Recall curve: AP={0:0.2f}'.format(
              average_precision))
