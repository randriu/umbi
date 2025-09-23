import logging

logger = logging.getLogger(__name__)

import click

import umbi


@click.command()
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    show_default=True,
    required=False,
    help="logging level",
)
@click.option("--import-umb", type=click.Path(), required=False, help=".umb filepath to import")
@click.option("--export-umb", type=click.Path(), required=False, help=".umb filepath to export")
def main(log_level, import_umb, export_umb):

    umbi.setup_logging()
    umbi.set_log_level(getattr(logging, log_level))
    logger.info(f"this is {umbi.__toolname__} v.{umbi.__version__}")

    ats = None
    if import_umb is not None:
        ats = umbi.io.read_umb(import_umb)
    if export_umb is not None:
        if ats is None:
            raise ValueError("--export-umb specified, but nothing to export")
        umbi.io.write_umb(ats, export_umb)


if __name__ == "__main__":
    main()
