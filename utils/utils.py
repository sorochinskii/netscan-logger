class ListsNotEqualException(Exception):
    pass


def to_lists_of_dicts(**kwargs):
    result = []
    maxlen = max(list(map(lambda x: len(kwargs[x]), kwargs)))
    names = [i for i in kwargs]
    for i in range(maxlen):
        result.append({name: kwargs[name][i] for name in names})
    return result


def check_inequality(*lengths):
    if sum(lengths) / len(lengths) != lengths[0]:
        raise ListsNotEqualException(f"Lengths are {lengths}")
    return True
