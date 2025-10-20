"""
Module name: process_data_1.py
Role: This module contains functions to process data.
Author: Guan Wang
Date: 08-02-2025
"""

def clean_data(data):
    """
    Clean data
    :param data: list of data
    :return: list of cleaned data
    >>> clean_data([1, '  hello  ', 3.14, 'world'])
    ['hello', 'WORLD']
    """
    # step 1: Clean data
    cleaned_data = []
    for item in data:
        if isinstance(item, str):
            item = item.strip()
        cleaned_data.append(item)
    return cleaned_data

def transform_data(cleaned_data):
    # step 2: Transform data
    transformed_data = []
    for item in cleaned_data:
        if isinstance(item, str):
            item = item.upper()
        transformed_data.append(item)
    return transformed_data

def summarize_data(transformed_data):
    # step 3: Summarize data
    summary = {}
    for item in transformed_data:
        if item in summary:
            summary[item] += 1
        else:
            summary[item] = 1
    return summary


def process_data(raw_data):
    # step 1: Clean data
    cleaned_data = clean_data(raw_data)
    # step 2: Transform data
    transformed_data = transform_data(cleaned_data)
    # step 3: Summarize data
    summary = summarize_data(transformed_data)

    return summary