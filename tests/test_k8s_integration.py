"""Integration tests for Kubernetes helper functions."""

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

# Ensure the parent directory is on the Python path so ``runner`` can be imported
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

pytest.importorskip("kubernetes", reason="kubernetes package required")
from kubernetes import client, config

from runner.k8s import (
    copy_file_to_pod,
    copy_from_pod,
    ensure_context,
    exec_in_pod,
    run_script_in_pod,
)


@pytest.mark.skipif(os.environ.get("CI") == "true", reason="kind not available in CI")
def test_copy_and_exec(tmp_path: Path) -> None:
    """Create a kind cluster and verify copy/exec helpers."""
    if shutil.which("kind") is None:
        pytest.skip("kind binary not found")
    if shutil.which("kubectl") is None:
        pytest.skip("kubectl binary not found")

    cluster_name = "runner-test"
    subprocess.run(["kind", "create", "cluster", "--name", cluster_name], check=True)
    try:
        api = ensure_context(f"kind-{cluster_name}")
        pod_manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": "helper"},
            "spec": {
                "containers": [
                    {"name": "bb", "image": "busybox", "command": ["sleep", "3600"]}
                ],
                "restartPolicy": "Never",
            },
        }
        api.create_namespaced_pod(namespace="default", body=pod_manifest)
        for _ in range(60):
            pod = api.read_namespaced_pod("helper", "default")
            if pod.status.phase == "Running":
                break
            time.sleep(1)
        else:
            raise RuntimeError("pod did not start")

        local_file = tmp_path / "foo.txt"
        local_file.write_text("hello")
        copy_file_to_pod(api, local_file, "default", "helper", "/tmp/foo.txt")
        assert exec_in_pod(api, "default", "helper", ["echo", "ok"]).strip() == "ok"
        out_file = tmp_path / "bar.txt"
        copy_from_pod(api, "default", "helper", "/tmp/foo.txt", out_file)
        assert out_file.read_text() == "hello"
    finally:
        subprocess.run(["kind", "delete", "cluster", "--name", cluster_name], check=False)


@pytest.mark.skipif(os.environ.get("CI") == "true", reason="kind not available in CI")
def test_run_workflow(tmp_path: Path) -> None:
    """Verify full run workflow including artifact collection."""
    if shutil.which("kind") is None:
        pytest.skip("kind binary not found")
    if shutil.which("kubectl") is None:
        pytest.skip("kubectl binary not found")

    cluster_name = "runner-test"
    subprocess.run(["kind", "create", "cluster", "--name", cluster_name], check=True)
    try:
        api = ensure_context(f"kind-{cluster_name}")
        pod_manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": "helper"},
            "spec": {
                "containers": [
                    {"name": "bb", "image": "busybox", "command": ["sleep", "3600"]}
                ],
                "restartPolicy": "Never",
            },
        }
        api.create_namespaced_pod(namespace="default", body=pod_manifest)
        for _ in range(60):
            pod = api.read_namespaced_pod("helper", "default")
            if pod.status.phase == "Running":
                break
            time.sleep(1)
        else:
            raise RuntimeError("pod did not start")

        script = tmp_path / "hi.sh"
        script.write_text("echo hi")
        art_dir = tmp_path / "artifacts"
        exit_code = run_script_in_pod(api, "default", "helper", script, artifact_dir=art_dir)
        assert exit_code == 0
        assert (art_dir / "out_script.log").read_text().strip() == "hi"
        assert (art_dir / "status").read_text().strip() == "0"
    finally:
        subprocess.run(["kind", "delete", "cluster", "--name", cluster_name], check=False)

