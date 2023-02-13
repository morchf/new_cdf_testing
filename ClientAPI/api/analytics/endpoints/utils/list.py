from typing import List, Dict, Set


def unique(l: List[Dict], key: str) -> Set[any]:
    """
    Unique values in list of objects

    Args:
        l (List): List of dictionaries
        key (str): Dictionary key

    Returns:
        Set with all unique values for a dictionary key. Includes 'None'
        for dictionaries missing the field
    """
    if not l or len(l) == 0:
        return set()

    return {x.get(key) for x in l}
