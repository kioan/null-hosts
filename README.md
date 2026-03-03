# Malicious Domain Blocklist

This repository contains a `hosts` file that is a curated list of fully qualified domain names (FQDNs) associated with malicious activity, including phishing attempts, malware distribution, and other harmful online behavior.

Domains are sourced from phishing emails, web access logs, and other suspicious activity reports.

---

## How to Use

Each entry uses `0.0.0.0` as the null route address, which causes DNS resolution to fail silently for the blocked domain. This format is compatible with both Pi-hole and standard `/etc/hosts` usage.

### Pi-hole

Add the raw URL of the `hosts` file as a custom blocklist:

1. Go to **Pi-hole admin** → **Group Management** → **Adlists**
2. Add the following URL:
   ```
   https://raw.githubusercontent.com/kioan/null-hosts/main/hosts
   ```
3. Run `pihole -g` (or use **Tools → Update Gravity** in the admin panel) to apply the changes.

### /etc/hosts

Append the contents of the `hosts` file to your system's `/etc/hosts`:

```bash
curl -s https://raw.githubusercontent.com/kioan/null-hosts/main/hosts >> /etc/hosts
```

Note: editing `/etc/hosts` typically requires root privileges (`sudo`).

---

## How to Contribute

If you would like to propose a domain to be added to the list, please open an [issue](https://github.com/kioan/null-hosts/issues) with the domain details and, if possible, a brief description of the associated malicious activity.

### False Positives

If you encounter a domain in the list that you believe to be a false positive, please open an [issue](https://github.com/kioan/null-hosts/issues). Accurate listings are a priority and your feedback is valuable.

---

## Tools

The [`tools/`](tools/) directory contains **hostscrub**, a Python utility used to maintain the `hosts` file. It removes duplicate entries, sorts them alphabetically, validates FQDNs, and normalizes formatting before each commit.

See [tools/README.md](tools/README.md) for usage details.

---

## Related Projects

For a more comprehensive collection of hosts files covering thousands of malicious domains from multiple sources, see the [StevenBlack/hosts project](https://github.com/StevenBlack/hosts).

---

## Notes

- This list is primarily intended for use with Pi-hole or other DNS-level blocking solutions.
- The list is regularly updated based on new findings and contributions.
