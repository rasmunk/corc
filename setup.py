#!/usr/bin/python
# coding: utf-8
import os
from setuptools import setup, find_packages

cur_dir = os.path.abspath(os.path.dirname(__file__))


def read(path):
    with open(path, "r") as _file:
        return _file.read()


def read_req(name):
    path = os.path.join(cur_dir, name)
    return [req.strip() for req in read(path).splitlines() if req.strip()]


version_ns = {}
with open(os.path.join(cur_dir, "version.py")) as f:
    exec(f.read(), {}, version_ns)


long_description = open("README.rst").read()
setup(
    name="corc",
    version=version_ns["__version__"],
    description="A tool for managing cloud resources and scheduling compute tasks",
    long_description=long_description,
    author="Rasmus Munk",
    author_email="munk1@live.dk",
    packages=find_packages(),
    url="https://github.com/rasmunk/corc",
    license="MIT",
    keywords=["Cloud", "Orchstration", "Compute"],
    install_requires=read_req("requirements.txt"),
    extras_require={
        "test": read_req("requirements-dev.txt"),
        "dev": read_req("requirements-dev.txt"),
    },
    entry_points={"console_scripts": ["corc = corc.cli.cli:run"]},
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
