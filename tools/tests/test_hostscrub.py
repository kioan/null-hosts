from pathlib import Path

import pytest
from hostscrub import NullHostsFile


def test_constructor():
    headers = ["# line1", "# line2", "# line3"]
    hosts = ["abs.com", "def.com", "ghi.jkl.com"]
    nhf = NullHostsFile(headers, hosts)
    assert nhf.header == headers
    assert nhf.hosts == hosts


@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


def test_from_input_file(fixtures_dir):
    input_file = fixtures_dir / "input_1.txt"
    nhf, _ = NullHostsFile.from_input_file(input_file)
    assert "abc.example.com" in nhf.hosts
    assert "def.example.com" in nhf.hosts


def test_export_to_file(fixtures_dir, tmp_path):
    input_file = fixtures_dir / "input_1.txt"
    nhf, _ = NullHostsFile.from_input_file(input_file)
    output_file = tmp_path / "output.txt"
    nhf.export_to_file(output_file)
    actual_output = output_file.read_text().strip()
    expected_output = (fixtures_dir / "expected_1.txt").read_text().strip()
    assert actual_output == expected_output


def test_is_comment():
    nhc = NullHostsFile
    assert nhc.is_comment("# This is a comment")
    assert nhc.is_comment("#This is a comment")
    assert nhc.is_comment(" # This is a comment")
    assert nhc.is_comment("## This is a comment")
    assert not nhc.is_comment("Not comment")
    assert not nhc.is_comment("Not comment #")


def test_format_comment():
    nhc = NullHostsFile
    assert nhc.format_comment("# This is a comment") == "# This is a comment"
    assert nhc.format_comment("#This is a comment") == "# This is a comment"
    assert nhc.format_comment(" # This is a comment") == "# This is a comment"


def test_is_valid_fqdn():
    nhc = NullHostsFile
    assert nhc.is_valid_fqdn("example.com")
    assert nhc.is_valid_fqdn("sub.domain.example.com")
    assert nhc.is_valid_fqdn("ex-ample.co.uk")
    assert not nhc.is_valid_fqdn("-example.com")
    assert not nhc.is_valid_fqdn("example-.com")
    assert not nhc.is_valid_fqdn("exa_mple.com")
    assert not nhc.is_valid_fqdn("")
    assert not nhc.is_valid_fqdn(".")
    assert nhc.is_valid_fqdn("example.com.")


def test_is_null_ip():
    nhc = NullHostsFile
    assert nhc.is_null_ip("0.0.0.0")
    assert not nhc.is_null_ip("1.2.3.4")


def test_is_nullhost_entry():
    nhc = NullHostsFile
    assert nhc.is_nullhost_entry("0.0.0.0 example.com")
    assert nhc.is_nullhost_entry(" 0.0.0.0 \t example.com  ")
    assert not nhc.is_nullhost_entry("127.0.0.1 example.com")
    assert not nhc.is_nullhost_entry("0.0.0.0 example.com #")
