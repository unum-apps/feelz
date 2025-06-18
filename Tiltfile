k8s_yaml(kustomize('kubernetes/tilt'))

k8s_resource(
  objects=['feelz:namespace'],
  new_name='namespace'
)

local_resource(
    name='config', resource_deps=['namespace'],
    cmd='kubectx docker-desktop && kubectl -n feelz create configmap config --from-file config/ --dry-run=client -o yaml | kubectl apply -f -'
)

local_resource(
    name='secret', resource_deps=['namespace'],
    cmd='kubectx docker-desktop && kubectl -n feelz create secret generic secret --from-file secret/ --dry-run=client -o yaml | kubectl apply -f -'
)

# api

docker_build('unum-apps-feelz-api', './api')
k8s_resource('api', port_forwards=['15270:80', '15238:5678'], resource_deps=['secret'])

# gui

docker_build('unum-apps-feelz-gui', './gui')
k8s_resource('gui', port_forwards=['5270:80'], resource_deps=['api'])

# daemon

docker_build('unum-apps-feelz-daemon', './daemon')
k8s_resource('daemon', port_forwards=['25238:5678'], resource_deps=['api'])

# cron

docker_build('unum-apps-feelz-cron', './cron')
k8s_resource('cron', port_forwards=['35238:5678'], resource_deps=['secret'])
