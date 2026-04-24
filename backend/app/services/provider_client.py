import json
from urllib import request
from urllib.error import HTTPError, URLError
import uuid


def post_json(url: str, payload: dict, api_key: str, timeout: int = 45) -> dict:
  body = json.dumps(payload).encode("utf-8")
  headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}",
  }
  req = request.Request(url, data=body, headers=headers, method="POST")

  try:
    with request.urlopen(req, timeout=timeout) as response:
      return json.loads(response.read().decode("utf-8"))
  except HTTPError as error:
    detail = error.read().decode("utf-8", errors="ignore")
    raise RuntimeError(f"Provider HTTP error {error.code}: {detail}") from error
  except URLError as error:
    raise RuntimeError(f"Provider connection error: {error}") from error


def post_multipart(url: str, fields: dict[str, str], files: list[dict], api_key: str, timeout: int = 90) -> dict:
  boundary = f"----AIGCSAR{uuid.uuid4().hex}"
  body = bytearray()

  for key, value in fields.items():
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
    body.extend(str(value).encode("utf-8"))
    body.extend(b"\r\n")

  for file_item in files:
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(
      (
        f'Content-Disposition: form-data; name="{file_item["field"]}"; '
        f'filename="{file_item["filename"]}"\r\n'
      ).encode("utf-8")
    )
    body.extend(f'Content-Type: {file_item["content_type"]}\r\n\r\n'.encode("utf-8"))
    body.extend(file_item["content"])
    body.extend(b"\r\n")

  body.extend(f"--{boundary}--\r\n".encode("utf-8"))

  headers = {
    "Content-Type": f"multipart/form-data; boundary={boundary}",
    "Authorization": f"Bearer {api_key}",
  }
  req = request.Request(url, data=bytes(body), headers=headers, method="POST")

  try:
    with request.urlopen(req, timeout=timeout) as response:
      return json.loads(response.read().decode("utf-8"))
  except HTTPError as error:
    detail = error.read().decode("utf-8", errors="ignore")
    raise RuntimeError(f"Provider HTTP error {error.code}: {detail}") from error
  except URLError as error:
    raise RuntimeError(f"Provider connection error: {error}") from error
