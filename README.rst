====
corc
====
.. image:: https://badge.fury.io/py/corc.svg
    :target: https://badge.fury.io/py/corc

**Note**, corc is a small project that is currently under development for providing a set of tools for managing infrastructure components.

corc is a tool for conducting a range of operations for managing infrastructure components via a set of supported providers.
Each provider is defined as a seperate plugin that can be installed and utilized by corc.
The list of components that corc exposes are:

- Configurer
- Compute
- Orchestration
- Storage

Currently, the set of plugins/providers is very limited, and the initial development is focused on the area of
orchestration and the associated `libvirt_provider` plugin.

However, plugin/provider contributions for each of these components are very welcome.

------------
Installation
------------

Installation from pypi::

    pip install corc


Installation from local git repository::

    cd corc
    pip install .


If you have cloned the repo, an alternative way to install corc is to run::

    make install

Which will create a virtual environment, install the required dependencies, and install corc itself.

-----
Usage
-----

Since `corc` is a top level interface for managing infrastucture components, specialized providers that provide the specific implementation have 
to be installed. To accomplish this, each of the different corc components define 
the `add_provider` and `remove_provider` arguments that can be used to install and remove providers::

    usage: corc orchestration [-h] {add_provider,remove_provider,pool,stack} ...

    options:
      -h, --help            show this help message and exit

    COMMAND:
      {add_provider,remove_provider,pool,stack}


For instance, if we want to add the `libvirt_provider <https://pypi.org/project/libvirt-provider/>`_ to the orchestration component, we can do so by running::

    corc orchestration add_provider libvirt_provider


-----------------------------
Orchestrator Stacks and Pools
-----------------------------

As part of the orchestration component, corc defines the concepts of `stacks` and `pools`.
A stack is a collection of resources that are managed and orchestrated by corc.

Stacks are expected to defined as a yaml file that are passed to corc, which is
used to orchestrate a set of resources.

A pool is a construct that can be used to logically group resources.
When a pool is constructed, it is saved to a local state file where the pool is constructed.

When defining a stack as a yaml file, it is supported that pools are defined as part of the stack.
An example of a stack yaml definition can be seen in the ``examples/stack.yml``

The corc orchestration CLI can be used to manage both `stacks` and `pools`::

    :~ corc orchestration -h
    usage: corc orchestration [-h] {add_provider,remove_provider,pool,stack} ...

    options:
    -h, --help            show this help message and exit

    COMMAND:
    {add_provider,remove_provider,pool,stack}


When a stack is deployed, corc will orchestrate the defined resources, create the 
specified pools if nonexistent, and associate resources to their specific pools.
