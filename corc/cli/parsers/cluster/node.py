def valid_node_group(parser):
    add_node_group(parser)
    select_node_group(parser)


def select_node_group(parser):
    node_group = parser.add_argument_group(title="Node Selection arguments")
    node_group.add_argument("--node-id", default="")
    node_group.add_argument("--node-name", default="")


def add_node_group(parser):
    node_group = parser.add_argument_group(title="Node arguments")
    node_group.add_argument("--node-availability-domain", default="")
    node_group.add_argument("--node-size", type=int)
    node_group.add_argument("--node-shape", default="")
    # https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/api/cims/models/oci.cims.models.CreateResourceDetails.html?highlight=availability_domain#oci.cims.models.CreateResourceDetails.availability_domain
    node_group.add_argument("--node-image", default="")
