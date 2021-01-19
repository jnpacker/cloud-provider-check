REPO_URL ?= ${REPO_URL}
TAG ?= 0.4
NAMESPACE ?= open-cluster-management

all:
	@echo "Commands:"
	@echo ""
	@echo "make build     # Build image ONLY"
	@echo "make push      # Build and push the image used by manual and cronjobs"
	@echo "make runqc     # Manually launch Quota check"
	@echo "make setup     # Deploys the cronjobs"
	@echo ""
	@echo "make run       # Executes the code locally via \"python\""
	@echo "  Environment Variables needed:"
	@echo "    export CM_TOKEN=      # This is your ACM Hub access token"
	@echo "    export CM_API_URL=    # This is your ACM Hub API URL: https://mycluster.com:6443"
	@echo "    export CM_THRESHOLD=  # This is the percentage threshold above which a warning event occurs" 


build:
	docker build . -t ${REPO_URL}/cloud-provider-quota-check:${TAG}

push: build
	./docker-tools/push.sh

clean:
	docker image rm ${REPO_URL}/cloud-provider-quota-check:${TAG}

runqc:
	oc -n ${NAMESPACE} create -f deploy/cloudproviderquotacheck-job.yaml

setup:
	oc -n ${NAMESPACE} apply -k deploy/

run:
	python src/main.py
