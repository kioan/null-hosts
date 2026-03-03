import logging
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class NullHostsFile:
    """
    Represents a null-hosts file, capable of parsing, cleaning,
    and exporting hosts entries.
    """

    NULL_IP = "0.0.0.0"

    def __init__(self, header: list[str], hosts: set[str], source_filepath: Optional[Path] = None) -> None:
        self.header: list[str] = header
        self.hosts: set[str] = hosts
        self.source_filepath: Optional[Path] = source_filepath

    @classmethod
    def from_input_file(cls, filepath: Path) -> tuple["NullHostsFile", dict]:
        """
        Parses a hosts file and creates a NullHostsFile instance.

        Returns:
            A tuple of (NullHostsFile, stats) where stats contains:
              - total: number of unique hosts after deduplication
              - duplicates: number of duplicate entries removed
              - invalid: number of invalid/malformed lines ignored
        """
        try:
            lines = filepath.read_text(encoding="utf-8").splitlines(keepends=True)
        except IOError as e:
            logger.error(f"Error reading file {filepath}: {e}")
            raise

        header: list[str] = []
        hosts: set[str] = set()
        duplicates = 0
        invalid_entries = 0

        for line_number, line_content in enumerate(lines, 1):
            stripped_line = line_content.strip()

            if not stripped_line:
                continue

            if cls.is_comment(line_content):
                header.append(cls.format_comment(line_content))
            elif cls.is_nullhost_entry(stripped_line):
                # Normalize: strip trailing dot and lowercase (DNS is case-insensitive)
                host = stripped_line.split()[1].rstrip(".").lower()
                if host in hosts:
                    duplicates += 1
                    logger.warning(f"L{line_number}: Duplicate entry ignored: '{host}'")
                else:
                    hosts.add(host)
            else:
                logger.warning(f"L{line_number}: Invalid or malformed line removed: '{stripped_line}'")
                invalid_entries += 1

        if duplicates > 0:
            logger.info(f"Duplicates removed: {duplicates}")
        if invalid_entries > 0:
            logger.info(f"Invalid or malformed lines removed: {invalid_entries}")

        stats = {
            "total": len(hosts),
            "duplicates": duplicates,
            "invalid": invalid_entries,
        }

        return cls(header, hosts, source_filepath=filepath), stats

    def render(self) -> str:
        """Renders the normalized file content as a string."""
        sorted_hosts = sorted(self.hosts)
        lines = []

        for hdr_line in self.header:
            lines.append(f"{hdr_line}\n")

        if self.hosts:
            lines.append("\n\n")

        for host in sorted_hosts:
            lines.append(f"{self.NULL_IP} {host}\n")

        return "".join(lines)

    def export_to_file(self, filepath: Path) -> None:
        """Writes the normalized hosts to the specified file."""
        try:
            filepath.write_text(self.render(), encoding="utf-8")
            logger.info(f"Processed hosts successfully written to {filepath}")
        except IOError as e:
            logger.error(f"Error writing to file {filepath}: {e}")
            raise

    def save(self, backup: bool = True) -> None:
        """
        Saves changes back to the original source file.
        Creates a .bak backup first unless backup=False.
        """
        if not self.source_filepath:
            raise ValueError("Source filepath not set. Cannot save in-place.")
        if backup:
            bak_path = self.source_filepath.with_suffix(self.source_filepath.suffix + ".bak")
            shutil.copy2(self.source_filepath, bak_path)
            logger.info(f"Backup created: {bak_path}")
        self.export_to_file(self.source_filepath)

    def is_changed(self) -> bool:
        """Returns True if the current file content differs from the normalized output."""
        if not self.source_filepath:
            raise ValueError("Source filepath not set.")
        current = self.source_filepath.read_text(encoding="utf-8")
        return current != self.render()

    @classmethod
    def is_comment(cls, line_content: str) -> bool:
        """Checks if a line is a comment (starts with '#', ignoring leading whitespace)."""
        return line_content.lstrip().startswith("#")

    @classmethod
    def format_comment(cls, comment_line: str) -> str:
        """
        Normalizes a comment line to '# <content>'.
        Strips all leading '#' characters and whitespace from the content.
        An empty comment (e.g. '##' or '# ') is returned as bare '#'.
        """
        stripped = comment_line.strip()
        content = stripped.lstrip("#").strip()
        if content:
            return f"# {content}"
        return "#"

    @classmethod
    def is_valid_fqdn(cls, name: str) -> bool:
        """
        Validates if the given string is a syntactically valid FQDN.
        - Total length max 253 characters (excluding optional trailing dot).
        - Must have at least two labels (e.g. 'example.com', not 'example').
        - Labels are 1-63 characters each.
        - Labels start and end with an alphanumeric character.
        - Labels contain only alphanumeric characters or hyphens.
        """
        if not name or len(name) > 253:
            return False
        name = name.rstrip(".")
        if not name:
            return False

        labels = name.split(".")
        if len(labels) < 2:
            return False
        if not all(labels):  # catches double dots like "domain..com"
            return False

        for label in labels:
            if not (1 <= len(label) <= 63):
                return False
            if not label[0].isalnum() or not label[-1].isalnum():
                return False
            if not all(ch.isalnum() or ch == "-" for ch in label):
                return False

        return True

    @classmethod
    def is_null_ip(cls, ip: str) -> bool:
        """Checks if the IP address is the null IP '0.0.0.0'."""
        return ip == cls.NULL_IP

    @classmethod
    def is_nullhost_entry(cls, line_content: str) -> bool:
        """
        Checks if a line is a valid null-host entry (e.g. '0.0.0.0 some.domain.com').
        Inline comments are not supported.
        """
        parts = line_content.strip().split()
        if len(parts) == 2:
            return cls.is_null_ip(parts[0]) and cls.is_valid_fqdn(parts[1])
        return False
