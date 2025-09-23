"""
Utilities for reading/wrting Tar archives.
"""

import io as std_io
import logging

logger = logging.getLogger(__name__)
import tarfile

import umbi.binary
import umbi.vectors

from .jsons import JsonLike, bytes_to_json, json_to_bytes


def is_of_vector_type(filetype: str) -> bool:
    return filetype.startswith("vector[") and filetype.endswith("]")


def value_type_of(filetype: str) -> str:
    if is_of_vector_type(filetype):
        return filetype[len("vector[") : -1]
    raise ValueError(f"filetype {filetype} is not a vector type")


class TarReader:
    """An auxiliary class to simplify tar reading."""

    @staticmethod
    def load_tar(tarpath: str) -> dict[str, bytes]:
        """
        Load all files from a tarball into memory.
        :return: a dictionary filename -> binary string
        """
        logger.debug(f"loading tarfile from {tarpath} ...")
        filename_data = {}
        with tarfile.open(tarpath, mode="r:*") as tar:
            for member in tar.getmembers():
                if member.isfile():
                    fileobj = tar.extractfile(member)
                    if fileobj is None:
                        raise KeyError(f"Could not extract file {member.name} from {tarpath}")
                    filename_data[member.name] = fileobj.read()
        logger.debug(f"successfully loaded the tarfile")
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

    def read_file(self, filename: str, required: bool = False) -> bytes | None:
        """Read raw bytes from a specific file in the tarball"""
        logger.debug(f"loading {filename} ...")
        if filename not in self.filenames:
            if not required:
                return None
            else:
                raise KeyError(f"tar archive {self.tarpath} has no file {filename}")
        return self.filename_data[filename]

    def read_filetype(self, filename: str, filetype: str, required: bool = False):
        """
        Read a file of a specific type.
        :param filename: name of the file to read
        :param filetype: one of ["bytes", "json", "csr", "vector[X]"]
        :param required: if True, raise an error if the file is not found
        """
        data = self.read_file(filename, required)
        if data is None:
            return None
        if filetype == "bytes":
            return data
        if filetype == "json":
            return bytes_to_json(data)
        if filetype == "csr":
            return umbi.vectors.csr_to_ranges(umbi.binary.bytes_to_vector(data, "uint64"))
        if is_of_vector_type(filetype):
            value_type = value_type_of(filetype)
            return umbi.binary.bytes_to_vector(data, value_type)
        else:
            raise ValueError(f"unrecognized file type {filetype} for file {filename}")

    def read_filetype_csr(
        self, filename: str, value_type: str, required: bool, filename_csr: str, required_csr: bool = False
    ) -> list | None:
        """
        Read a file containing a vector of values. Use an accompanying CSR file if needed.
        :param filename: name of the main file to read
        :param value_type: value type
        :param required: if True, raise an error if the main file is not found
        :param filename_csr: name of the accompanying CSR file
        :param required_csr: if True, raise an error if the CSR file is not found
        """
        data = self.read_file(filename, required)
        if data is None:
            return None
        chunk_ranges = self.read_filetype(filename_csr, "csr", required=required_csr)
        assert isinstance(chunk_ranges, list) or chunk_ranges is None
        return umbi.binary.bytes_to_vector(data, value_type, chunk_ranges=chunk_ranges)


class TarWriter:  #
    """An auxiliary class to simplify tar writing."""

    @classmethod
    def tar_write(cls, tarpath: str, filename_data: dict[str, bytes], compression: str = "gz"):
        """
        Create a tarball file with the given contents.

        :param tarpath: path to a tarball file
        :param filename_data: a dictionary filename -> binary string
        :param compression: compression algorithm one of ("gz", "bz2", "xz" or "" for no compression)
        """
        logger.debug(f"writing tarfile {tarpath} with compression '{compression}' ...")
        assert compression in ("", "gz", "bz2", "xz"), "unsupported compression algorithm"
        mode = "w"
        if compression != "":
            mode = f"w:{compression}"
        with tarfile.open(tarpath, mode=mode) as tar:  # type: ignore
            for filename, data in filename_data.items():
                tar_info = tarfile.TarInfo(name=filename)
                tar_info.size = len(data)
                tar.addfile(tar_info, std_io.BytesIO(data))
        logger.debug(f"successfully wrote the tarfile")

    def __init__(self):
        self.filename_data = {}

    def add_file(self, filename: str, data: bytes):
        """Add a (binary) file to the tarball."""
        logger.debug(f"writing {filename} ...")
        if filename in self.filename_data:
            logger.warning(f"file {filename} already exists in the tarball")
        self.filename_data[filename] = data

    def add_filetype(self, filename: str, filetype: str, data, required: bool = False):
        if data is None:
            if required:
                raise ValueError(f"missing required data for {filename}")
            return
        data_out = None
        if filetype == "bytes":
            data_out = data
        elif filetype == "json":
            data_out = json_to_bytes(data)
        elif filetype == "csr":
            data_out, chunk_ranges = umbi.binary.vector_to_bytes(umbi.vectors.ranges_to_csr(data), "uint64")
            assert chunk_ranges is None, "unexpected chunk ranges"
        elif is_of_vector_type(filetype):
            value_type = value_type_of(filetype)
            data_out, chunk_ranges = umbi.binary.vector_to_bytes(data, value_type)
            assert chunk_ranges is None, "exporting the vector requires the CSR file, but no such file was specified"
        else:
            raise ValueError(f"unrecognized file type {filetype} for file {filename}")
        assert data_out is not None, "data is not None, but data_out is None"
        assert isinstance(data_out, bytes), "data_out must be of type bytes"
        self.add_file(filename, data_out)

    def add_filetype_csr(self, filename: str, value_type: str, data, required: bool, filename_csr: str):
        if data is None:
            if required:
                raise ValueError(f"missing required data for {filename}")
            return
        data_out, chunk_ranges = umbi.binary.vector_to_bytes(data, value_type)
        self.add_file(filename, data_out)
        if chunk_ranges is not None:
            self.add_filetype(filename_csr, "csr", chunk_ranges, required=True)
        else:
            logger.debug(f"skipping CSR file {filename_csr}")

    def write(self, tarpath: str):
        """Write all added files to a tarball."""
        TarWriter.tar_write(tarpath, self.filename_data)
