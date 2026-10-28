"""All learned preprocessing is fitted inside each training fold."""
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from .config import NUMERIC_FEATURES, CATEGORICAL_FEATURES, RANDOM_SEED


def build_preprocessor():
    numbers = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    categories = Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                           ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False))])
    return ColumnTransformer([("numeric", numbers, NUMERIC_FEATURES),
                              ("category", categories, CATEGORICAL_FEATURES)])


def candidates():
    return {
        "decision_tree": (DecisionTreeClassifier(random_state=RANDOM_SEED),
                          {"classifier__max_depth": [3, 6, None], "classifier__min_samples_leaf": [1, 5]}),
        "random_forest": (RandomForestClassifier(n_estimators=200, random_state=RANDOM_SEED, n_jobs=1),
                          {"classifier__max_depth": [6, None], "classifier__min_samples_leaf": [1, 3]}),
        "logistic_regression": (LogisticRegression(max_iter=4000, random_state=RANDOM_SEED),
                                {"classifier__C": [0.1, 1.0, 10.0]}),
    }


def make_pipeline(classifier):
    return Pipeline([("preprocess", build_preprocessor()), ("classifier", classifier)])
