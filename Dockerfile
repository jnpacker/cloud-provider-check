FROM registry.access.redhat.com/ubi8/python-38

# Add the program and the configuration file
ADD ./src/main.py .
ADD ./src/event.py .

# Install dependencies
RUN pip install --upgrade pip
RUN python -m pip install kubernetes
RUN python -m pip install azurerm

USER 1001