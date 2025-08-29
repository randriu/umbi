import umbi.io

import umbi
import logging
umbi.set_log_level(level=logging.DEBUG)

umbfile = "../examples/_temp_umb_files/examples/dice/dice.umb"
# reader = umbi.io.TarReader(umbfile)

ats = umbi.read_umb(umbfile)
# json_obj = reader.read_json("index.json")
# print(umbi.json_to_string(json_obj))
# umbi_index = umbi.UmbIndex.from_json(json_obj)
# print(umbi_index.annotations.rewards)
# print(umbi_index.annotations.variables)

# print(umbi_index)

# jsonlike = umbi_index.to_json()
# print(jsonlike)

# reader.warn_unread_files()
