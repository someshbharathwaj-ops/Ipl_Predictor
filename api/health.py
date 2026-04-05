import json

from backend.web.api_handlers import get_health_payload


def handler(request):
    print("health handler invoked")
    payload = get_health_payload()
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }
