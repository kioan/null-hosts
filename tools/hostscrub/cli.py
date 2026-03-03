import argparse
import logging
import sys
from pathlib import Path

from .hostsfile import NullHostsFile

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        encoding="utf-8",
    )

    parser = argparse.ArgumentParser(
        description=(
            "Process a null-hosts file: remove duplicates, sort entries alphabetically, "
            "validate FQDNs, and normalize formatting."
        )
    )
    parser.add_argument("filename", type=Path, help="Path to the hosts file (absolute or relative)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=False,
        help="Output file to write. If omitted, the input file is updated in-place.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Check if the file needs processing without writing any changes. "
            "Exits with code 1 if changes would be made, 0 if the file is already clean. "
            "Useful as a git pre-commit hook."
        ),
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating a .bak backup when writing in-place (ignored when --output is set).",
    )

    args = parser.parse_args()
    input_file: Path = args.filename

    if not input_file.is_file():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)

    try:
        logger.info(f"Processing hosts file: {input_file}")
        nh, stats = NullHostsFile.from_input_file(input_file)

        logger.info(
            f"Stats: {stats['total']} hosts total, "
            f"{stats['duplicates']} duplicates removed, "
            f"{stats['invalid']} invalid entries removed"
        )

        if args.check:
            if nh.is_changed():
                logger.warning("File needs processing. Run without --check to apply changes.")
                sys.exit(1)
            else:
                logger.info("File is already clean. No changes needed.")
                sys.exit(0)

        if args.output:
            nh.export_to_file(args.output)
        else:
            nh.save(backup=not args.no_backup)

        logger.info("Done.")

    except IOError:
        logger.error("A file operation failed. Check permissions and file paths.")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
