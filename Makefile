VERSION?=$(shell cat VERSION)
SEMVER=$(shell cat VERSION)
TILT_PORT=8438
INSTALL=python:3.8.5-alpine3.12
VOLUMES=-v ${PWD}/api/:/opt/service/api/ \
		-v ${PWD}/VERSION:/opt/service/VERSION \
		-v ${PWD}/setup.py:/opt/service/setup.py
.PHONY: up down setup semver tag untag

up:
	kubectx docker-desktop
	mkdir -p secret
	mkdir -p config
	test -f secret/mysql.json || echo '{"host": "db.mysql", "user": "root", "password": "local"}' > secret/mysql.json
	test -d api/ddl || (cd api; make build; make ddl;)
	test -d daemon/dep || (cd daemon; make dep;)
	test -d cron/dep || (cd cron; make dep;)
	# cnc-forge: up
	tilt --port $(TILT_PORT) up

down:
	kubectx docker-desktop
	tilt down

setup:
	docker run $(TTY) $(VOLUMES) $(INSTALL) sh -c "cp -r /opt/service /opt/install && \
	apk add git && \
	pip install 'unum-ledger @ git+https://github.com/unum-apps/ledger@0.1.4rc2' && \
	cd /opt/install/ && python setup.py install && \
	python -m unum_feelz"

semver:
	cd api; VERSION=$(VERSION) SEMVER=$(SEMVER) make semver;
	cd daemon; VERSION=$(VERSION) SEMVER=$(SEMVER) make semver;
	cd cron; VERSION=$(VERSION) SEMVER=$(SEMVER) make semver;
	cd gui; VERSION=$(VERSION) SEMVER=$(SEMVER) make semver;

tag:
	-git tag -a $(VERSION) -m "Version $(VERSION)"
	git push origin --tags

untag:
	-git tag -d $(VERSION)
	git push origin ":refs/tags/$(VERSION)"
