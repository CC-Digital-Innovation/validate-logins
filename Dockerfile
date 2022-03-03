FROM python:3.8-slim

# install curl and jq
RUN apt-get update && apt-get install -y curl jq

# install sops
RUN curl -OL https://github.com/mozilla/sops/releases/download/v3.7.1/sops_3.7.1_amd64.deb \
    && apt-get -y install ./sops_3.7.1_amd64.deb \
    && rm sops_3.7.1_amd64.deb

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -U pip
RUN pip install --no-cache-dir -r requirements.txt

COPY app .

# Replace CMD if running outside of Kubernetes
# CMD [ "python3", "main.py" ]
CMD [ "./build-script.sh" ]
