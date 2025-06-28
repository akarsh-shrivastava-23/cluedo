"""Helper functions for interacting with Kubernetes pods."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Iterable, List, Optional

from kubernetes import client, config
from kubernetes.stream import stream


class RunnerTimeoutError(RuntimeError):
    """Raised when a Kubernetes operation exceeds the given timeout."""


def ensure_context(context: Optional[str] = None) -> client.CoreV1Api:
    """Load Kubernetes configuration and return a CoreV1Api instance."""
    try:
        config.load_kube_config(context=context)
    except config.ConfigException:
        config.load_incluster_config()
    return client.CoreV1Api()


def exec_in_pod(
    api: client.CoreV1Api,
    namespace: str,
    pod: str,
    command: Iterable[str],
    *,
    container: Optional[str] = None,
    timeout: int | float | None = None,
) -> str:
    """Execute a command in the specified pod and return stdout."""
    try:
        return stream(
            api.connect_get_namespaced_pod_exec,
            pod,
            namespace,
            command=list(command),
            container=container,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
            _request_timeout=timeout,
        )
    except Exception as exc:  # pragma: no cover - passthrough for API errors
        if "timed out" in str(exc).lower():
            raise RunnerTimeoutError(str(exc)) from exc
        raise


def copy_file_to_pod(
    api: client.CoreV1Api,
    src: Path,
    namespace: str,
    pod: str,
    dest: str,
    *,
    container: Optional[str] = None,
    timeout: int | float | None = None,
) -> None:
    """Copy a local file into the pod."""
    data = src.read_bytes()
    encoded = base64.b64encode(data).decode()
    command = ["/bin/sh", "-c", f"base64 -d > {dest}"]
    try:
        resp = stream(
            api.connect_get_namespaced_pod_exec,
            pod,
            namespace,
            command=command,
            container=container,
            stderr=True,
            stdin=True,
            stdout=True,
            tty=False,
            _preload_content=False,
            _request_timeout=timeout,
        )
        resp.write_stdin(encoded)
        resp.close()
    except Exception as exc:  # pragma: no cover - passthrough for API errors
        if "timed out" in str(exc).lower():
            raise RunnerTimeoutError(str(exc)) from exc
        raise


def copy_from_pod(
    api: client.CoreV1Api,
    namespace: str,
    pod: str,
    src: str,
    dest: Path,
    *,
    container: Optional[str] = None,
    timeout: int | float | None = None,
) -> None:
    """Copy a file from the pod to the local filesystem."""
    command = ["/bin/sh", "-c", f"base64 {src}"]
    try:
        encoded = stream(
            api.connect_get_namespaced_pod_exec,
            pod,
            namespace,
            command=command,
            container=container,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
            _request_timeout=timeout,
        )
    except Exception as exc:  # pragma: no cover - passthrough for API errors
        if "timed out" in str(exc).lower():
            raise RunnerTimeoutError(str(exc)) from exc
        raise
    data = base64.b64decode(encoded)
    dest.write_bytes(data)

