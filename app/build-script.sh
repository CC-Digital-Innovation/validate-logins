#!/bin/bash

# get token from vault
export VAULT_TOKEN=$(curl -X POST -d "{\"role\": \"sops\", \"jwt\": \"$(cat $JWT_PATH)\"}" "${VAULT_ADDR}/v1/auth/kubernetes/login" | jq -r .auth.client_token)

# decrypt config file
sops -d --hc-vault-transit ${VAULT_ADDR}/v1/sops/keys/test-key encrypted.ini > config.ini

# run main
python main.py
