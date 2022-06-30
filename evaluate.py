#!/usr/bin/env python3
# MAP score code extended from https://gist.github.com/bwhite/3726239
# and https://github.com/leopoldwalden/DeepPavlov_jilei/blob/deb6c37028f6a2cd6967c1eb676a493bade698da/deeppavlov/metrics/recall_at_k.py

import json
import logging
import warnings
from collections import OrderedDict
from typing import Dict, List, Iterable

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.DEBUG)


def process_gold_premises(path: str)-> Dict[str, List[str]]:
    gold_premises = {}

    with open(path, "rb") as f:
        gold_premises_file = json.load(f)

    for statement_id in gold_premises_file:
        gold_premises[statement_id] = list(gold_premises_file[statement_id]["premises"])

    return gold_premises


def process_predictions(
    filepath_or_buffer: str, sep: str = "\t"
) -> Dict[str, List[str]]:
    df = pd.read_csv(
        filepath_or_buffer, sep=sep, names=("statement", "premise"), dtype=str
    )

    if any(df[field].isnull().all() for field in df.columns):
        raise ValueError(
            "invalid format of the prediction dataset, possibly the wrong separator"
        )

    pred: Dict[str, List[str]] = OrderedDict()

    for id, df_premises in df.groupby("statement"):
        pred[id] = list(
            OrderedDict.fromkeys(df_premises["premise"].str.lower())
        )

    return pred


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True)
    parser.add_argument("pred", type=argparse.FileType("r", encoding="UTF-8"))
    parser.add_argument('-n','--nearest', type=int, default=500)
    args = parser.parse_args()

    preds = process_predictions(args.pred)
    gold_premises = process_gold_premises(args.gold)
    map_score = compute_mean_average_precision(gold_premises, preds, args.nearest)
    print(f"Mean Average Precision@{args.nearest} : {map_score}")

def precision_at_k(r, k):
    """Score is precision @ k
    Relevance is binary (nonzero is relevant).
    >>> r = [0, 0, 1]
    >>> precision_at_k(r, 1)
    0.0
    >>> precision_at_k(r, 2)
    0.0
    >>> precision_at_k(r, 3)
    0.33333333333333331
    >>> precision_at_k(r, 4)
    Traceback (most recent call last):
        File "<stdin>", line 1, in ?
    ValueError: Relevance score length < k
    Args:
        r: Relevance scores (list or numpy) in rank order
            (first element is the first item)
    Returns:
        Precision @ k
    Raises:
        ValueError: len(r) must be >= k
    """
    assert k >= 1
    r = np.asarray(r)[:k] != 0
    if r.size != k:
        raise ValueError('Relevance score length < k')
    return np.mean(r)

def average_precision(r):
    """Score is average precision (area under PR curve)
    Relevance is binary (nonzero is relevant).
    >>> r = [1, 1, 0, 1, 0, 1, 0, 0, 0, 1]
    >>> delta_r = 1. / sum(r)
    >>> sum([sum(r[:x + 1]) / (x + 1.) * delta_r for x, y in enumerate(r) if y])
    0.7833333333333333
    >>> average_precision(r)
    0.78333333333333333
    Args:
        r: Relevance scores (list or numpy) in rank order
            (first element is the first item)
    Returns:
        Average precision
    """
    r = np.asarray(r) != 0
    out = [precision_at_k(r, k + 1) for k in range(r.size) if r[k]]
    if not out:
        return 0.
    return np.mean(out)


def mean_average_precision(rs):
    """Score is mean average precision
    Relevance is binary (nonzero is relevant).
    >>> rs = [[1, 1, 0, 1, 0, 1, 0, 0, 0, 1]]
    >>> mean_average_precision(rs)
    0.78333333333333333
    >>> rs = [[1, 1, 0, 1, 0, 1, 0, 0, 0, 1], [0]]
    >>> mean_average_precision(rs)
    0.39166666666666666
    Args:
        rs: Iterator of relevance scores (list or numpy) in rank order
            (first element is the first item)
    Returns:
        Mean average precision
    """
    return np.mean([average_precision(r) for r in rs])

def compute_mean_average_precision(gold_results, predicted_results, k):
    relevance_results = list()
    test_cases = gold_results.keys()
    for prediction_id in test_cases:
        if len(predicted_results[prediction_id]) < k:
            raise ValueError(
                f"invalid format of the prediction file, the systems have to retrieve at least {k} premises for each statement"
            )
        relevance_list = list()
        if not prediction_id in predicted_results:
            relevance_list.append(0)
            relevance_results.append(relevance_list)
            continue
        num_predictions = 0
        for p in predicted_results[prediction_id]:
            if int(p) in gold_results[prediction_id]:
                relevance_list.append(1)
            else:
                relevance_list.append(0)
            num_predictions += 1
            if num_predictions >= k:
                break
        relevance_results.append(relevance_list)
    
    return mean_average_precision(relevance_results)


if __name__ == "__main__":
    main()
