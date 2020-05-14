from kubernetes import client


class KubernetesClient:
    def __init__(self):
        loaded = load_kube_config()
        if not loaded:
            raise RuntimeError("Failed to load the kubernetes config")
        self.client = client.BatchV1Api()
