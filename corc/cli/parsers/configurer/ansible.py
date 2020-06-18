def valid_ansible_group(parser):
    add_ansible_group(parser)


def add_ansible_group(parser):
    ansible_group = parser.add_argument_group(title="Ansible arguments")
    ansible_group.add_argument("--ansible-root-path", default=False)
    ansible_group.add_argument("--ansible-playbook-path", default=False)
    ansible_group.add_argument("--ansible-inventory-path", default=False)
