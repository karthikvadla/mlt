#!/bin/bash

# TODO: port to python

set -e
set -u
set -o pipefail

_usage() {
  echo "${*}"
cat << EOF
usage: kube_debug.sh [deployment_name] [open_port] [BRANCH] {optional: repo, used instead of deployment name}
examples:
  kubefs helium 51000 improvement/concurrent_requests
  kubefs helium-celery 51000 improvement/concurrent_requests helium
EOF
  exit 1
}

[[ $# -lt 3 ]] && _usage "missing parameters"

DLS_DEVTOOLS="${DLS_DEVTOOLS:-${HOME}/dls-devtools}"
NERVANA_NAMESPACE="${NERVANA_NAMESPACE:-$(whoami)}"
PUB_KEY="${PUB_KEY:-${HOME}/.ssh/id_rsa.pub}"

script_dir=$NERVANA_ROOT/scripts
. "${script_dir}/common.sh"

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

_create_pvc() {
  echo "{
    \"apiVersion\": \"v1\",
    \"kind\": \"PersistentVolumeClaim\",
    \"metadata\": {
        \"name\": \"${1}\"
    },
    \"spec\": {
        \"accessModes\": [
            \"ReadWriteOnce\"
        ],
        \"resources\": {
            \"requests\": {
                \"storage\": \"1Gi\"
            }
        },
        \"storageClassName\": \"standard\"
    }
}" | kubectl apply -f -
}

deployment=$1
port=$2
branch=$3
if [ $# -eq 4 ]; then repo=$4; else repo=$1; fi
CLAIM_NAME="${deployment}-${NERVANA_NAMESPACE}"
_info "replacing deployment ${deployment}"

_check_cmd kubectl 2>&1

_create_pvc "${CLAIM_NAME}"


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
        jq "setpath([\"spec\",\"template\",\"spec\",\"containers\",0,\"command\"];[\"/bin/bash\",\"-c\",\"$debug_command\"])" | \
        jq 'setpath(["spec","template","spec","containers",0,"workingDir"];"/")' | \
    kubectl replace deployment "${deployment}" -f -
    kubectl label deployment $deployment debugger=true
fi

_wait_for_pods $deployment 1
pod=$(kubectl get pods --selector=app="${deployment}" | grep "${deployment}" | awk '{print $1}')

[[ -f "${PUB_KEY}" ]] || _error "Cannot find public key ${PUB_KEY}"
_info "copying ${PUB_KEY} to ${pod}"
kubectl exec -i "${pod}" -- bash -c "mkdir -p /root/.ssh"
# NOTE: kubectl cp does not support changing target filename
cp "${PUB_KEY}" "${script_dir}"/authorized_keys2
kubectl cp "${script_dir}/authorized_keys2" "${pod}":/root/.ssh/authorized_keys2
rm "${script_dir}/authorized_keys2"

_info "Copy known hosts so can pull from github. Change to adding word 'yes' to github clone later?"
kubectl cp "${HOME}/.ssh/known_hosts" "${pod}":/root/.ssh/known_hosts

_info "Installing dependencies on ${pod}"
kubectl cp "${script_dir}/install_ssh.sh" "${pod}":/tmp/install_ssh.sh
kubectl exec -i "${pod}" -- /tmp/install_ssh.sh

_info "port forwarding ${pod} on port ${port}"
pkill kubectl port-forward "${pod}" || true
kubectl port-forward "${pod}" "${port}":22 &

sleep 2

_info "Create user with same name as current user"
kubectl exec -i "${pod}" -- bash -c "useradd -ms /bin/bash `whoami` || true"

_info "Re-clone whatever we are trying to deploy so versioneer will work"
_info "Falling back to deployment name if no repo specified"
ssh -A root@127.0.0.1 -p ${port} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /dev/null "rm -rf /app_sysinstall && (mv /app /app_sysinstall > /dev/null 2>&1 || true) && git clone git@github.com:NervanaSystems/${repo}.git /app && cd /app && chown -R `whoami` . && git checkout ${branch}"

_info "Install rsync in container so syncing is possible quickly"
kubectl cp "$DLS_DEVTOOLS/scripts/rsync_rsh.sh" "${pod}":/tmp/rsync_rsh.sh
kubectl exec -i "${pod}" -- bash -c "apt-get -y install rsync && echo 'export 'RSYNC_RSH=/tmp/rsync_rsh.sh >> /root/.bashrc"

_info "Install vim into container"
kubectl exec -i "${pod}" -- bash -c "apt-get -y install vim && export EDITOR=vim"

_info "Save deployment environment variables."
kubectl cp "$DLS_DEVTOOLS/scripts/export_env_vars.sh" "${pod}":/tmp/export_env_vars.sh
kubectl exec -i "${pod}" -- /tmp/export_env_vars.sh `whoami`

# TODO: print out what command users can run for each deployment to run the thing they are patching manually

_info "pod ${pod} is accessible via:
ssh -A root@127.0.0.1 -p ${port} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /dev/null"
