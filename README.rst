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
