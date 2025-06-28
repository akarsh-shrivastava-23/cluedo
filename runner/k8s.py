"""Helper functions for interacting with Kubernetes pods."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Iterable, List, Optional

from .exec_map import command_for_file

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


def run_script_in_pod(
    api: client.CoreV1Api,
    namespace: str,
    pod: str,
    local_path: Path,
    *,
    container: Optional[str] = None,
    artifact_dir: Path,
    timeout: int | float | None = None,
) -> int:
    """Copy ``local_path`` into the pod and execute it.

    The remote process writes ``/tmp/out_script.log`` or ``/tmp/out_mongo.log``
    and ``/tmp/status``. These files as well as anything in
    ``/tmp/artifacts`` are copied back into ``artifact_dir``.

    Returns the exit status recorded in ``/tmp/status``.
    """

    remote_path = f"/tmp/{local_path.name}"
    copy_file_to_pod(api, local_path, namespace, pod, remote_path, container=container, timeout=timeout)

    if local_path.suffix.lower() in {".mongo", ".js"}:
        out_log = "/tmp/out_mongo.log"
    else:
        out_log = "/tmp/out_script.log"

    cmd = command_for_file(Path(remote_path))
    command = " ".join(cmd) + f" > {out_log} 2>&1; echo $? > /tmp/status"
    exec_in_pod(
        api,
        namespace,
        pod,
        ["/bin/sh", "-c", command],
        container=container,
        timeout=timeout,
    )

    artifact_dir.mkdir(parents=True, exist_ok=True)
    copy_from_pod(api, namespace, pod, out_log, artifact_dir / Path(out_log).name, container=container, timeout=timeout)
    copy_from_pod(api, namespace, pod, "/tmp/status", artifact_dir / "status", container=container, timeout=timeout)

    listing = exec_in_pod(
        api,
        namespace,
        pod,
        ["/bin/sh", "-c", "if [ -d /tmp/artifacts ]; then ls -1 /tmp/artifacts; fi"],
        container=container,
        timeout=timeout,
    )
    for line in listing.splitlines():
        if not line:
            continue
        copy_from_pod(
            api,
            namespace,
            pod,
            f"/tmp/artifacts/{line}",
            artifact_dir / line,
            container=container,
            timeout=timeout,
        )

    status_text = (artifact_dir / "status").read_text().strip()
    try:
        return int(status_text)
    except ValueError:
        return 1


