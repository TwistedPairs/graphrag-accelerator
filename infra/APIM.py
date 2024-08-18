import requests

# Define the subscription key variable
# Replace "YOUR_SUBSCRIPTION_KEY" with the actual copied key
ocp_apim_subscription_key = "5ce3cc7433fe48a49e15d06cbb4195e7"

# Example Headers with Subscription Key
headers = {
    "Ocp-Apim-Subscription-Key": ocp_apim_subscription_key
}

# Example endpoint from previously provided data
endpoint = "https://apim-6b7pszrzqfrdm.azure-api.net"

# Example API Call
response = requests.get(
    url=f"{endpoint}/data",
    headers=headers
)

# Log the status to verify it's working
print(response.status_code)
print(response.json())