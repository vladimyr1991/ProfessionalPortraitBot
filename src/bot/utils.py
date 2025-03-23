import replicate
import os

def get_replicate_client() -> replicate.Client:
    return replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))