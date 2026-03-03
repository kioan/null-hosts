"""Tests for NullHostsFile."""
import pytest
from pathlib import Path

from hostscrub.hostsfile import NullHostsFile


# ---------------------------------------------------------------------------
# is_valid_fqdn
# ---------------------------------------------------------------------------

class TestIsValidFqdn:
    def test_simple_domain(self):
        assert NullHostsFile.is_valid_fqdn("example.com") is True

    def test_subdomain(self):
        assert NullHostsFile.is_valid_fqdn("sub.example.com") is True

    def test_deep_subdomain(self):
        assert NullHostsFile.is_valid_fqdn("a.b.c.example.com") is True

    def test_single_label_rejected(self):
        assert NullHostsFile.is_valid_fqdn("example") is False

    def test_trailing_dot_valid(self):
        assert NullHostsFile.is_valid_fqdn("example.com.") is True

    def test_only_dot_invalid(self):
        assert NullHostsFile.is_valid_fqdn(".") is False

    def test_empty_string(self):
        assert NullHostsFile.is_valid_fqdn("") is False

    def test_too_long(self):
        assert NullHostsFile.is_valid_fqdn("a" * 254) is False

    def test_label_too_long(self):
        assert NullHostsFile.is_valid_fqdn(f"{'a' * 64}.com") is False

    def test_label_max_length_valid(self):
        assert NullHostsFile.is_valid_fqdn(f"{'a' * 63}.com") is True

    def test_hyphen_in_label(self):
        assert NullHostsFile.is_valid_fqdn("my-host.example.com") is True

    def test_starts_with_hyphen(self):
        assert NullHostsFile.is_valid_fqdn("-host.example.com") is False

    def test_ends_with_hyphen(self):
        assert NullHostsFile.is_valid_fqdn("host-.example.com") is False

    def test_double_dot(self):
        assert NullHostsFile.is_valid_fqdn("host..example.com") is False

    def test_numeric_labels(self):
        assert NullHostsFile.is_valid_fqdn("123.456.com") is True

    def test_underscore_rejected(self):
        assert NullHostsFile.is_valid_fqdn("host_name.example.com") is False

    def test_uppercase_valid(self):
        assert NullHostsFile.is_valid_fqdn("HOST.EXAMPLE.COM") is True

    def test_mixed_case_valid(self):
        assert NullHostsFile.is_valid_fqdn("My-Host.Example.COM") is True

    def test_numeric_tld(self):
        assert NullHostsFile.is_valid_fqdn("host.example.123") is True

    def test_single_char_labels(self):
        assert NullHostsFile.is_valid_fqdn("a.b") is True


# ---------------------------------------------------------------------------
# is_comment
# ---------------------------------------------------------------------------

class TestIsComment:
    def test_hash_line(self):
        assert NullHostsFile.is_comment("# This is a comment") is True

    def test_leading_spaces(self):
        assert NullHostsFile.is_comment("   # comment") is True

    def test_double_hash(self):
        assert NullHostsFile.is_comment("## double hash") is True

    def test_not_comment(self):
        assert NullHostsFile.is_comment("0.0.0.0 example.com") is False

    def test_empty_line(self):
        assert NullHostsFile.is_comment("") is False

    def test_just_hash(self):
        assert NullHostsFile.is_comment("#") is True

    def test_hash_with_newline(self):
        assert NullHostsFile.is_comment("# comment\n") is True


# ---------------------------------------------------------------------------
# format_comment
# ---------------------------------------------------------------------------

class TestFormatComment:
    def test_simple_comment(self):
        assert NullHostsFile.format_comment("# Hello") == "# Hello"

    def test_no_space_after_hash(self):
        assert NullHostsFile.format_comment("#Hello") == "# Hello"

    def test_double_hash(self):
        assert NullHostsFile.format_comment("## Title") == "# Title"

    def test_triple_hash(self):
        assert NullHostsFile.format_comment("### Note") == "# Note"

    def test_hash_only(self):
        assert NullHostsFile.format_comment("#") == "#"

    def test_hash_with_space_only(self):
        assert NullHostsFile.format_comment("# ") == "#"

    def test_leading_spaces(self):
        assert NullHostsFile.format_comment("   # Indented") == "# Indented"

    def test_preserves_content(self):
        assert NullHostsFile.format_comment("# Source: https://example.com") == "# Source: https://example.com"

    def test_strips_newline(self):
        assert NullHostsFile.format_comment("# Hello\n") == "# Hello"

    def test_double_hash_with_content(self):
        assert NullHostsFile.format_comment("## Section Title") == "# Section Title"


# ---------------------------------------------------------------------------
# is_nullhost_entry
# ---------------------------------------------------------------------------

