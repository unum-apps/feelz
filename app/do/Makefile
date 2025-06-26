CLUSTER="do-{{ unum }}-unum"
NAMESPACE="feelz"
SERVICE="gui"
LOCAL_PORT=5270
.PHONY: tfenv init remote install uninstall

tfenv:
	tfenv use 1.10.5

init: tfenv
	terraform init

remote:
	kubectx ${CLUSTER}
	@open "http://localhost:${LOCAL_PORT}"
	kubectl port-forward -n ${NAMESPACE} service/${SERVICE} ${LOCAL_PORT}:http

install: init
	terraform apply

uninstall: init
	terraform destroy
