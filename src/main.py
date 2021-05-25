#author: jpacker@redhat.com
import kubernetes.client
import os
import base64
import yaml
import event
import json

import azurerm
import boto3

from googleapiclient import discovery
from google.oauth2 import service_account

from pprint import pprint
#quota_client = boto3.client('service-quotas')
#response = quota_client.list_service_quotas(ServiceCode='vpc')
#response = quota_client.get_service_quota(ServiceCode='vpc', QuotaCode='L-E79EC296')
#pprint(response)

# Decode base64 values to string
def dc(base64Value):
    return base64.b64decode(base64Value).decode("utf-8")

configuration = kubernetes.client.Configuration()
configuration.verify_ssl = False
provider_types = ['aws','gcp','azr']

# Read API key Bearer Token
CM_TOKEN = os.getenv('CM_TOKEN')
if 'CM_TOKEN' not in os.environ:
    if not os.path.isfile('/var/run/secrets/kubernetes.io/serviceaccount/token'):
        raise EnvironmentError("Connection token not found. CM_TOKEN or .../serviceaccount/token")
    print("Read token for Service Account from a secret")
    CM_TOKEN = open('/var/run/secrets/kubernetes.io/serviceaccount/token', 'r').read()
else:
    os.getenv('CM_TOKEN')
configuration.api_key = {"authorization": "Bearer " + CM_TOKEN}

# Threshold percentage for which to fire a warning event
CM_THRESHOLD=0.85
if 'CM_THRESHOLD' in os.environ:
    CM_THRESHOLD = int(os.getenv('CM_THRESHOLD')) / 100

# Read the API URL
if 'CM_API_URL' not in os.environ:
    CM_API_URL = "https://kubernetes.default.svc.cluster.local"
else:
    CM_API_URL = os.getenv('CM_API_URL')
configuration.host = CM_API_URL

with kubernetes.client.ApiClient(configuration) as api_client:
    # Create instances of the API class
    api_core = kubernetes.client.CoreV1Api(api_client)
    for cloud in provider_types:
        for cloud_provider in api_core.list_secret_for_all_namespaces(label_selector="cluster.open-cluster-management.io/type="+cloud).items:
            try:
                secret_data = cloud_provider.data
                provider_name = cloud_provider.metadata.name
                if cloud == "aws":
                    print("AWS  : Processing Access Key: " + dc(secret_data['awsAccessKeyID']))
                    #quota_client = boto3.client('service-quotas')
                    #response = quota_client.list_service_quotas(ServiceCode='vpc')
                    #pprint(response)
                    # awsSecretAccessKeyID awsAccessKeyID

                elif cloud == "gcp":
                    # gcProjectID osServiceAccount.json
                    # Setup the service account json credential
                    with open('/tmp/gcp.json', 'w', encoding='utf-8') as outfile:
                        json.dump(json.loads(dc(secret_data['osServiceAccount.json'])), outfile)
                    cred = service_account.Credentials.from_service_account_file('/tmp/gcp.json')

                    compute = discovery.build('compute', 'v1', credentials=cred)
                    for region in ['global','europe-west3','us-east1','us-west1','us-central1']:
                        print("GCP: Processing Cloud Provider: " + provider_name + " in region: " + region)
                        if region == 'global':
                            print("gcProjectID: " + dc(secret_data['gcProjectID']))
                            req = compute.projects().get(project=dc(secret_data['gcProjectID']))
                        else:
                            req = compute.regions().get(project=dc(secret_data['gcProjectID']), region=region)

                        resp = req.execute()
                        for quota in resp['quotas']:
                            if quota['limit'] != 0 and quota['usage'] / quota['limit'] > CM_THRESHOLD:
                                msg = quota['metric'] + " " + str(quota['usage']) + "/" + str(quota['limit'])
                                print(" \ -> " + msg)
                                eventName = 'quota-' + provider_name + "-" + quota['metric']
                                event.fire(cloud_provider.metadata.name, cloud_provider.metadata.namespace, 'secret', eventName, "Quota warning for cloud provider " + provider_name + ": " + msg, 'FullQuota', 'Warning', api_core)

                elif cloud == "azr":
                    access_token = azurerm.get_access_token(dc(secret_data['tenantId']), dc(secret_data['clientId']), dc(secret_data['clientSecret']))
                    for region in ['centralus','eastus','eastus2','westus','westus2','southcentralus']:
                        compute_usage = azurerm.get_compute_usage(access_token, dc(secret_data['subscriptionId']), region)['value']
                        compute_usage = compute_usage + azurerm.get_network_usage(access_token, dc(secret_data['subscriptionId']), region)['value']
                        compute_usage = compute_usage + azurerm.get_storage_usage(access_token, dc(secret_data['subscriptionId']), region)['value']
                        print("Azure: Processing Cloud Provider: " + provider_name + " in region: " + region)

                        for quota in compute_usage:
                            if quota['limit'] != 0 and quota['currentValue'] / quota['limit'] > CM_THRESHOLD and quota['name']['value'] != 'NetworkWatchers':
                                msg = quota['name']['localizedValue'] + " " + str(quota['currentValue']) + "/" + str(quota['limit'])
                                print(" \ -> " + msg)
                                eventName = 'quota-' + provider_name + "-" + quota['name']['value']
                                event.fire(cloud_provider.metadata.name, cloud_provider.metadata.namespace, 'secret', eventName, "Quota warning for cloud provider " + provider_name + ": " + msg, 'FullQuota', 'Warning', api_core)
                            # clientSecret  subscriptionId tenantId clientId
            except:
                event.fire(cloud_provider.metadata.name, cloud_provider.metadata.namespace, 'secret', 'cloudprovider-quotacheck', "Cloud Provider quota check for cloud provider " + provider_name + " failed", 'cloudproviderquotacheckfail', 'Warning', api_core)
                if 'MY_POD_NAMESPACE' in os.environ and 'MY_POD_NAME' in os.environ:
                    event.fire(os.getenv('MY_POD_NAME'), os.getenv('MY_POD_NAMESPACE'), 'pod', 'cloudprovider-quotacheck', 'Cloud Provider quota check for cloud providers failed', 'cloudproviderquotacheckfailed', 'Warning', api_core)
                raise