.DEFAULT_GOAL := manga_scraper.pyz

PREFIX := ~/.local/bin
PYTHON := /usr/bin/env python3
# $(shell which python)
SRCDIR := ./src
SRCS := $(wildcard $(SRCDIR)/*.py)
APP := manga_scraper.pyz

$(APP): $(SRCS)
	python3 -m zipapp --output $(APP) --python "$(PYTHON)" $(SRCDIR)

install: $(APP)
	cp $(APP) $(PREFIX)/$(APP)
	chmod +x $(PREFIX)/$(APP)

uninstall:
	if [[ -f $(PREFIX)/$(APP) ]]; then \
		rm $(PREFIX)/$(APP); \
	fi

clean:
	if [[ -f $(APP) ]]; then \
		rm $(APP); \
	fi

.PHONY: clean install
