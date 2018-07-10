# Scratch pad for prototyping code


'''
NOTES:
    Need to look for dataset splitting tools
    Tune hyperparameters
'''
import sklearn.tree as tree
import sklearn.naive_bayes as nb
import sklearn.svm as svm
import sklearn.model_selection as ms

tree_classifier = tree.DecisionTreeClassifier()
tree_classifier.fit()
tree_classifier.predict()

nb_classifier = nb.GaussianNB()
nb_classifier.fit()
nb_classifier.predict()

svm_classifier = svm.LinearSVC()
svm_classifier.fit()
svm_classifier.predict()

