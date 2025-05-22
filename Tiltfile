k8s_yaml(kustomize('kubernetes/tilt'))

k8s_resource(
  objects=['tehfeelz:namespace'],
  new_name='namespace'
)

local_resource(
    name='config', resource_deps=['namespace'],
    cmd='kubectx docker-desktop && kubectl -n tehfeelz create configmap config --from-file config/ --dry-run=client -o yaml | kubectl apply -f -'
)

local_resource(
    name='secret', resource_deps=['namespace'],
    cmd='kubectx docker-desktop && kubectl -n tehfeelz create secret generic secret --from-file secret/ --dry-run=client -o yaml | kubectl apply -f -'
)

# api

docker_build('unum-apps-tehfeelz-api', './api')
k8s_resource('api', port_forwards=['15270:80', '15238:5678'], resource_deps=['secret'])

# gui

docker_build('unum-apps-tehfeelz-gui', './gui')
k8s_resource('gui', port_forwards=['5270:80'], resource_deps=['api'])

# daemon

docker_build('unum-apps-tehfeelz-daemon', './daemon')
k8s_resource('daemon', port_forwards=['25238:5678'], resource_deps=['api'])

# cron

docker_build('unum-apps-tehfeelz-cron', './cron')
k8s_resource('cron', port_forwards=['35238:5678'], resource_deps=['secret'])

