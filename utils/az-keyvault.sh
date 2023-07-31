az account list --output table


az keyvault list --output table

key_vault_name=containerizationtool
az keyvault secret list --vault-name $key_vault_name --output table