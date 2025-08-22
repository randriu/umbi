import io
import logging
import tarfile

import umbi


def tar_read(tarpath: str) -> dict[str, bytes]:
    """
    Read all contents of a tarball file.

    :returns: a dictionary filename -> contents
    """
    filename_data = {}
    with tarfile.open(tarpath, mode="r:*") as tar:
        for member in tar.getmembers():
            if member.isfile():
                fileobj = tar.extractfile(member)
                if fileobj is None:
                    raise KeyError(f"Could not extract file {member.name} from {tarpath}")
                filename_data[member.name] = fileobj.read()
    return filename_data


def tar_write(tarpath: str, filename_data: dict[str, bytes], gzip: bool = True):
    """
    Create a tarball file with the given contents.

    :param tarpath: path to a tarball file
    :param filename_data: a dictionary filename -> binary string
    :param gzip: if True, the tarball file will be gzipped
    """
    mode = "w" if not gzip else "w:gz"
    with tarfile.open(tarpath, mode=mode) as tar:
        for filename, data in filename_data.items():
            tar_info = tarfile.TarInfo(name=filename)
            tar_info.size = len(data)
            tar.addfile(tar_info, io.BytesIO(data))
    logging.info(f"data exported to {tarpath}")


def row_start_to_ranges(row_start: list) -> list:
    """Convert row start indices to ranges."""
    ranges = []
    num_rows = len(row_start) - 1
    for row in range(num_rows):
        ranges.append(list(range(row_start[row], row_start[row + 1])))
    return ranges


def ranges_to_row_start(ranges: list) -> list:
    """Convert ranges to row start indices."""
    row_start = [interval[0] for interval in ranges]
    row_start.append(ranges[-1][-1] + 1)
    assert len(row_start) == len(ranges) + 1
    return row_start


def indices_to_bitvector(vector: list[int], num_entries: int) -> list[bool]:
    """Convert a list of unsigned integers to a bitvector.

    :param vector: a list of unsigned integers
    :param num_entries: the size of the resulting bitvector, must be no smaller than max(vector)
    """
    assert max(vector) < num_entries
    bitvector = [False] * num_entries
    for x in vector:
        bitvector[x] = True
    return bitvector


def bitvector_to_indices(bitvector: list[bool]) -> list[int]:
    """Convert a bitvector to a list of indices set to True.

    :param bitvector: a list of bools
    """
    return [i for i, bit in enumerate(bitvector) if bit]


class TarReader:
    """An auxiliary class to simplify tar reading and to keep track of (un)used files."""

    def __init__(self, tarpath: str):
        self.tarpath = tarpath
        self.filename_data = tar_read(tarpath)
        self.filename_read = {filename: False for filename in self.filenames}

        filenames_str = "\n".join(self.filenames)
        logging.debug(f"found the following files:\n{filenames_str}")

    @property
    def filenames(self) -> list[str]:
        """List of filenames in the tarball."""
        return list(self.filename_data.keys())

    def warn_unread_files(self):
        """Print warning about unread files from the tarfile, if such exist."""
        unread_files = [f for f in self.filenames if f not in self.filename_read]
        if len(unread_files) > 0:
            unread_files_str = "\n".join(unread_files)
            logging.warning(
                f'the following files from "{self.tarpath}" were not used during parsing:\n{unread_files_str}'
            )

    def read(self, filename: str, file_format: str, csr: bool = False) -> umbi.JsonLike | list:
        """Read contents and process a specific file in the tarball.

        :param file_format: one of ["json", "bool", "uint32","uint64", "double"]
        :param csr: if True, interpret the data as a CSR vector and convert to ranges
        :raises: KeyError if the file is not present in the tarball
        """
        if filename not in self.filenames:
            raise KeyError(f"tar archive {self.tarpath} has no required file {filename}")
        self.filename_read[filename] = True
        data = self.filename_data[filename]

        if file_format == "json":
            return umbi.bytes_to_json(data)

        data = umbi.bytes_to_vector(data, file_format)
        if file_format == "bool":
            data = bitvector_to_indices(data)
        if csr:
            data = row_start_to_ranges(data)
        return data


class TarWriter:
    """An auxiliary class to simplify tar writing."""

    def __init__(self):
        self.filename_data = {}

    def add_json(self, json_obj: umbi.JsonLike, filename: str):
        """Add a JSON-like object to the tarball."""
        data_bytes = umbi.json_to_bytes(json_obj)
        self.filename_data[filename] = data_bytes

    def add_list(self, data: list, filename: str, file_format: str, csr: bool = False):
        """Add a list to the tarball, optionally converting ranges to row starts."""
        if csr:
            data = ranges_to_row_start(data)
        data_bytes = umbi.vector_to_bytes(data, file_format)
        self.filename_data[filename] = data_bytes

    def write(self, tarpath: str, gzip: bool = True):
        """Write all added files to a tarball."""
        tar_write(tarpath, self.filename_data, gzip=gzip)
