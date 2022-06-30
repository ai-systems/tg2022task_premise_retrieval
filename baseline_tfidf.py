#!/usr/bin/env python3

import os
import json
import warnings
from typing import List, Tuple, Iterable

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_distances
import json

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable: Iterable, **kwargs) -> Iterable:
        return iterable


def read_premises_kb(path: str) -> List[Tuple[str, str]]:
    premises_kb = []

    with open(path, "rb") as f:
        kb_file = json.load(f)

    for premise_id in kb_file:
        premise_text = kb_file[premise_id]
        premises_kb.append((premise_id, premise_text))

    return premises_kb


def read_test_statements(path: str)-> List[Tuple[str,str]]:
    statements_list = []

    with open(path, "rb") as f:
        statements_file = json.load(f)

    for statement_id in statements_file:
        statement_text = statements_file[statement_id]["text"]
        statements_list.append((statement_id, statement_text))

    return statements_list


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--nearest', type=int, default=500)
    parser.add_argument('kb')
    parser.add_argument('statements')
    args = parser.parse_args()

    premises_kb = read_premises_kb(args.kb)    

    statements_list = read_test_statements(args.statements)

    df_p = pd.DataFrame(premises_kb, columns=('pid', 'premise'))
    df_s = pd.DataFrame(statements_list, columns=('sid', 'statement'))

    vectorizer = TfidfVectorizer().fit(list(df_p['premise']))
    X_s = vectorizer.transform(list(df_s['statement']))
    X_p = vectorizer.transform(list(df_p['premise']))
    X_dist = cosine_distances(X_s, X_p)

    for i_statement, distances in tqdm(enumerate(X_dist), desc=args.statements, total=X_s.shape[0]):
        for i_premise in np.argsort(distances)[:args.nearest]:
            print('{}\t{}'.format(df_s.loc[i_statement]['sid'], df_p.loc[i_premise]['pid']))


if '__main__' == __name__:
    main()
