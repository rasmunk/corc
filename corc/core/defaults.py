# Copyright (C) 2024  rasmunk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os

# Package name
PACKAGE_NAME = "corc"

PROVIDER = "provider"

# Profile group defaults
PROFILE = "profile"
DRIVER = "driver"
PROFILE_DRIVER = "{}_{}".format(PROFILE, DRIVER)

# Argument group defaults
ANSIBLE = "ansible"
CLUSTER = "cluster"
NODE = "node"
CLUSTER_NODE = "{}_{}".format(CLUSTER, NODE)
INSTANCE = "instance"
CONFIG = "config"
JOB = "job"
META = "meta"
JOB_META = "{}_{}".format(JOB, META)
RUN = "run"

STORAGE = "storage"

# To get extra information about an entity
DETAILS = "details"

CONFIGURER = "configurer"
CONFIGURER_OPERATIONS = ["add_provider", "remove_provider"]
CONFIGURER_CLI = {CONFIGURER: CONFIGURER_OPERATIONS}

POOL = "pool"
POOL_OPERATIONS = ["create", "remove", "show", "ls", "add_instance", "remove_instance"]
POOL_CLI = {POOL: POOL_OPERATIONS}

PERSISTENCE = "persistence"

STACK = "stack"
STACK_OPERATIONS = [
    "create",
    "remove",
    "update",
    "show",
    "ls",
    "deploy",
    "destroy",
]
STACK_CLI = {STACK: STACK_OPERATIONS}

SWARM = "swarm"
SWARM_OPERATIONS = [
    "create",
    "remove",
    "update",
    "show",
    "sync",
    "ls",
]
SWARM_CLI = {SWARM: SWARM_OPERATIONS}

ORCHESTRATION = "orchestration"
ORCHESTRATION_OPERATIONS = [
    "add_provider",
    "remove_provider",
    "list_providers",
    POOL_CLI,
]
ORCHESTRATION_CLI = {ORCHESTRATION: ORCHESTRATION_OPERATIONS}

# List of functionality that corc supports
CORC_CLI_STRUCTURE = [CONFIGURER_CLI, ORCHESTRATION_CLI, STACK_CLI, SWARM_CLI]

# Default state directory
default_base_path = os.path.join(os.path.expanduser("~"), ".{}".format(PACKAGE_NAME))

# Default persistence directory
default_persistence_path = os.path.join(default_base_path, PERSISTENCE)
