.PHONY: all zip clean mypy pylint fix vendor aw-server
all: zip

PACKAGE_NAME := aw_watcher

zip: $(PACKAGE_NAME).ankiaddon

$(PACKAGE_NAME).ankiaddon: src/*
	rm -f $@
	rm -rf src/__pycache__
	rm -rf src/meta.json
	( cd src/; zip -r ../$@ * )

vendor:
	pip install -r requirements.txt -t src/vendor

fix:
	python -m black src --exclude="vendor"
	python -m isort src

mypy:
	python -m mypy src

pylint:
	python -m pylint src

# Run aw-server in testing mode (Windows)
aw-server:
	pwsh -Command "cd $$env:LOCALAPPDATA ; .\Programs\ActivityWatch\aw-server\aw-server.exe --testing"

clean:
	rm -f $(PACKAGE_NAME).ankiaddon
