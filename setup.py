#!/usr/bin/python
# coding: utf-8

import os
from setuptools import setup, find_packages

cur_dir = os.path.abspath(os.path.dirname(__file__))

version_ns = {}
with open(os.path.join(cur_dir, "version.py")) as f:
    exec(f.read(), {}, version_ns)

long_description = open("README.rst").read()
setup(
    name="oci_orchestration",
    version=version_ns["__version__"],
    description="A set of helper functions to "
    "orchestrate Oracle Cloud Infrastructure entities",
    long_description=long_description,
    author="Rasmus Munk",
    author_email="munk1@live.dk",
    packages=find_packages(),
    url="https://github.com/rasmunk/oci_orchestration",
    license="MIT",
    keywords=["OCI", "Orchestration"],
    install_requires=["ansible", "kubernetes", "oci"],
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
