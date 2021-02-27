import random
from kubernetes import client
from corc.schedulers.kubernetes.config import load_kube_config

ROUND_ROBIN = "ROUND_ROBIN"
RANDOM = "RANDOM"


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
        return None

    def _select_random(self):
        if not self.nodes:
            return None

        num_nodes = len(self.nodes)
        if num_nodes > 0:
            if num_nodes == 1:
                selected_index = 0
                self.last_selected_index = selected_index
            else:
                selected_index = random.randint(0, num_nodes - 1)
                self.last_selected_index = selected_index

            selected = self.nodes[self.last_selected_index]
            return selected
        return None

    def select(self, selection_type=RANDOM):
        if not self.nodes:
            return None

        if selection_type == ROUND_ROBIN:
            return self._select_round_robin()

        if selection_type == RANDOM:
            return self._select_random()
        return None
