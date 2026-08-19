import base64
import ipaddress
import re
from typing import List, Tuple, Optional


def validate_base64_key(key: str) -> bool:
    """Validates if key is a 32-byte base64 encoded WireGuard key (44 chars)."""
    if not key or not isinstance(key, str):
        return False
    key = key.strip()
    if len(key) != 44:
        return False
    try:
        decoded = base64.b64decode(key)
        return len(decoded) == 32
    except Exception:
        return False


def validate_endpoint(endpoint: str) -> Tuple[bool, Optional[str]]:
    """Validates Endpoint in format host:port or [ipv6]:port."""
    if not endpoint or not isinstance(endpoint, str):
        return False, "Endpoint cannot be empty"
    endpoint = endpoint.strip()
    
    # Check for IPv6 format: [2001:db8::1]:51820
    if endpoint.startswith("["):
        m = re.match(r"^\[([a-fA-F0-9:]+)\]:(\d+)$", endpoint)
        if not m:
            return False, "Invalid IPv6 endpoint format. Use [ipv6]:port"
        host, port_s = m.group(1), m.group(2)
    else:
        parts = endpoint.rsplit(":", 1)
        if len(parts) != 2:
            return False, "Endpoint must be in format host:port"
        host, port_s = parts[0], parts[1]

    if not host:
        return False, "Endpoint host is empty"

    try:
        port = int(port_s)
        if not (1 <= port <= 65535):
            return False, "Port must be between 1 and 65535"
    except ValueError:
        return False, "Invalid port number in endpoint"

    # Host can be an IPv4, IPv6, or domain/hostname
    try:
        ipaddress.ip_address(host)
        return True, None
    except ValueError:
        # Domain / hostname check
        if re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?$", host):
            return True, None
        return False, "Invalid hostname/domain in endpoint"


def validate_cidr_list(cidr_str: str) -> Tuple[bool, Optional[str]]:
    """Validates comma-separated list of IP CIDRs (e.g. 10.0.0.2/32, fd00::2/128)."""
    if not cidr_str or not isinstance(cidr_str, str):
        return False, "IP address list is empty"
    items = [x.strip() for x in cidr_str.split(",") if x.strip()]
    if not items:
        return False, "No valid IP addresses provided"
    for item in items:
        try:
            ipaddress.ip_network(item, strict=False)
        except ValueError:
            # Check if plain IP provided without subnet, which is often accepted
            try:
                ipaddress.ip_address(item)
            except ValueError:
                return False, f"Invalid IP/CIDR: '{item}'"
    return True, None


def validate_config_dict(cfg: dict) -> Tuple[bool, List[str]]:
    """
    Validates a WireGuard configuration dictionary.
    Returns (is_valid, list_of_errors).
    """
    errors: List[str] = []
    
    # Validate Interface
    interface = cfg.get("interface", {})
    private_key = interface.get("PrivateKey", "").strip()
    if not private_key:
        errors.append("Interface: PrivateKey is required")
    elif not validate_base64_key(private_key):
        errors.append("Interface: PrivateKey must be a valid 44-character base64 string")

    address = interface.get("Address", "").strip()
    if not address:
        errors.append("Interface: Address is required")
    else:
        valid_addr, err = validate_cidr_list(address)
        if not valid_addr:
            errors.append(f"Interface: {err}")

    # Validate Peer
    peer = cfg.get("peer", {})
    public_key = peer.get("PublicKey", "").strip()
    if not public_key:
        errors.append("Peer: PublicKey is required")
    elif not validate_base64_key(public_key):
        errors.append("Peer: PublicKey must be a valid 44-character base64 string")

    endpoint = peer.get("Endpoint", "").strip()
    if endpoint:
        valid_ep, err = validate_endpoint(endpoint)
        if not valid_ep:
            errors.append(f"Peer: {err}")

    allowed_ips = peer.get("AllowedIPs", "").strip()
    if allowed_ips:
        valid_aips, err = validate_cidr_list(allowed_ips)
        if not valid_aips:
            errors.append(f"Peer AllowedIPs: {err}")

    keepalive = peer.get("PersistentKeepalive", "")
    if keepalive:
        try:
            val = int(str(keepalive).strip())
            if val < 0:
                errors.append("Peer: PersistentKeepalive must be >= 0")
        except ValueError:
            errors.append("Peer: PersistentKeepalive must be an integer")

    return len(errors) == 0, errors
