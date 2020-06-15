.. image:: https://travis-ci.org/rasmunk/corc.svg?branch=master
    :target: https://travis-ci.org/rasmunk/corc

====
corc
====

corc is a cloud orchestration tool for managing cloud resources,
including VM's, virtual networks and container clusters.

In addition, corc provides the capability to schedule job on orchestrated resources

The current implementation only supports the `OCI <https://en.wikipedia.org/wiki/Oracle_Cloud>`_ backend.
Future plans includes expanding this to support AWS as well.

In alpha development, not ready for anything

------------
Installation
------------

Installation from pypi::

    pip install corc


Installation from local git repository::

    cd corc
    pip install .

-------------
Configuration
-------------

Depending on the selected backend cloud to utilize, corc requires that the specified provider's developer authentication mechanism is configuered on the system at hand.

For instance the OCI (Oracle Cloud Infrastructure), requires that API keys have been predefined in the specific compartment and that these are associated
with a profile in a valid oci configuration. See (https://docs.cloud.oracle.com/en-us/iaas/Content/API/Concepts/devguidesetupprereq.htm)

In addition, if utilizing the S3 storage feature, corc expects that there similarly is a valid S3 configuration.
For more information on this, see (https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)


-----
Usage
-----

As mentioned, corc is a command-line tool for managing cloud resources, such instantiating VM instances or Kubernetes Clusters or scheduling jobs on said clusters.

The available options can be discovered through the CLI itself, e.g::

    corc -h
    usage: corc [-h] [--oci-profile-name OCI_PROFILE_NAME]
                [--oci-compartment-id OCI_COMPARTMENT_ID]
                {OCI} {instance,cluster,job} ...

    optional arguments:
    -h, --help            show this help message and exit

    Available Platforms:
    {OCI}

    OCI arguments:
    --oci-profile-name OCI_PROFILE_NAME
    --oci-compartment-id OCI_COMPARTMENT_ID

    COMMAND:
    {instance,cluster,job}

As show above, the first thing that is specified is which of the `Available Platforms` is the target of the specified `COMMAND`.
Expanding on this, the `cluster` command provides the following functionalities::

    corc OCI cluster -h
    usage: corc {OCI} cluster [-h] {start,stop,list,update} ...

    optional arguments:
    -h, --help            show this help message and exit

    Commands:
    {start,stop,list,update}

A cluster currently only means a Kubernetes Cluster created from a specified set of VM nodes.
On a cluster, you can submit jobs via the `job` command::

    corc OCI job -h
    usage: corc {OCI} job [-h] {run,result} ...

    optional arguments:
    -h, --help    show this help message and exit

    Commands:
    {run,result}



**Note**, corc is still very much in early development, therefore not every command and option will run as expected.
