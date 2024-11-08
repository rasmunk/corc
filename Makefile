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

PACKAGE_NAME=corc
PACKAGE_NAME_FORMATTED=$(subst -,_,$(PACKAGE_NAME))

.PHONY: all init clean dist distclean maintainer-clean
.PHONY: install-dev uninstall-dev install-dep uninstall-dep
.PHONY: install uninstall installtest uninstalltest test

all: venv install-dep init

init:
ifeq ($(shell test -e defaults.env && echo yes), yes)
ifneq ($(shell test -e .env && echo yes), yes)
		ln -s defaults.env .env
endif
endif

clean: distclean venv-clean
	rm -fr .env
	rm -fr *.lock
	rm -fr .pytest_cache
	rm -fr tests/__pycache__

dist: venv
	$(VENV)/python setup.py sdist bdist_wheel

distclean:
	rm -fr dist build $(PACKAGE_NAME).egg-info $(PACKAGE_NAME_FORMATTED).egg-info

maintainer-clean: distclean
	@echo 'This command is intended for maintainers to use; it'
	@echo 'deletes files that may need special tools to rebuild.'

install-dev: venv
	$(VENV)/pip install -r requirements-dev.txt

uninstall-dev: venv
	$(VENV)/pip uninstall -y -r requirements-dev.txt

install-dep: venv
	$(VENV)/pip install -r requirements.txt

uninstall-dep: venv
	$(VENV)/pip uninstall -y -r requirements.txt

install: install-dep
	$(VENV)/pip install .

uninstall: uninstall-dep
	$(VENV)/pip uninstall -y $(PACKAGE_NAME)

installtest: install-dep
	$(VENV)/pip install -r tests/requirements.txt

uninstalltest: venv
	$(VENV)/pip uninstall -y -r requirements.txt

test_pre: venv
	. $(VENV)/activate; python3 setup.py check -rms

test: test_pre
	. $(VENV)/activate; pytest -s -v tests/providers
	. $(VENV)/activate; pytest -s -v tests/

include Makefile.venv