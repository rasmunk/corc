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

from corc.core.defaults import PROFILE, CLUSTER
from corc.cli.parsers.providers.ec2.cluster import (
    start_cluster_group,
    cluster_identity_group,
)


def start_cluster_groups(parser):
    start_cluster_group(parser)

    provider_groups = [PROFILE]
    argument_groups = [
        CLUSTER,
    ]
    return provider_groups, argument_groups


def stop_cluster_groups(parser):
    cluster_identity_group(parser)

    provider_groups = [PROFILE]
    argument_groups = [CLUSTER]
    return provider_groups, argument_groups


def get_cluster_groups(parser):
    cluster_identity_group(parser)

    provider_groups = [PROFILE]
    argument_groups = [CLUSTER]
    return provider_groups, argument_groups


def list_cluster_groups(parser):
    return [PROFILE], []
