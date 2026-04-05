import json

from fastapi import HTTPException
from pydantic import ValidationError

from backend.web.api_handlers import PredictPayload, get_prediction_payload


def _read_request_body(request):
    body = getattr(request, "body", b"")
    if callable(body):
        body = body()
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    return body or "{}"


def handler(request):
    print("predict handler invoked")
    try:
        raw_body = _read_request_body(request)
        payload_dict = json.loads(raw_body)
        payload = PredictPayload(**payload_dict)
        response_payload = get_prediction_payload(payload)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response_payload),
        }
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"detail": "Invalid JSON body."}),
        }
    except ValidationError as error:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"detail": error.errors()}),
        }
    except HTTPException as error:
        return {
            "statusCode": error.status_code,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"detail": error.detail}),
        }
