__author__ = 'nastra'
#
# This script trains multinomial Naive Bayes on the tweet corpus
# to find two different results:
# - How well can we distinguis positive from negative tweets?
# - How well can we detect whether a tweet contains sentiment at all?
#

from utils import load_sanders_data
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import MultinomialNB
from sklearn.cross_validation import ShuffleSplit
from sklearn.metrics import precision_recall_curve, auc
from utils import plot_pr
import numpy as np


def create_ngram_model():
    tfidf_ngrams = TfidfVectorizer(ngram_range=(1, 3), analyzer="word", binary=False)
    clf = MultinomialNB()
    return Pipeline([('vect', tfidf_ngrams), ('clf', clf)])


def train_model(clf_factory, X, Y):
    # setting random state to get deterministic behavior
    cv = ShuffleSplit(n=len(X), n_iter=10, test_size=0.3, indices=True, random_state=0)

    train_errors = []
    test_errors = []

    scores = []
    precisions, recalls, thresholds = [], [], []
    precision_recall_scores = []

    for train_index, test_index in cv:
        X_train, y_train = X[train_index], Y[train_index]
        X_test, y_test = X[test_index], Y[test_index]

        clf = clf_factory
        clf.fit(X_train, y_train)

        train_score = clf.score(X_train, y_train)
        test_score = clf.score(X_test, y_test)

        train_errors.append(1 - train_score)
        test_errors.append(1 - test_score)

        scores.append(test_score)
        probability = clf.predict_proba(X_test)
        precision, recall, pr_thresholds = precision_recall_curve(y_test, probability[:, 1])

        precision_recall_scores.append(auc(recall, precision))
        precisions.append(precision)
        recalls.append(recall)
        thresholds.append(pr_thresholds)

    return scores, precision_recall_scores, precisions, recalls, thresholds, test_errors, train_errors


def print_and_plot_scores(scores, pr_scores, train_errrors, test_errors, name="NaiveBayes ngram"):
    scores_to_sort = pr_scores
    median = np.argsort(scores_to_sort)[len(scores_to_sort) / 2]

    plot_pr(pr_scores[median], name, "01", precisions[median],
            recalls[median], label=name)

    summary = (np.mean(scores), np.std(scores),
               np.mean(pr_scores), np.std(pr_scores))
    print("AVG Scores\tSTD Scores\tAVG PR Scores\tSTD PR Scores")
    print "%.3f\t\t%.3f\t\t%.3f\t\t\t%.3f\t" % summary

    return np.mean(train_errors), np.mean(test_errors)


if __name__ == "__main__":
    X_orig, Y_orig = load_sanders_data()
    unique_classes = np.unique(Y_orig)
    for c in unique_classes:
        print("#%s tweets: %i" % (c, sum(Y_orig == c)))

    pos_neg = np.logical_or(Y_orig == "positive", Y_orig == "negative")
    X = X_orig[pos_neg]
    Y = Y_orig[pos_neg]
    Y = Y == "positive"

    pipeline = create_ngram_model()

    scores, precision_recall_scores, precisions, recalls, thresholds, test_errors, train_errors = train_model(pipeline,
                                                                                                              X, Y)

    avg_train_err, avg_test_err = print_and_plot_scores(scores, precision_recall_scores, train_errors, test_errors)

    print("AVG Training Error: %.3f  -- AVG Testing Error: %.3f" % (avg_train_err, avg_test_err))


