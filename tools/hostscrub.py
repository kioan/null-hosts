import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)
# Logging will be configured in main()


class NullHostsFile:
    """
    Represents a null-hosts file, capable of parsing, cleaning,
    and exporting hosts entries.
    """

    NULL_IP = "0.0.0.0"

    def __init__(self, header: list[str], hosts: set[str], source_filepath: Optional[Path] = None) -> None:
        """
        Initializes a NullHostsFile object.

        Args:
            header: A list of strings representing the header/comment lines.
            hosts: A set of strings representing the hostnames.
            source_filepath: The original path of the file this object was created from.
        """
        self.header: list[str] = header
        self.hosts: set[str] = hosts
        self.source_filepath: Optional[Path] = source_filepath

    @classmethod
    def from_input_file(cls, filepath: Path) -> "NullHostsFile":
        """
        Parses a hosts file and creates a NullHostsFile instance.
        """
        lines: list[str] = []
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                lines = file.readlines()
        except IOError as e:
            logger.error(f"Error reading file {filepath}: {e}")
            raise

        header = []
        hosts = set()
        duplicates = 0
        invalid_entries = 0

        for line_number, line_content in enumerate(lines, 1):
            stripped_line = line_content.strip()

            if not stripped_line:  # Skip empty lines
                continue

            if cls.is_comment(line_content):
                header.append(cls.format_comment(line_content))
            elif cls.is_nullhost_entry(line_content):
                # is_nullhost_entry ensures line.split() is safe and parts[1] is the host
                host = stripped_line.split()[1]
                if host not in hosts:
                    hosts.add(host)
                else:
                    duplicates += 1
            elif stripped_line:  # Non-empty, not comment, not valid host entry
                logger.warning(f"L{line_number}: Invalid or malformed line ignored: '{stripped_line}'")
                invalid_entries += 1

        if duplicates > 0:
            logging.info(f"Duplicates found and removed: {duplicates}")
        if invalid_entries > 0:
            logging.info(f"Invalid or malformed lines ignored: {invalid_entries}")

        return cls(header, hosts, source_filepath=filepath)

    def export_to_file(self, filepath: Path) -> None:
        """
        Exports the header and sorted hosts entries to the specified file.
        """
        sorted_hosts = sorted(list(self.hosts))

        try:
            with open(filepath, "w", encoding="utf-8") as file:
                for hdr_line in self.header:
                    file.write(f"{hdr_line}\n")

                # Add a separator between header and host entries if there are hosts
                if self.hosts:
                    file.write("\n\n")

                for host in sorted_hosts:
                    file.write(f"{self.NULL_IP} {host}\n")
            logger.info(f"Processed hosts successfully written to {filepath}")
        except IOError as e:
            logger.error(f"Error writing to file {filepath}: {e}")
            raise

    def save(self):
        """
        Saves the changes back to the original source file.
        Raises ValueError if the source filepath is not set.
        """
        if not self.source_filepath:
            logger.error("Source filepath not set. Cannot save in-place.")
            raise ValueError("Source filepath not set. Cannot save in-place.")
        logger.info(f"Saving changes to {self.source_filepath}...")
        self.export_to_file(self.source_filepath)

    @classmethod
    def is_comment(cls, line_content: str) -> bool:
        """Checks if a line is a comment (starts with '#')."""
        return line_content.lstrip().startswith("#")

    @classmethod
    def format_comment(cls, comment_line: str) -> str:
        """Formats a comment line to ensure it starts with '# '."""
        stripped_comment = comment_line.strip()
        # Remove existing '#' and leading/trailing whitespace from the content
        content = stripped_comment.removeprefix("#").strip()
        return f"# {content}"

    @classmethod
    def is_valid_fqdn(cls, name: str) -> bool:
        """
        Validates if the given string is a syntactically valid FQDN.
        - Total length max 253 characters.
        - Labels (parts between dots) are 1-63 characters.
        - Labels start and end with an alphanumeric character.
        - Labels contain only alphanumeric characters or hyphens.
        """
        if not name or len(name) > 253:  # Added explicit check for empty name
            return False
        if name.endswith("."):
            # remove the trailing dot if present
            name = name[:-1]
            if not name:  # Handles case where name was just "."
                return False

        labels = name.split(".")
        if not labels or not all(labels):  # Ensure no empty labels (e.g., "domain..com")
            return False
        for label in labels:
            if len(label) == 0 or len(label) > 63:
                # labels (between dots) are 1-63 characters
                return False
            if not label[0].isalnum() or not label[-1].isalnum():
                # labels must start and end with alphanumeric
                return False
            for ch in label:
                if not (ch.isalnum() or ch == "-"):
                    # allowed characters: letters, digits, hyphens.
                    return False
        return True

    @classmethod
    def is_null_ip(cls, ip: str) -> bool:
        """Checks if the IP address is the null IP '0.0.0.0'."""
        return ip == cls.NULL_IP

    @classmethod
    def is_nullhost_entry(cls, line_content: str) -> bool:
        """
        Checks if a line is a valid null-host entry (e.g., "0.0.0.0 some.domain.com").
        Does not support inline comments on the same line as the host entry.
        """
        stripped_line = line_content.strip()
        parts = stripped_line.split()  # Splits by whitespace, handles multiple spaces
        if len(parts) == 2:
            return cls.is_null_ip(parts[0]) and cls.is_valid_fqdn(parts[1])
        return False


def main():
    logging.basicConfig(
        level=logging.INFO,  # Default to INFO; DEBUG can be enabled if needed
        format="%(levelname)s: %(message)s",
        encoding="utf-8",
    )

    parser = argparse.ArgumentParser(
        description="Process a null-hosts file. Removes duplicate entries, sorts them alphabetically, and validates entries."
    )
    parser.add_argument("filename", type=Path, help="Path to the hosts file (absolute or relative)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=False,
        help="Output file to write. If omitted, the input file will be updated.",
    )

    args = parser.parse_args()

    input_file = Path(args.filename)

    if not input_file.is_file():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)

    try:
        logger.info(f"Processing hosts file: {input_file}")
        nh = NullHostsFile.from_input_file(input_file)

        if args.output:
            output_file = Path(args.output)
            logger.info(f"Writing to output file: {output_file}")
            nh.export_to_file(output_file)
        else:
            logger.info(f"Updating input file in-place: {input_file}")
            nh.save()

        logger.info("Hosts file processing complete.")

    except IOError:
        # Specific error messages are logged by the methods raising IOError
        logger.error("A file operation failed. Please check permissions and file paths.")
        sys.exit(1)
    except ValueError as e:  # Catch specific errors like from nh.save()
        logger.error(f"A value error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)  # Log stack trace for unexpected errors
        sys.exit(1)


if __name__ == "__main__":
    main()
