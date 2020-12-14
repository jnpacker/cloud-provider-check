# cloud-provider-quota-check
This Kubernetes cronjob is able to detect low quota values for Cloud Providers defined in Red Hat Advanced Cluster Management.
## Supported Cloud Providers
1. GCP
2. Azure

## How it works
The code checks every 60min for quota values across all cloud providers on the system. It generates Kubernetes **Warning** events in the namespaces where the Cloud Provider secrets are stored. It also associates the event to the Cloud provider secret.

# Deploy
It is as simple as connecting to OpenShift hosting Advanced Cluster Management and running the following command:
```bash
# Log into Openshift
make setup
```
You can view the status of the cronjob:
```bash
oc get cronjobs -A
```
Use the OpenShift event view to see output. Filter on `quota`


## Manually run a quota check
Command:
```bash
make runqc
```
Check the output:
```bash
oc get pods | grep cloudprovider-quotacheck-job
oc logs <POD_NAME_FROM_PREVIOUS_COMMAND>
```


## Change the threshold percentage
Update:
```bash
./deploy/cloudproviderquotacheck-cronjob.yaml
./deploy/cloudproviderquotacheck-job.yaml
```
Change the `env` variable `CM_THRESHOLD`
```yaml
env:
- name: PYTHONWARNINGS
    value: "ignore:Unverified HTTPS request"
- name: CM_THRESHOLD
    value: "85"             # This is the threshold percentage after which a kube warning event is fired
```

## Required environment variables when running from your local machine
```bash
export CM_TOKEN=<TOKEN_VALUE>                  # The OCP connection token
export CM_API_URL=https://my.cluster.com:6443  # The OCP API URL

# OPTIONL
export CM_THRESHOLD=85                         # The threshold above which a kube warning event is fired

# Required to BUILD & PUSH
export tag=0.X                   # Used to tag the image
export REPO_URL=quay.io/my-repo  # Repository to push image. requires docker already be authenticated
```

### OPTIONAL: To change namespace used
```bash
export NAMESPACE         # Used to work with a different namespace
```
Also edit deploy/rolebinding.yaml file and replace `open-cluster-management` with yournamespace of choice
```yaml
name: system:serviceaccount:open-cluster-management:cloudprovider-quotacheck
```
