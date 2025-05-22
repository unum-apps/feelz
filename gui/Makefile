ACCOUNT?=$(shell cat ../ACCOUNT)
IMAGE=unum-apps-tehfeelz-gui
VERSION?=dev
SEMVER=?=$(VERSION)
NAME=$(IMAGE)-$(ACCOUNT)

.PHONY: build shell image push semver

build:
	docker build . --build-arg BASE=$(BASE) -t $(ACCOUNT)/$(IMAGE):$(VERSION)

shell:
	-docker run -it --rm $(ACCOUNT)/$(IMAGE):$(VERSION) sh

image: build

push: image
	docker push $(ACCOUNT)/$(IMAGE):$(VERSION)

semver:
	docker pull $(ACCOUNT)/$(IMAGE):$(VERSION)
	docker tag $(ACCOUNT)/$(IMAGE):$(VERSION) $(ACCOUNT)/$(IMAGE):$(SEMVER)
	docker push $(ACCOUNT)/$(IMAGE):$(SEMVER)
