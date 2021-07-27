FROM registry.access.redhat.com/ubi8/python-39

# Add the program and the configuration file
ADD ./src/main.py .
ADD ./src/event.py .

# Install dependencies
RUN pip install --upgrade pip
RUN python -m pip install kubernetes
RUN python -m pip install google-api-python-client
RUN python -m pip install azurerm
RUN python -m pip install boto3
USER 1001