class TestIsNullhostEntry:
    def test_valid_entry(self):
        assert NullHostsFile.is_nullhost_entry("0.0.0.0 example.com") is True

    def test_wrong_ip(self):
        assert NullHostsFile.is_nullhost_entry("127.0.0.1 example.com") is False

    def test_invalid_fqdn_single_label(self):
        assert NullHostsFile.is_nullhost_entry("0.0.0.0 notadomain") is False

    def test_inline_comment_rejected(self):
        assert NullHostsFile.is_nullhost_entry("0.0.0.0 example.com # phishing") is False

    def test_trailing_dot_valid(self):
        assert NullHostsFile.is_nullhost_entry("0.0.0.0 example.com.") is True

    def test_multiple_spaces(self):
        assert NullHostsFile.is_nullhost_entry("0.0.0.0   example.com") is True

    def test_empty_line(self):
        assert NullHostsFile.is_nullhost_entry("") is False

    def test_comment_not_entry(self):
        assert NullHostsFile.is_nullhost_entry("# 0.0.0.0 example.com") is False

    def test_subdomain_entry(self):
        assert NullHostsFile.is_nullhost_entry("0.0.0.0 sub.example.com") is True


# ---------------------------------------------------------------------------
# from_input_file
# ---------------------------------------------------------------------------

class TestFromInputFile:
    def test_basic_parse(self, tmp_path):
        p = tmp_path / "hosts"
        p.write_text("# Header\n\n0.0.0.0 evil.com\n0.0.0.0 phish.net\n", encoding="utf-8")
        nh, stats = NullHostsFile.from_input_file(p)
        assert "evil.com" in nh.hosts
        assert "phish.net" in nh.hosts
        assert stats["total"] == 2
        assert stats["duplicates"] == 0
        assert stats["invalid"] == 0

    def test_duplicate_removal(self, tmp_path):
        p = tmp_path / "hosts"
        p.write_text("0.0.0.0 evil.com\n0.0.0.0 evil.com\n", encoding="utf-8")
        nh, stats = NullHostsFile.from_input_file(p)
        assert len(nh.hosts) == 1
        assert stats["duplicates"] == 1

    def test_case_insensitive_duplicate(self, tmp_path):
        p = tmp_path / "hosts"
        p.write_text("0.0.0.0 Evil.Com\n0.0.0.0 evil.com\n", encoding="utf-8")
        nh, stats = NullHostsFile.from_input_file(p)
        assert len(nh.hosts) == 1
        assert "evil.com" in nh.hosts
        assert stats["duplicates"] == 1

    def test_lowercase_normalization(self, tmp_path):
        p = tmp_path / "hosts"
        p.write_text("0.0.0.0 Evil.COM\n", encoding="utf-8")
        nh, _ = NullHostsFile.from_input_file(p)
        assert "evil.com" in nh.hosts
        assert "Evil.COM" not in nh.hosts

    def test_trailing_dot_normalization(self, tmp_path):
        p = tmp_path / "hosts"
        p.write_text("0.0.0.0 evil.com.\n", encoding="utf-8")
        nh, _ = NullHostsFile.from_input_file(p)
        assert "evil.com" in nh.hosts
        assert "evil.com." not in nh.hosts

    def test_single_label_rejected(self, tmp_path):
        p = tmp_path / "hosts"
        p.write_text("0.0.0.0 notadomain\n", encoding="utf-8")
        nh, stats = NullHostsFile.from_input_file(p)
        assert len(nh.hosts) == 0
        assert stats["invalid"] == 1

    def test_invalid_line_counted(self, tmp_path):
        p = tmp_path / "hosts"
        p.write_text("0.0.0.0 valid.com\njunk line here\n", encoding="utf-8")
        nh, stats = NullHostsFile.from_input_file(p)
        assert stats["invalid"] == 1
        assert stats["total"] == 1

    def test_header_parsed(self, tmp_path):
        p = tmp_path / "hosts"
        p.write_text("# Line 1\n# Line 2\n\n0.0.0.0 evil.com\n", encoding="utf-8")
        nh, _ = NullHostsFile.from_input_file(p)
        assert nh.header == ["# Line 1", "# Line 2"]

    def test_empty_file(self, tmp_path):
        p = tmp_path / "hosts"
        p.write_text("", encoding="utf-8")
        nh, stats = NullHostsFile.from_input_file(p)
        assert len(nh.hosts) == 0
        assert stats["total"] == 0

    def test_source_filepath_set(self, tmp_path):
        p = tmp_path / "hosts"
        p.write_text("0.0.0.0 evil.com\n", encoding="utf-8")
        nh, _ = NullHostsFile.from_input_file(p)
        assert nh.source_filepath == p

    def test_inline_comment_entry_rejected(self, tmp_path):
        p = tmp_path / "hosts"
        p.write_text("0.0.0.0 evil.com # phishing site\n", encoding="utf-8")
        nh, stats = NullHostsFile.from_input_file(p)
        assert len(nh.hosts) == 0
        assert stats["invalid"] == 1

    def test_trailing_dot_logs_warning(self, tmp_path, caplog):
        import logging
        p = tmp_path / "hosts"
        p.write_text("0.0.0.0 evil.com.\n", encoding="utf-8")
        with caplog.at_level(logging.WARNING, logger="hostscrub.hostsfile"):
            NullHostsFile.from_input_file(p)
        assert any("evil.com." in msg for msg in caplog.messages)


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------

