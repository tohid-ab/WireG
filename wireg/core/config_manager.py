import configparser
import io
import json
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from ..utils.paths import get_configs_json_path, ensure_directories
from ..utils.validator import validate_config_dict


@dataclass
class WireGuardConfig:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New WireGuard Config"
    interface: Dict[str, str] = field(default_factory=dict)
    peer: Dict[str, str] = field(default_factory=dict)
    is_favorite: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_connected_at: Optional[str] = None
    last_ping: Optional[float] = None
    last_ping_status: str = "untested"  # "ok", "high", "timeout", "error", "untested"
    notes: str = ""

    def to_conf_str(self) -> str:
        """Converts config data to standard WireGuard INI .conf string."""
        lines = ["[Interface]"]
        
        # Interface ordered keys
        order_iface = ["PrivateKey", "Address", "DNS", "ListenPort", "MTU", "PostUp", "PostDown", "PreUp", "PreDown"]
        for k in order_iface:
            if k in self.interface and self.interface[k]:
                lines.append(f"{k} = {self.interface[k]}")
        for k, v in self.interface.items():
            if k not in order_iface and v:
                lines.append(f"{k} = {v}")

        lines.append("")
        lines.append("[Peer]")
        order_peer = ["PublicKey", "PresharedKey", "AllowedIPs", "Endpoint", "PersistentKeepalive"]
        for k in order_peer:
            if k in self.peer and self.peer[k]:
                lines.append(f"{k} = {self.peer[k]}")
        for k, v in self.peer.items():
            if k not in order_peer and v:
                lines.append(f"{k} = {v}")

        return "\n".join(lines) + "\n"

    @classmethod
    def from_conf_str(cls, conf_str: str, name: Optional[str] = None, config_id: Optional[str] = None) -> "WireGuardConfig":
        """Parses a WireGuard .conf INI formatted string."""
        parser = configparser.RawConfigParser(strict=False)
        # Wireguard keys are case-sensitive
        parser.optionxform = lambda option: option  # type: ignore

        # Clean comments or prepended metadata
        clean_lines = []
        inferred_name = None
        for line in conf_str.splitlines():
            sline = line.strip()
            if sline.startswith("# Name:") or sline.startswith("# name:"):
                inferred_name = sline.split(":", 1)[1].strip()
            clean_lines.append(line)

        try:
            parser.read_file(io.StringIO("\n".join(clean_lines)))
        except Exception as e:
            raise ValueError(f"Invalid WireGuard configuration file format: {e}")

        interface_data: Dict[str, str] = {}
        peer_data: Dict[str, str] = {}

        for sec in parser.sections():
            sec_lower = sec.lower()
            if sec_lower == "interface":
                for k, v in parser.items(sec):
                    interface_data[k] = v
            elif sec_lower == "peer":
                for k, v in parser.items(sec):
                    peer_data[k] = v

        if not interface_data and not peer_data:
            raise ValueError("Configuration must contain at least [Interface] or [Peer] section")

        final_name = name or inferred_name or "WireGuard Tunnel"
        cid = config_id or str(uuid.uuid4())

        return cls(
            id=cid,
            name=final_name,
            interface=interface_data,
            peer=peer_data,
        )

    def get_endpoint_host_and_port(self) -> Tuple[Optional[str], Optional[int]]:
        """Returns (host, port) from peer Endpoint."""
        ep = self.peer.get("Endpoint", "").strip()
        if not ep:
            return None, None
        if ep.startswith("["):
            # IPv6
            parts = ep.split("]:")
            if len(parts) == 2:
                host = parts[0].lstrip("[")
                try:
                    return host, int(parts[1])
                except ValueError:
                    return host, 51820
        else:
            parts = ep.rsplit(":", 1)
            if len(parts) == 2:
                try:
                    return parts[0], int(parts[1])
                except ValueError:
                    return parts[0], 51820
            return parts[0], 51820
        return None, None

    def get_dns_server(self) -> Optional[str]:
        """Returns primary DNS server configured in Interface."""
        dns = self.interface.get("DNS", "").strip()
        if dns:
            return dns.split(",")[0].strip()
        return None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "WireGuardConfig":
        return cls(
            id=d.get("id", str(uuid.uuid4())),
            name=d.get("name", "Untitled Config"),
            interface=d.get("interface", {}),
            peer=d.get("peer", {}),
            is_favorite=d.get("is_favorite", False),
            created_at=d.get("created_at", datetime.now().isoformat()),
            last_connected_at=d.get("last_connected_at"),
            last_ping=d.get("last_ping"),
            last_ping_status=d.get("last_ping_status", "untested"),
            notes=d.get("notes", ""),
        )


