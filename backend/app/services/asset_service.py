import base64
import mimetypes


def _guess_mime_type(name: str, provided: str) -> str:
  if provided:
    return provided
  guessed, _ = mimetypes.guess_type(name)
  return guessed or "application/octet-stream"


def normalize_case_assets(case_assets: list[dict]) -> list[dict]:
  normalized = []
  for index, asset in enumerate(case_assets):
    mime_type = _guess_mime_type(asset.get("name", ""), asset.get("mimeType", ""))
    data_base64 = asset.get("dataBase64")
    binary = base64.b64decode(data_base64) if data_base64 else b""
    normalized.append(
      {
        "id": asset.get("id") or f"asset-{index + 1}",
        "kind": asset.get("kind", "text"),
        "name": asset.get("name") or f"asset-{index + 1}",
        "mimeType": mime_type,
        "sizeBytes": len(binary),
        "dataBase64": data_base64,
        "binary": binary,
        "dataUrl": f"data:{mime_type};base64,{data_base64}" if data_base64 else "",
        "text": asset.get("text", ""),
      }
    )
  return normalized


def build_asset_preview(asset: dict) -> dict:
  preview = {
    "id": asset["id"],
    "kind": asset["kind"],
    "name": asset["name"],
    "mimeType": asset["mimeType"],
    "sizeBytes": asset["sizeBytes"],
  }
  if asset["kind"] == "image" and asset["dataUrl"]:
    preview["previewUrl"] = asset["dataUrl"]
  if asset["kind"] == "audio":
    preview["previewText"] = asset["name"]
  if asset["kind"] == "text":
    preview["previewText"] = asset.get("text", "")[:120]
  return preview
