# cloud-provider-quota-check
This Kubernetes cronjob is able to detect low quota values for Cloud Providers defined in Red Hat Advanced Cluster Management.

## How it works
The code checks every 60min for quota values across all cloud providers on the system. It generates Kubernetes **Warning** events in the namespaces where the Cloud Provider secret is stored. It also associates the event to the Cloud provider secret.

# Deploy
It is as simple as connecting to OpenShift and running the following command:
```bash
# Log into Openshift
make setup
```
You can view the status of the cronjob:
```bash
oc get cronjobs -A
```


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


## Change namespace
Edit the `Makefile` and change the value of
```Makefile
NAMESPACE := open-cluster-management   # Use your namespace of choice
```
Also edit deploy/rolebinding.yaml file and replace `open-cluster-management` with yournamespace of choice
```yaml
name: system:serviceaccount:open-cluster-management:cloudprovider-quotacheck
```