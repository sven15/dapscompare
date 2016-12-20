#
# Copyright (c) 2016 Stefan Knorr <sknorr@suse.de>
#

# FIXME: how do I check for the line end? $ does not work.
version = $(shell sed -n -r "s_^Version:\s+dapscompare\s+([.0-9]+)_\1_ p" README)
prefix = dist/
dirname = dapscompare-$(version)
packagename = $(dirname).tar.bz2

.PHONY: package clean

all: package

package: README dapscompare.py modules/daps.py modules/*.py
	if [ ! -d dist ]; then mkdir dist; fi
	if [ -f $(prefix)$(packagename) ]; then rm $(prefix)$(packagename); fi
	if [ -f $(prefix)$(dirname) ]; then rm -r $(prefix)$(packagename); fi
	mkdir $(prefix)$(dirname) && mkdir $(prefix)$(dirname)/modules
	cp dapscompare.py README $(prefix)$(dirname)
	cp modules/*.py $(prefix)$(dirname)/modules
	cd dist && tar -cvjSf $(packagename) $(dirname)
	@echo -e "\nWrote $(packagename)"
	rm -r $(prefix)$(dirname)

clean: $(prefix)dapscompare-*
	rm -r $(prefix)dapscompare-*
