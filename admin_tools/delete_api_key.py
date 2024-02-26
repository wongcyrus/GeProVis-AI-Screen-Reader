from google.cloud import api_keys_v2

def delete_key(name: str):
    # Create a client
    client = api_keys_v2.ApiKeysClient()

    # Initialize request argument(s)
    request = api_keys_v2.DeleteKeyRequest(
        name=name,
    )

    # Make the request
    operation = client.delete_key(request=request)

    print("Waiting for operation to complete...")

    response = operation.result()

    # Handle the response
    print(response)

def undelete_key(name: str):
    # Create a client
    client = api_keys_v2.ApiKeysClient()

    # Initialize request argument(s)
    request = api_keys_v2.UndeleteKeyRequest(
        name=name,
    )

    # Make the request
    operation = client.undelete_key(request=request)

    print("Waiting for operation to complete...")

    response = operation.result()

    # Handle the response
    print(response)

if __name__ == "__main__":
    undelete_key(name="projects/310301685106/locations/global/keys/studentid-12345678")