class ConfigManager:
    """Manages collection of WireGuard configurations persisted in JSON."""

    def __init__(self, json_path: Optional[Path] = None):
        ensure_directories()
        self.json_path = json_path or get_configs_json_path()
        self.configs: Dict[str, WireGuardConfig] = {}
        self.load()

    def load(self) -> None:
        """Loads configurations from JSON file."""
        if not self.json_path.exists():
            self.configs = {}
            return
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.configs = {
                    item["id"]: WireGuardConfig.from_dict(item)
                    for item in data
                    if "id" in item
                }
        except Exception as e:
            print(f"Error loading configs from {self.json_path}: {e}")
            self.configs = {}

    def save(self) -> None:
        """Atomically saves all configs to JSON file."""
        ensure_directories()
        temp_path = self.json_path.with_suffix(".tmp")
        data = [cfg.to_dict() for cfg in self.configs.values()]
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, self.json_path)
            # Secure file permissions (rw-------)
            os.chmod(self.json_path, 0o600)
        except Exception as e:
            print(f"Error saving configs to {self.json_path}: {e}")
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)

    def get_all(self) -> List[WireGuardConfig]:
        return list(self.configs.values())

    def get_by_id(self, config_id: str) -> Optional[WireGuardConfig]:
        return self.configs.get(config_id)

    def add(self, config: WireGuardConfig) -> None:
        self.configs[config.id] = config
        self.save()

    def update(self, config: WireGuardConfig) -> None:
        self.configs[config.id] = config
        self.save()

    def delete(self, config_id: str) -> bool:
        if config_id in self.configs:
            del self.configs[config_id]
            self.save()
            return True
        return False

    def duplicate(self, config_id: str) -> Optional[WireGuardConfig]:
        orig = self.get_by_id(config_id)
        if not orig:
            return None
        new_cfg = WireGuardConfig(
            name=f"{orig.name} (Copy)",
            interface=dict(orig.interface),
            peer=dict(orig.peer),
            notes=orig.notes,
        )
        self.add(new_cfg)
        return new_cfg

    def toggle_favorite(self, config_id: str) -> bool:
        cfg = self.get_by_id(config_id)
        if cfg:
            cfg.is_favorite = not cfg.is_favorite
            self.save()
            return cfg.is_favorite
        return False

    def update_ping_result(self, config_id: str, ping_ms: Optional[float], status: str) -> None:
        cfg = self.get_by_id(config_id)
        if cfg:
            cfg.last_ping = ping_ms
            cfg.last_ping_status = status
            self.save()

    def update_last_connected(self, config_id: str) -> None:
        cfg = self.get_by_id(config_id)
        if cfg:
            cfg.last_connected_at = datetime.now().isoformat()
            self.save()

    def import_from_file(self, file_path: str, custom_name: Optional[str] = None) -> WireGuardConfig:
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        content = p.read_text(encoding="utf-8", errors="replace")
        default_name = custom_name or p.stem
        cfg = WireGuardConfig.from_conf_str(content, name=default_name)
        self.add(cfg)
        return cfg

    def export_to_file(self, config_id: str, target_path: str) -> bool:
        cfg = self.get_by_id(config_id)
        if not cfg:
            return False
        p = Path(target_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(cfg.to_conf_str(), encoding="utf-8")
        os.chmod(target_path, 0o600)
        return True

    def search_and_sort(
        self,
        query: str = "",
        sort_by: str = "name_asc",
        favorites_first: bool = True
    ) -> List[WireGuardConfig]:
        """
        Filters by query and sorts items.
        sort_by options:
          - 'name_asc', 'name_desc'
          - 'ping_asc', 'ping_desc'
          - 'last_connected'
          - 'created_at'
        """
        items = list(self.configs.values())
        query = query.strip().lower()

        if query:
            filtered = []
            for c in items:
                ep = c.peer.get("Endpoint", "").lower()
                addr = c.interface.get("Address", "").lower()
                if (
                    query in c.name.lower()
                    or query in ep
                    or query in addr
                    or query in c.notes.lower()
                ):
                    filtered.append(c)
            items = filtered

        def sort_key(cfg: WireGuardConfig):
            # Favorites first
            fav_rank = 0 if (favorites_first and cfg.is_favorite) else 1

            if sort_by == "name_asc":
                return (fav_rank, cfg.name.lower())
            elif sort_by == "name_desc":
                # For descending string, invert ranking by tuple
                return (fav_rank, -1, cfg.name.lower())
            elif sort_by == "ping_asc":
                # Put valid pings first, then timeouts/errors
                p = cfg.last_ping if (cfg.last_ping is not None and cfg.last_ping_status == "ok") else 999999
                return (fav_rank, p)
            elif sort_by == "ping_desc":
                p = cfg.last_ping if (cfg.last_ping is not None and cfg.last_ping_status == "ok") else -1
                return (fav_rank, -p)
            elif sort_by == "last_connected":
                ts = cfg.last_connected_at or ""
                return (fav_rank, ts)
            elif sort_by == "created_at":
                return (fav_rank, cfg.created_at)
            return (fav_rank, cfg.name.lower())

        reverse = sort_by in ["name_desc", "last_connected", "created_at"]
        if sort_by == "name_desc":
            items.sort(key=lambda x: (0 if (favorites_first and x.is_favorite) else 1, x.name.lower()), reverse=True)
            if favorites_first:
                items.sort(key=lambda x: 0 if x.is_favorite else 1)
        elif sort_by in ["last_connected", "created_at"]:
            items.sort(key=lambda x: getattr(x, sort_by) or "", reverse=True)
            if favorites_first:
                items.sort(key=lambda x: 0 if x.is_favorite else 1)
        else:
            items.sort(key=sort_key)

        return items
