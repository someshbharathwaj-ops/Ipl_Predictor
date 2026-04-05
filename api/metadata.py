import json

from backend.web.api_handlers import get_metadata_payload


def handler(request):
    print("metadata handler invoked")
    payload = get_metadata_payload()
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }
