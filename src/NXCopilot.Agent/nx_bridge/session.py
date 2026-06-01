# -*- coding: utf-8 -*-
"""NXCopilot NX Bridge — NX Session 管理。"""

from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger("nxcopilot.nx_bridge.session")


class NXSession:
    """管理与 NX 实例的连接（本地 NXOpen 或远程 RemoteSession）。"""

    def __init__(self, remote_host: str = "", remote_port: int = 0):
        self._session = None
        self._remote_host = remote_host
        self._remote_port = remote_port
        self._connected = False
        self._mode = "local"

    def connect(self) -> bool:
        if self._try_local():
            return True
        if self._remote_host:
            return self._try_remote()
        return False

    def _try_local(self) -> bool:
        try:
            import NXOpen
            self._session = NXOpen.Session.GetSession()
            self._connected = True
            self._mode = "local"
            logger.info("Connected to NX (local)")
            return True
        except ImportError:
            logger.debug("NXOpen not available")
            return False
        except Exception as e:
            logger.warning(f"Local connection failed: {e}")
            return False

    def _try_remote(self) -> bool:
        try:
            import NXOpen
            self._session = NXOpen.RemoteSession(self._remote_host, self._remote_port)
            self._connected = True
            self._mode = "remote"
            return True
        except Exception as e:
            logger.error(f"Remote connection failed: {e}")
            return False

    def disconnect(self) -> None:
        self._session = None
        self._connected = False

    def is_connected(self) -> bool:
        if not self._connected or self._session is None:
            return False
        try:
            _ = self._session.Parts
            return True
        except Exception:
            self._connected = False
            return False

    @property
    def session(self):
        return self._session

    @property
    def work_part(self):
        if not self.is_connected():
            return None
        try:
            return self._session.Parts.Work
        except Exception:
            return None

    def get_part_info(self) -> dict[str, Any]:
        wp = self.work_part
        if wp is None:
            return {"connected": True, "active_part": None}
        return {
            "connected": True, "mode": self._mode,
            "active_part": wp.Name,
            "file_path": str(getattr(wp, "FullPath", "")),
        }
