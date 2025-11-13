# Azure SDK for Python – Quick Start Guide
## Overview
The Azure SDK for Python provides libraries to manage Azure resources programmatically. This guide covers:

- Installing the SDK
- Authenticating with Azure
- Creating a Virtual Machine (VM)

## 1. Installation

Install the required packages using pip

```
pip install azure-identity azure-mgmt-resource azure-mgmt-compute
```

## 2. Authentication

Use DefaultAzureCredential for authentication. It supports multiple methods (Environment variables, Azure CLI login, Managed Identity).

## Login via Azure CLI

```
az login
```
Ensure you have the correct subscription selected
```
az account set --subscription "<your-subscription-id>"
```

## 3. Basic Setup

Create a Python script and import the required libraries

```
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient

# Authenticate
credential = DefaultAzureCredential()
subscription_id = "<your-subscription-id>"

# Clients
resource_client = ResourceManagementClient(credential, subscription_id)
compute_client = ComputeManagementClient(credential, subscription_id)
```

## 4. Create a Resource Group

```
resource_group_name = "myResourceGroup"
location = "eastus"

resource_client.resource_groups.create_or_update(
    resource_group_name,
    {"location": location}
)
```

## 5. Create a Virtual Machine

```
vm_name = "myVM"

vm_parameters = {
    "location": location,
    "hardware_profile": {"vm_size": "Standard_DS1_v2"},
    "storage_profile": {
        "image_reference": {
            "publisher": "Canonical",
            "offer": "UbuntuServer",
            "sku": "18.04-LTS",
            "version": "latest"
        }
    },
    "os_profile": {
        "computer_name": vm_name,
        "admin_username": "azureuser",
        "admin_password": "YourPassword123!"
    },
    "network_profile": {
        "network_interfaces": [
            {"id": "<network-interface-id>"}
        ]
    }
}

compute_client.virtual_machines.begin_create_or_update(
    resource_group_name,
    vm_name,
    vm_parameters
)
```

## 6. Useful Commands

- List all VMs

```
for vm in compute_client.virtual_machines.list_all():
    print(vm.name)
```

- Delete a VM

```
compute_client.virtual_machines.begin_delete(resource_group_name, vm_name)
```

## References

https://learn.microsoft.com/en-us/azure/developer/python/