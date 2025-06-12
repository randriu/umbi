import io
import logging
import tarfile

import umbi


def tar_filenames(tarpath: str) -> list[str]:
    """Retrieve filenames in the tarball file."""
    with tarfile.open(tarpath, mode="r:*") as tar:
        return [m.name for m in tar.getmembers() if m.isfile()]


def tar_read_file(tarpath: str, filename: str) -> object:
    """Read contents of a specific file in the tarball."""
    with tarfile.open(tarpath, mode="r:*") as tar:
        filenames = [m.name for m in tar.getmembers() if m.isfile()]
        if filename not in filenames:
            raise KeyError(f"{tarpath} has no file {filename}")
        member = tar.getmember(filename)
        return tar.extractfile(member).read()


def tar_read(tarpath: str) -> dict[str, bytes]:
    """
    Read all contents of a tarball file.

    :returns: a dictionary filename -> contents
    """
    filename_data = {}
    with tarfile.open(tarpath, mode="r:*") as tar:
        for member in tar.getmembers():
            if member.isfile():
                filename_data[member.name] = tar.extractfile(member).read()
    return filename_data


def tar_write(tarpath: str, filename_data: dict[str, bytes], gzip: bool = True):
    """
    Create a tarball file with the given contents.

    :param tarpath: path to a tarball file
    :param filename_data: a dictionary filename -> binary string
    :param gzip: if True, the tarball file will be gzipped
    """
    mode = "w"
    if gzip:
        mode = "w:gz"
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode=mode) as tar:
        for filename, data in filename_data.items():
            tar_info = tarfile.TarInfo(name=filename)
            tar_info.size = len(data)
            tar.addfile(tar_info, io.BytesIO(data))
    tar_bytes = tar_stream.getvalue()
    with open(tarpath, "wb") as file:
        file.write(tar_bytes)
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
        self.filenames = tar_filenames(tarpath)
        self.files_read = set()

        filenames_str = "\n".join(self.filenames)
        logging.debug(f"found the following files:\n{filenames_str}")

    def warn_unread_files(self):
        """Print warning about unread files from the tarfile, if such exist."""
        unread_files = [f for f in self.filenames if f not in self.files_read]
        if len(unread_files) > 0:
            unread_files_str = "\n".join(unread_files)
            logging.warning(
                f'the following files from "{self.tarpath}" were not used during parsing:\n{unread_files_str}'
            )

    def read(self, filename: str, file_format: str, csr: bool = False) -> object:
        """Read contents and process a specific file in the tarball.

        :param file_format: one of ["json", "bool", "uint32","uint64", "double"]
        """
        if filename not in self.filenames:
            raise KeyError(f"tar archive {self.tarpath} has no required file {filename}")
        self.files_read.add(filename)
        data = tar_read_file(self.tarpath, filename)

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
        self.filename_data = dict[str, bytes]()

    def add(self, data: object, filename: str, file_format: str, csr: bool = False):
        if csr:
            data = ranges_to_row_start(data)

        if file_format == "json":
            data = umbi.json_to_bytes(data)
        else:
            # if file_format == "bool":
            #     data = indices_to_bitvector(data)
            data = umbi.vector_to_bytes(data, file_format)

        self.filename_data[filename] = data

    def write(self, tarpath: str):
        umbi.tar_write(tarpath, self.filename_data)
