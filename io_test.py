import logging
import os

import umbi

umbi.set_log_level(level=logging.WARNING)


def try_file(umbpath: str):
    try:
        umb = umbi.read_umb(umbpath)
        umbi.write_umb(umb, "out.umb")
    except Exception as e:
        logging.error(f"Error processing {umbpath}: {e}")


test_folder = "../_temp_umb_files/examples/"
for root, dirs, files in os.walk(test_folder):
    for filename in files:
        if filename.endswith(".umb"):
            umbfile = os.path.join(root, filename)
            try_file(umbfile)
