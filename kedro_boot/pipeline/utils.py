from collections import Counter


def find_duplicates(lst):
    counter = Counter(lst)
    duplicates = [value for value, count in counter.items() if count > 1]

    return duplicates
