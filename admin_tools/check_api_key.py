
from google.cloud import api_keys_v2
from google.cloud import language_v1

def lookup_api_key(api_key_string: str) -> None:
    """
    Retrieves name (full path) of an API key using the API key string.

    TODO(Developer):
    1. Before running this sample,
      set up ADC as described in https://cloud.google.com/docs/authentication/external/set-up-adc
    2. Make sure you have the necessary permission to view API keys.

    Args:
        api_key_string: API key string to retrieve the API key name.
    """

    # Create the API Keys client.
    client = api_keys_v2.ApiKeysClient()

    # Initialize the lookup request and set the API key string.
    lookup_key_request = api_keys_v2.LookupKeyRequest(
        key_string=api_key_string,
        # Optionally, you can also set the etag (version).
        # etag=etag,
    )
    
    # Make the request and obtain the response.
    lookup_key_response = client.lookup_key(lookup_key_request)
    

    print(f"Successfully retrieved the API key name: {lookup_key_response}")

def authenticate_with_api_key(quota_project_id: str, api_key_string: str) -> None:
    """
    Authenticates with an API key for Google Language service.

    TODO(Developer): Replace these variables before running the sample.

    Args:
        quota_project_id: Google Cloud project id that should be used for quota and billing purposes.
        api_key_string: The API key to authenticate to the service.
    """

    # Initialize the Language Service client and set the API key and the quota project id.
    client = language_v1.LanguageServiceClient(
        client_options={"api_key": api_key_string, "quota_project_id": quota_project_id}
    )

    text = "Hello, world!"
    document = language_v1.Document(
        content=text, type_=language_v1.Document.Type.PLAIN_TEXT
    )

    # Make a request to analyze the sentiment of the text.
    sentiment = client.analyze_sentiment(
        request={"document": document}
    ).document_sentiment

    print(f"Text: {text}")
    print(f"Sentiment: {sentiment.score}, {sentiment.magnitude}")
    print("Successfully authenticated using the API key")   

if __name__ == "__main__":
    lookup_api_key("")
