.. image:: https://travis-ci.org/rasmunk/corc.svg?branch=master
    :target: https://travis-ci.org/rasmunk/corc

====
corc
====

**Note**, corc is still very much in early development, therefore not every command and option will run as expected.

corc is a cloud orchestration tool for managing cloud resources,
including VM's, virtual networks and container clusters.

In addition, corc provides the capability to schedule job on orchestrated resources

The current implementation only supports the `OCI <https://en.wikipedia.org/wiki/Oracle_Cloud>`_ backend.
Future plans includes expanding this to support AWS as well.

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

    usage: corc [-h] {config,aws,oci} ...

    optional arguments:
      -h, --help        show this help message and exit

    COMMAND:
      {config,aws,oci}

A good start is to first generate the corc configuration. Afterwards the provider specific details such as the OCI ``compartment_id`` should be filled into this.
By default the corc configuration is placed into the ``~/.corc/config`` file. Currently OCI is the only supported provider, which means that this is also the only provider that will be put into the configuration file.

The specific values can be overwritten during the config generation, details about this can be displayed via ``corc config oci generate -h``.

---------------
Getting Started
---------------

To start utilizing the OCI provider, corc requires that the authentication details for this provider is first defined via the default ``~/.oci/config`` as defined by OCI. In addition, `corc` needs to know which `compartment` to operate the given task on. This is defined via the ``corc.providers.oci.profile.compartment_id`` configuration variable.

After these steps have been fulfilled, corc is ready to either orchestrate resources or schedule tasks/jobs on the providers infrastructure.

For instance, the following command orchestrates a Kubernetes cluster called ``cluster`` at OCI with 5 nodes::

    :~# corc oci orchestration cluster start --cluster-node-size 5

After this is completed, a simple hello world job can be schduled straight after::

    # Schedule the job
    :~# corc oci job run --storage-enable "/bin/echo Hello World"
    {
        "job": {
            "id": "job-1594378280"
        },
        "msg": "Job submitted",
        "status": "success"
    }

    # Retrieve the results
    :~# corc oci job result get --job-meta-name job-1594378280
    
Which will download the generated content available in the default output directory ``/tmp/output`` in the execution environment.
This by default includes a ``job`` description file that details what command was executed and how it went.

The ``get`` COMMAND will unless otherwise specified, download the job output into the current directory with the ``job-name`` as the prefix, and a automatically unique generated postfix string. The ``corc oci job result get --job-meta-name job-15943782`` for instance produced a local directory called ``job-1594378280-mgjb2`` that contains the job output file.

