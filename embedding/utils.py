"""Utility functions for embedding"""

COMPOSITE_SPLITTER = '$'

def tuple_to_composite_key(tup):
    return COMPOSITE_SPLITTER.join([str(item) for item in tup])

def composite_key_to_tuple(key):
    return tuple([int(item) if item.isdigit() else item for item in key.split(COMPOSITE_SPLITTER)])