class TestRender:
    def test_sorted_output(self):
        nh = NullHostsFile(header=[], hosts={"zebra.com", "alpha.com"})
        output = nh.render()
        lines = [l for l in output.splitlines() if l.startswith("0.0.0.0")]
        assert lines[0] == "0.0.0.0 alpha.com"
        assert lines[1] == "0.0.0.0 zebra.com"

    def test_header_preserved(self):
        nh = NullHostsFile(header=["# My Header"], hosts={"evil.com"})
        output = nh.render()
        assert output.startswith("# My Header\n")

    def test_separator_between_header_and_hosts(self):
        nh = NullHostsFile(header=["# Header"], hosts={"evil.com"})
        output = nh.render()
        assert "# Header\n\n\n0.0.0.0" in output

    def test_no_separator_when_no_hosts(self):
        nh = NullHostsFile(header=["# Header"], hosts=set())
        output = nh.render()
        assert output == "# Header\n"

    def test_each_host_on_own_line(self):
        nh = NullHostsFile(header=[], hosts={"alpha.com", "beta.com"})
        lines = [l for l in nh.render().splitlines() if l]
        assert "0.0.0.0 alpha.com" in lines
        assert "0.0.0.0 beta.com" in lines

    def test_idempotent(self, tmp_path):
        """Parsing a file produced by render() gives identical output on re-render."""
        p = tmp_path / "hosts"
        nh1 = NullHostsFile(header=["# Header"], hosts={"alpha.com", "beta.com"})
        p.write_text(nh1.render(), encoding="utf-8")
        nh2, _ = NullHostsFile.from_input_file(p)
        assert nh1.render() == nh2.render()


# ---------------------------------------------------------------------------
# save / backup
# ---------------------------------------------------------------------------

class TestSave:
    def test_backup_created(self, tmp_path):
        p = tmp_path / "hosts"
        p.write_text("0.0.0.0 evil.com\n", encoding="utf-8")
        bak = p.with_suffix(p.suffix + ".bak")
        nh, _ = NullHostsFile.from_input_file(p)
        nh.save(backup=True)
        assert bak.exists()

    def test_no_backup_when_disabled(self, tmp_path):
        p = tmp_path / "hosts"
        p.write_text("0.0.0.0 evil.com\n", encoding="utf-8")
        bak = p.with_suffix(p.suffix + ".bak")
        nh, _ = NullHostsFile.from_input_file(p)
        nh.save(backup=False)
        assert not bak.exists()

    def test_save_raises_without_source(self):
        nh = NullHostsFile(header=[], hosts={"evil.com"})
        with pytest.raises(ValueError, match="Source filepath not set"):
            nh.save()

    def test_save_writes_sorted_content(self, tmp_path):
        p = tmp_path / "hosts"
        p.write_text("0.0.0.0 zebra.com\n0.0.0.0 alpha.com\n", encoding="utf-8")
        nh, _ = NullHostsFile.from_input_file(p)
        nh.save(backup=False)
        lines = [l for l in p.read_text(encoding="utf-8").splitlines() if l.startswith("0.0.0.0")]
        assert lines[0] == "0.0.0.0 alpha.com"
        assert lines[1] == "0.0.0.0 zebra.com"

    def test_backup_preserves_original_content(self, tmp_path):
        p = tmp_path / "hosts"
        original = "0.0.0.0 zebra.com\n0.0.0.0 alpha.com\n"
        p.write_text(original, encoding="utf-8")
        bak = p.with_suffix(p.suffix + ".bak")
        nh, _ = NullHostsFile.from_input_file(p)
        nh.save(backup=True)
        assert bak.read_text(encoding="utf-8") == original


# ---------------------------------------------------------------------------
# is_changed
# ---------------------------------------------------------------------------

class TestIsChanged:
    def test_unsorted_file_is_changed(self, tmp_path):
        p = tmp_path / "hosts"
        p.write_text("0.0.0.0 zebra.com\n0.0.0.0 alpha.com\n", encoding="utf-8")
        nh, _ = NullHostsFile.from_input_file(p)
        assert nh.is_changed() is True

    def test_file_with_duplicates_is_changed(self, tmp_path):
        p = tmp_path / "hosts"
        p.write_text("0.0.0.0 alpha.com\n0.0.0.0 alpha.com\n", encoding="utf-8")
        nh, _ = NullHostsFile.from_input_file(p)
        assert nh.is_changed() is True

    def test_clean_file_not_changed(self, tmp_path):
        p = tmp_path / "hosts"
        nh_orig = NullHostsFile(header=["# Header"], hosts={"alpha.com", "beta.com"})
        p.write_text(nh_orig.render(), encoding="utf-8")
        nh, _ = NullHostsFile.from_input_file(p)
        assert nh.is_changed() is False

    def test_is_changed_raises_without_source(self):
        nh = NullHostsFile(header=[], hosts={"evil.com"})
        with pytest.raises(ValueError):
            nh.is_changed()

    def test_uppercase_entry_is_changed(self, tmp_path):
        p = tmp_path / "hosts"
        p.write_text("0.0.0.0 Evil.COM\n", encoding="utf-8")
        nh, _ = NullHostsFile.from_input_file(p)
        assert nh.is_changed() is True
