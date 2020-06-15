def valid_node_group(parser):
    add_node_group(parser)
    select_node_group(parser)


def select_node_group(parser):
    node_group = parser.add_argument_group(title="Node Selection arguments")
    node = node_group.add_mutually_exclusive_group(required=True)
    node.add_argument("--node-id", default="")
    node.add_argument("--node-name", default="NodePool")


def add_node_group(parser):
    node_group = parser.add_argument_group(title="Node arguments")
    node_group.add_argument("--node-availability-domain", default="", required=True)
    node_group.add_argument("--node-size", default=1, type=int)
    node_group.add_argument("--node-shape", default="VM.Standard2.1")
    # https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/api/cims/models/oci.cims.models.CreateResourceDetails.html?highlight=availability_domain#oci.cims.models.CreateResourceDetails.availability_domain
    node_group.add_argument("--node-image", default="Oracle-Linux-7.7-2020.03.23-0")
