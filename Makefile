REPO_URL := ${REPO_URL}
TAG := 0.3
NAMESPACE := open-cluster-management

all:
	@echo "Commands:"
	@echo ""
	@echo "make build     # Build image ONLY"
	@echo "make push      # Build and push the image used by manual and cronjobs"
	@echo "make runqc   # Manually launch Quota check"
	@echo "make setup     # Deploys the cronjobs"

build:
	docker build . -t ${REPO_URL}/cloud-provider-quota-check:${TAG}

push: build
	docker push ${REPO_URL}/cloud-provider-quota-check:${TAG}

clean:
	docker image rm ${REPO_URL}/cloud-provider-quota-check:${TAG}

runqc:
	oc -n ${NAMESPACE} create -f deploy/cloudproviderquotacheck-job.yaml

setup:
	oc -n ${NAMESPACE} apply -k deploy/
