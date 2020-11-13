#author: jpacker@redhat.com
import kubernetes.client
import os
import base64
import yaml
import event
import json

#from googleapiclient import discovery
import azurerm
from pprint import pprint

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
        for cloud_provider in api_core.list_secret_for_all_namespaces(label_selector="cluster.open-cluster-management.io/provider="+cloud).items:
            secret_data = yaml.safe_load(base64.b64decode(cloud_provider.data['metadata']))
            provider_name = cloud_provider.metadata.name
            if cloud == "aws":
                print("AWS  : Processing Access Key: " + secret_data['awsAccessKeyID'])
                # awsSecretAccessKeyID awsAccessKeyID
            elif cloud == "gcp":
                # gcProjectID
                print("GCP: Processing ProjectID: " + secret_data['gcProjectID'])
                service_account = eval(secret_data['gcServiceAccountKey'])
                #with open('/tmp/gcp.json', 'w') as outfile:
                #    json.dump(service_account, outfile)
                #client = dns.Client.from_service_account_json('/tmp/gcp.json')
                #quotas = client.quotas()
                #pprint(quotas)
            elif cloud == "azr":
                access_token = azurerm.get_access_token(secret_data['tenantId'], secret_data['clientId'], secret_data['clientSecret'])
                for region in ['centralus','eastus','eastus2','westus','westus2','southcentralus']:
                    compute_usage = azurerm.get_compute_usage(access_token, secret_data['subscriptionId'], region)['value']
                    compute_usage = compute_usage + azurerm.get_network_usage(access_token, secret_data['subscriptionId'], region)['value']
                    compute_usage = compute_usage + azurerm.get_storage_usage(access_token, secret_data['subscriptionId'], region)['value']
                    print("Azure: Processing Cloud Provider: " + provider_name + " in region: " + region)

                    for quota in compute_usage:
                        if quota['limit'] != 0 and quota['currentValue'] / quota['limit'] > 0.85 and quota['name']['value'] != 'NetworkWatchers':
                            msg = quota['name']['localizedValue'] + " " + str(quota['currentValue']) + "/" + str(quota['limit'])
                            print(" \ -> " + msg)
                            eventName = 'quota-' + provider_name + "-" + quota['name']['value']
                            event.fire(cloud_provider.metadata.name, cloud_provider.metadata.namespace, 'secret', eventName, "Full quota for cloud provider " + provider_name + ": " + msg, 'FullQuota', 'Warning', api_core)
                        # clientSecret  subscriptionId tenantId clientId
