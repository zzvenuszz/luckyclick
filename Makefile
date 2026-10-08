# Makefile for LuckyClick
# Targets:
#   install     - Install locally via pip
#   run         - Run the application
#   deb         - Build .deb package
#   clean       - Clean build artifacts

PACKAGE_NAME = luckyclick
VERSION = 1.1.2
DEBIAN_REVISION = 0

.PHONY: all install run deb clean

all: install

install:
	pip3 install --user -e .

run:
	python3 -m luckyclick.main

deb:
	# Ensure we have the right tools
	dpkg-checkbuilddeps 2>/dev/null || apt-get install -y debhelper python3-all python3-setuptools
	
	# Build the package
	dpkg-buildpackage -b -us -uc
	
	# Move the .deb to current directory
	mv ../$(PACKAGE_NAME)_$(VERSION)-$(DEBIAN_REVISION)_all.deb ./ 2>/dev/null || true
	
	@echo ""
	@echo "============================================"
	@echo "  ✅ .deb package created!"
	@echo "  File: $(PACKAGE_NAME)_$(VERSION)-$(DEBIAN_REVISION)_all.deb"
	@echo "  Install with: sudo dpkg -i $(PACKAGE_NAME)_$(VERSION)-$(DEBIAN_REVISION)_all.deb"
	@echo "============================================"

clean:
	rm -rf build/ dist/ *.egg-info/ __pycache__/
	rm -rf luckyclick/__pycache__/ luckyclick/core/__pycache__/ luckyclick/gui/__pycache__/
	rm -f ../$(PACKAGE_NAME)_*.deb ../$(PACKAGE_NAME)_*.dsc ../$(PACKAGE_NAME)_*.tar.xz
	rm -f ../$(PACKAGE_NAME)_*.buildinfo ../$(PACKAGE_NAME)_*.changes
	rm -rf debian/.debhelper/ debian/luckyclick/ debian/debhelper-build-stamp
	rm -f debian/files debian/*.log
	@echo "Cleaned!"