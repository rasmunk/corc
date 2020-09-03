from kubernetes import client
from corc.schedulers.kubernetes.config import load_kube_config

ROUND_ROBIN = "ROUND_ROBIN"


def list_nodes(api_instance, **kwargs):
    # Can accept label selector
    return api_instance.list_node(**kwargs)


class NodeManager:
    def __init__(self):
        loaded = load_kube_config()
        if not loaded:
            raise RuntimeError("Failed to load the kubernetes config")
        self.client = client.CoreV1Api()

        self.nodes = []
        self.last_selected_index = 0

    def discover(self, **kwargs):
        nodes_response = list_nodes(self.client, **kwargs)
        if nodes_response.items:
            self.nodes = nodes_response.items
            return True
        return False

    def _select_round_robin(self):
        if not self.nodes:
            return None

        if (self.last_selected_index + 1) < len(self.nodes):
            next_index = self.last_selected_index + 1
            selected = self.nodes[next_index]
            self.last_selected_index = next_index
            return selected
        else:
            # Back to the start
            next_index = 0
            selected = self.nodes[next_index]
            self.last_selected_index = next_index
            return selected
        return None

    def select(self, selection_type=ROUND_ROBIN):
        if not self.nodes:
            return None

        if selection_type == ROUND_ROBIN:
            return self._select_round_robin()
        return None
