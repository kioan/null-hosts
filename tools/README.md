# hostscrub

A Python utility for maintaining the `hosts` blocklist file. It validates FQDN entries, removes duplicates (including case-insensitive ones), sorts entries alphabetically, and normalizes formatting.

## Requirements

- Python 3.10+
- No external dependencies for normal use
- `pytest` for running tests (optional)

## Usage

Run from the `tools/` directory.

### Process a file in-place

Normalizes the file and overwrites it. A `.bak` backup is created automatically.

```bash
python -m hostscrub ../hosts
```

### Write output to a separate file

```bash
python -m hostscrub ../hosts -o ../hosts.clean
```

### Skip the backup

```bash
python -m hostscrub ../hosts --no-backup
```

### Check mode (no writes)

Exits with code `0` if the file is already clean, or `1` if it needs processing. Does not modify anything.

```bash
python -m hostscrub ../hosts --check
```

Useful as a pre-commit check — see [Git hook](#git-pre-commit-hook) below.

## Options

| Option           | Description                                                |
| ---------------- | ---------------------------------------------------------- |
| `filename`       | Path to the hosts file (required)                          |
| `-o`, `--output` | Write output to this file instead of overwriting the input |
| `--check`        | Check only — exit 1 if changes are needed, exit 0 if clean |
| `--no-backup`    | Skip creating a `.bak` backup when writing in-place        |

## What it does

- **Validates** each entry: must be in the form `0.0.0.0 <fqdn>` where the FQDN has at least two labels and follows RFC syntax
- **Removes** invalid or malformed lines
- **Deduplicates**: case-insensitive (e.g. `Evil.COM` and `evil.com` are treated as the same entry)
- **Normalizes** hostnames to lowercase and strips trailing dots
- **Sorts** all entries alphabetically
- **Normalizes** comment formatting

## Git pre-commit hook

To prevent pushing an unprocessed file, create `.git/hooks/pre-commit` in the repository root:

```bash
#!/bin/sh
cd tools && python -m hostscrub ../hosts --check
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

If the file needs processing, the commit will be blocked. Run `python -m hostscrub ../hosts` to fix it, then commit again.

## Running tests

From the `tools/` directory:

```bash
python -m pytest
```

Or with verbose output:

```bash
python -m pytest -v
```
