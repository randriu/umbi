"""
Utilities for reading/wrting Tar archives.
"""

import io
import logging
logger = logging.getLogger(__name__)
import tarfile

from .bytes import bytes_to_vector, vector_to_bytes
from .json import JsonLike, bytes_to_json, json_to_bytes
from .vector import *

class TarReader:
    """An auxiliary class to simplify tar reading and to keep track of (un)used files."""

    @staticmethod
    def load_tar(tarpath: str) -> dict[str, bytes]:
        """
        Load all files from a tarball into memory.
        :return: a dictionary filename -> binary string
        """
        logger.debug(f"reading tarfile {tarpath} ...")
        filename_data = {}
        with tarfile.open(tarpath, mode="r:*") as tar:
            for member in tar.getmembers():
                if member.isfile():
                    fileobj = tar.extractfile(member)
                    if fileobj is None:
                        raise KeyError(f"Could not extract file {member.name} from {tarpath}")
                    filename_data[member.name] = fileobj.read()
        logger.debug(f"successfully read the tarfile {tarpath}")
        return filename_data

    def __init__(self, tarpath: str):
        self.tarpath = tarpath
        self.filename_data = TarReader.load_tar(tarpath)
        # filenames_str = "\n".join(self.filenames)
        # logger.debug(f"found the following files:\n{filenames_str}")

    @property
    def filenames(self) -> list[str]:
        """List of filenames in the tarball."""
        return list(self.filename_data.keys())

    def read_file(self, filename: str, required : bool = True) -> bytes | None:
        """Read raw bytes from a specific file in the tarball"""
        if filename not in self.filenames:
            if not required:
                return None
            else:
                raise KeyError(f"tar archive {self.tarpath} has no file {filename}")
        return self.filename_data[filename]

    def read_json(self, filename: str, required : bool = True) -> JsonLike | None:
        """Read a JSON-like object from a specific file in the tarball."""
        data = self.read_file(filename,required)
        if data is None:
            return None
        return bytes_to_json(data)

    def read_vector(self, filename: str, value_type: str, required : bool = True) -> list | None:
        """Read a vector of items from a specific file in the tarball, optionally converting ranges to row starts."""
        data = self.read_file(filename,required)
        if data is None:
            return None
        return bytes_to_vector(data, value_type)

    def read_csr(self, filename: str, value_type: str = "uint64", required : bool = True) -> list[list[int]] | None:
        """Read a CSR matrix from a specific file in the tarball."""
        assert value_type in ["uint32", "uint64"], "CSR format only supported for integer vectors"
        vector = self.read_vector(filename, value_type, required=required)
        if vector is None:
            return None
        return row_start_to_ranges(vector)

    def read_bitvector_indices(self, filename: str, required : bool = True) -> list[int] | None:
        """Read a bitvector from a specific file in the tarball and convert it to a list of indices set to True."""
        vector = self.read_vector(filename, "bool")
        if vector is None:
            return None
        return bitvector_to_indices(vector)


class TarWriter:
    """An auxiliary class to simplify tar writing."""

    @classmethod
    def tar_write(cls, tarpath: str, filename_data: dict[str, bytes], gzip: bool = True):
        """
        Create a tarball file with the given contents.

        :param tarpath: path to a tarball file
        :param filename_data: a dictionary filename -> binary string
        :param gzip: if True, the tarball file will be gzipped
        """
        logger.debug(f"writing tarfile {tarpath} ...")
        mode = "w" if not gzip else "w:gz"
        with tarfile.open(tarpath, mode=mode) as tar:
            for filename, data in filename_data.items():
                tar_info = tarfile.TarInfo(name=filename)
                tar_info.size = len(data)
                tar.addfile(tar_info, io.BytesIO(data))
        logger.info(f"successfully wrote the tarfile {tarpath}")

    def __init__(self):
        self.filename_data = {}

    def add_file(self, filename: str, data: bytes):
        """Add a (binary) file to the tarball."""
        if filename in self.filename_data:
            logger.warning(f"file {filename} already exists in the tarball")
        self.filename_data[filename] = data

    def add_json(self, filename: str, json_obj: JsonLike):
        """Add a JSON file to the tarball."""
        self.add_file(filename, json_to_bytes(json_obj))

    def add_vector(self, filename: str, vector: list, value_type: str):
        """Add a file containing a vector of items to the tarball, optionally converting ranges to row starts."""
        self.add_file(filename, vector_to_bytes(vector, value_type))
    
    def add_csr(self, filename: str, csr: list[list[int]], value_type: str = "uint64"):
        """Add a file containing a CSR matrix to the tarball."""
        assert value_type in ["uint32", "uint64"], "CSR format only supported for integer vectors"
        row_start = ranges_to_row_start(csr)
        self.add_vector(filename, row_start, value_type)

    def add_bitvector_indices(self, filename: str, bitvector_indices: list[int], num_entries: int):
        """Add a file containing indices of a bitvector to the tarball."""
        bitvector = indices_to_bitvector(bitvector_indices, num_entries)
        self.add_vector(filename, bitvector, "bool")

    def write(self, tarpath: str, gzip: bool = True):
        """Write all added files to a tarball."""
        self.tar_write(tarpath, self.filename_data, gzip=gzip)
