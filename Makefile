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

.PHONY: all
all: venv install-dep init

.PHONY: init
init:
ifeq ($(shell test -e defaults.env && echo yes), yes)
ifneq ($(shell test -e .env && echo yes), yes)
		ln -s defaults.env .env
endif
endif

.PHONY: clean
clean: distclean venv-clean
	rm -fr .env
	rm -fr *.lock
	rm -fr .pytest_cache
	rm -fr tests/__pycache__

.PHONY: dist
dist: venv install-dist-dep
	$(VENV)/python -m build .

.PHONY: install-dist-dep
install-dist-dep: venv
	$(VENV)/pip install build

.PHONY: distclean
distclean:
	rm -fr dist build $(PACKAGE_NAME).egg-info $(PACKAGE_NAME_FORMATTED).egg-info

.PHONY: maintainer-clean
maintainer-clean: distclean
	@echo 'This command is intended for maintainers to use; it'
	@echo 'deletes files that may need special tools to rebuild.'

.PHONY: install-dev
install-dev: venv
	$(VENV)/pip install -r requirements-dev.txt

.PHONY: uninstall-dev
uninstall-dev: venv
	$(VENV)/pip uninstall -y -r requirements-dev.txt

.PHONY: install-dep
install-dep: venv
	$(VENV)/pip install -r requirements.txt

.PHONY: uninstall-dep
uninstall-dep: venv
	$(VENV)/pip uninstall -y -r requirements.txt

.PHONY: install
install: install-dep
	$(VENV)/pip install .

.PHONY: uninstall
uninstall: uninstall-dep
	$(VENV)/pip uninstall -y $(PACKAGE_NAME)

.PHONY: installtest
installtest: install-dep
	$(VENV)/pip install -r tests/requirements.txt

.PHONY: uninstalltest
uninstalltest: venv
	$(VENV)/pip uninstall -y -r requirements.txt

.PHONY: test_pre
test_pre: venv
	. $(VENV)/activate; python3 setup.py check -rms

.PHONY: test
test: test_pre
	. $(VENV)/activate; pytest -s -v tests/providers
	. $(VENV)/activate; pytest -s -v tests/

include Makefile.venv