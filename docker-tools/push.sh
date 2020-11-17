#!/bin/bash
loc=$(dirname $0)
echo ${loc}
docker push ${REPO_URL}/cloud-provider-quota-check:${TAG}
SHA256=`docker inspect --format='{{index .RepoDigests 0}}' ${REPO_URL}/cloud-provider-quota-check:${TAG}`
sed -i "s|image: .*$|image: ${SHA256}|g" $loc/../deploy/cloudproviderquotacheck-cronjob.yaml
sed -i "s|image: .*$|image: ${SHA256}|g" $loc/../deploy/cloudproviderquotacheck-job.yaml