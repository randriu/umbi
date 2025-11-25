"""
umbi.datatypes: Core datatype definitions and utilities.

This package contains the fundamental datatype classes and definitions used throughout umbi,
including intervals, composite types, vector utilities, and JSON operations. Serialization operations remain in umbi.binary.
"""

from .common_type import *
from .interval import Interval
from .json import *
from .struct import *
from .utils import *
from .vector import *

__all__ = [
    # common_type.py
    "CommonType",
    "is_fixed_size_integer_type",
    "is_variable_size_integer_type",
    "is_integer_type",
    "is_interval_type",
    "assert_interval_type",
    "interval_base_type",
    "is_numeric_type",
    # interval.py
    "Interval",
    # struct.py
    "StructPadding",
    "StructAttribute",
    "StructType",
    # json.py
    "JsonPrimitive",
    "JsonList",
    "JsonDict",
    "JsonLike",
    "is_json_instance",
    "json_remove_none_dict_values",
    "json_to_string",
    "string_to_json",
    # utils.py
    "NumericPrimitive",
    "Numeric",
    "is_instance_of_common_type",
    "promote_numeric_primitive",
    "promote_numeric",
    # vector.py
    "VectorType",
    "CSR_TYPE",
    "assert_is_list",
    "is_vector_of_common_type",
    "is_vector_of_type",
    "vector_common_numeric_type",
    "promote_vector",
]
