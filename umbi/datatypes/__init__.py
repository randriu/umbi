"""
umbi.datatypes: Core datatype definitions and utilities.

This package contains the fundamental datatype classes and definitions used throughout umbi,
including intervals, composite types, vector utilities, and JSON operations. Serialization operations remain in umbi.binary.
"""

#TODO add variable valuation in addition to struct
#TODO add vector?
#TODO add CSR vector
#TODO add vector of ranges (for CSR?)

from .common_type import *
from .interval import *
from .struct import *
from .csr import *
from .json import *

__all__ = [
	# definitions.py
	"CommonType",
    "NumericPrimitive",
	"Numeric",
    "is_instance_of_common_type",

	"is_fixed_size_integer_type",
	"is_variable_size_integer_type",
	"is_integer_type",
	"assert_integer_type",

	"is_interval_type",
	"assert_interval_type",
	"interval_base_type",

	# interval.py
	"Interval",

	# struct.py
	"StructPadding",
	"StructAttribute",
	"StructType",

	# csr.py
	"VectorType",
    "CSR_TYPE",
	"is_vector_ranges",
	"is_vector_csr",
	"csr_to_ranges",
	"ranges_to_csr",

	# json.py
	"JsonPrimitive",
	"JsonList",
	"JsonDict",
	"JsonLike",
	"is_json_instance",
	"json_remove_none_dict_values",
	"json_to_string",
	"string_to_json",
]