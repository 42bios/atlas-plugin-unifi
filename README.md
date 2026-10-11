# Atlas UniFi connector

Read-only homelab inventory, based on the authentication and port-data patterns in [UniFi Network+](https://github.com/42bios/unifi-network-plus). No Home Assistant dependency, control commands, WebSocket monitoring or traffic statistics.

## Inventory

- UniFi switches, gateways and access points, identified by MAC.
- Switch ports, observed link speed, media and explicit native VLAN facts.
- Configured IPv4/IPv6 subnets and VLAN numbers.
- Known clients plus current WLAN associations, with SSID and access point.
- Observed client MACs on switch ports; physical patch-panel routes are never fabricated.

Configured facts are imported snapshots, not continuous monitoring. Fiber socket labels do not establish the cable type (fiber, DAC or AOC); document the cable manually. VLAN-only networks without a subnet are omitted because Atlas’s network contract requires CIDR. Port profiles, SSID configuration, LAGs and multi-site aggregation are not yet collected. API failure aborts the complete import; no partial snapshot is published.

## Install

In Atlas open **Sources & settings → Add-ins → Add GitHub repository** and enter `https://github.com/42bios/atlas-plugin-unifi`. Review the commit and confirm trust. Create a manual connector instance, choose HTTPS controller origin, site slug and controller type (`os` for UniFi OS, `classic` for a standalone Network controller). Automatic controller-type detection is intentionally avoided.

Enter private credential JSON:

```json
{"username":"LOCAL_READ_ONLY_USER","password":"YOUR_PASSWORD","ca":"OPTIONAL_PRIVATE_CA_PEM"}
```

Use a dedicated local read-only account with access to the selected site. TLS verification remains enabled; supply the trusted private CA when necessary. Cloud SSO/MFA authentication and API-key-based official integration endpoints are not implemented in this initial version. The only POST is session login; inventory endpoints use GET. Session expiry triggers one login retry.

## Status and development

Initial version 0.1.0. Ten package, collector and transport tests pass. Atlas schema validation and a complete GitHub-to-worker import were verified with separate UniFi OS and classic HTTPS fixtures, including session cookies, CSRF and trusted test certificates. **A live UniFi controller test remains pending.** No controller credentials are included here.

Run `python -m unittest discover -s tests`. After changing declared files, run `python tools/update_manifest.py` and increment the version for a release. Installed repository code runs with Atlas user permissions; checksums establish integrity, not trust or sandboxing.

Authentication compatibility follows [the source integration API](https://github.com/42bios/unifi-network-plus/blob/main/custom_components/unifi_network_plus/api.py). Network configuration fields follow [aiounifi’s network model](https://github.com/Kane610/aiounifi/blob/master/aiounifi/models/network.py). Attribution is preserved in THIRD_PARTY_NOTICES.md.

Avoid parallel connector instances importing the same devices and IPs. Atlas rejects duplicate address assignments; existing manual inventory may need reconciliation before the first live import.

Source integration reviewed at commit `29c33821b3680a4748701ac1c6f3f90ee9a19467`. Its control commands and monitoring entities were not included.
