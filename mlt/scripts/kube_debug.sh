#!/bin/bash

# TODO: port to python

set -e
set -u
set -o pipefail

deployment=$1

_wait_for_pods(){
    if [[ $# -ne 2 ]]; then
        _error "must pass 2 arguments to wait_for_pod. deployment and replicacount"
    fi
    _info "waiting for ${1} to come up"
    while ! [[ $(kubectl get pods --selector=app=$1 | grep $1 | awk '{{print $2}}') == "$2/$2" ]]; do
        kubectl get pods --selector=app=$1 | grep CrashLoopBackOff && echo 'container failed to start' && exit 1
        echo -n .
        sleep 5
    done
}

echo "Replacing deployment ${deployment}"


if ! [[ $(kubectl get deployment ${deployment} -o json | jq -r '.metadata.labels.debugger') == 'true' ]]; then
    debug_command="if [ ! -d "/mnt/${NERVANA_NAMESPACE}/${deployment}" ]; then
  mv /app /mnt/${NERVANA_NAMESPACE}/${deployment}
fi
rm -rf /app
ln -sf /mnt/${NERVANA_NAMESPACE}/${deployment} /app; trap : TERM INT; sleep infinity & wait"
    kubectl get deployment "${deployment}" -o json | \
        jq 'del(.metadata.resourceVersion)' | \
        jq ".spec.template.spec.volumes += [{\"name\": \"user-pvc\", \"persistentVolumeClaim\": { \"claimName\": \"${CLAIM_NAME}\" } }]" | \
        jq ".spec.template.spec.containers[0].volumeMounts +=[{\"mountPath\":\"/mnt/${NERVANA_NAMESPACE}\",\"name\":\"user-pvc\"}]" | \
        jq 'delpaths([["spec","template","spec","containers",0,"readinessProbe"],["spec","template","spec","containers",0,"livenessProbe"]])' | \
        jq "setpath([\"spec\",\"template\",\"spec\",\"containers\",0,\"command\"];[\"/bin/bash\",\"-c\",\"sleep infinity & wait\"])" | \
        jq 'setpath(["spec","template","spec","containers",0,"workingDir"];"/")' | \
    kubectl replace deployment "${deployment}" -f -
    kubectl label deployment $deployment debugger=true
fi

_wait_for_pods $deployment 1
pod=$(kubectl get pods --selector=app="${deployment}" | grep "${deployment}" | awk '{print $1}')

