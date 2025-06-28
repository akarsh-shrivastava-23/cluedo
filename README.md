# k8s-script-runner

This project provides a small CLI for executing scripts either locally or in an
existing Kubernetes pod. When running inside a pod the command output and exit
status are written to temporary files in the pod and then copied back to the
local machine.

## Local execution

```bash
k8s-script-runner run --script-file ./hello.py
```

## Running inside a pod

Specify the pod (and optionally namespace or container) together with an
artifact directory. After the script finishes the files `out_script.log` or
`out_mongo.log`, `status` and anything found in `/tmp/artifacts` in the pod are
downloaded into the given directory. The CLI exits with the status code written
by the remote command.

```bash
k8s-script-runner run --script-file ./hello.sh \
    --pod my-helper --namespace default --artifact-dir ./artifacts
```

## Integration test

The integration tests require the `kind` and `kubectl` binaries as well as the
Python `kubernetes` package. To run the tests manually:

```bash
pip install kubernetes
pytest tests/test_k8s_integration.py -q
```

The tests will create a temporary kind cluster and remove it when finished.

