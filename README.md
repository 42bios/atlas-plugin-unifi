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

1. Open **Marketplace**, search for this connector and open its repository README.
2. Choose **Download & review**. Atlas resolves the catalog's pinned commit and verifies the declared package files before installation.
3. Review the package and its access requirements, type `42bios/atlas-plugin-unifi` to confirm trust, then install it.
4. Choose **Configure connector**. An existing system opens for editing; multiple systems produce a chooser. Create a new instance only for a different upstream system.
5. Start with **Manual imports**, enter the controller URL / discovery targets and private credential, then save.
6. Open **Sources & settings → Connected systems** and select **Test & import**. Review the imported objects before enabling a schedule.

For a private or unlisted connector, use **Sources & settings → Developer tools → Add GitHub repository**. Installing a package does not authenticate to an upstream service or start an import. Each configured system has its own stable source ID and credential. Updates retain those IDs and credentials; do not create a second collector for the same system.


Enter private credential JSON:

```json
{"username":"LOCAL_READ_ONLY_USER","password":"YOUR_PASSWORD","ca":"OPTIONAL_PRIVATE_CA_PEM"}
```

Use a dedicated local read-only account with access to the selected site. TLS verification remains enabled. Supply a trusted private CA when the certificate includes the controller hostname, or explicitly configure its SHA-256 certificate fingerprint. Pinning compares the live server certificate before any login credentials or cookies are sent; a mismatch aborts the request. Verify the fingerprint through a trusted channel before saving it. Certificate replacement requires updating the pin. Cloud SSO/MFA authentication and API-key-based official integration endpoints are not implemented in this initial version. The only POST is session login; inventory endpoints use GET. Session expiry triggers one login retry.

## Status and development

Collector and transport fixture tests cover the supported response patterns. Atlas schema validation and a complete GitHub-to-worker import were verified with separate UniFi OS and classic HTTPS fixtures, including session cookies, CSRF and trusted test certificates. **A live UniFi controller test remains pending.** No controller credentials are included here.

Run `python -m unittest discover -s tests`. After changing declared files, run `python tools/update_manifest.py` and increment the version for a release. Atlas executes each import in a separate worker container. It receives this instance’s configuration and credential and a source-scoped import token. The worker has outbound network access, but no Atlas database, other instances’ credentials or Docker socket mount. Use reviewed code and read-only upstream credentials. File checksums identify the downloaded content; they do not certify its author.

Authentication compatibility follows [the source integration API](https://github.com/42bios/unifi-network-plus/blob/main/custom_components/unifi_network_plus/api.py). Network configuration fields follow [aiounifi’s network model](https://github.com/Kane610/aiounifi/blob/master/aiounifi/models/network.py). Attribution is preserved in THIRD_PARTY_NOTICES.md.

Avoid parallel connector instances importing the same devices and IPs. Atlas rejects duplicate address assignments; existing manual inventory may need reconciliation before the first live import.

Source integration reviewed at commit `29c33821b3680a4748701ac1c6f3f90ee9a19467`. Its control commands and monitoring entities were not included.

## Validation and upgrade notes

UniFi OS and classic-controller authentication flows are fixture validated. A live controller connection has not been configured in the current Atlas environment.

This documentation release changes setup instructions and runtime descriptions. Collector behavior is unchanged. Review Marketplace updates explicitly; applying an update does not require re-entering saved credentials. Keep credentials out of repositories, issues and screenshots.
