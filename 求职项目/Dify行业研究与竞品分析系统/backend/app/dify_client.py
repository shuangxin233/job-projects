import os
from typing import Any

import httpx


class DifyClient:
  def __init__(self):
    self.api_key = os.getenv("DIFY_API_KEY", "")
    self.workflow_url = os.getenv("DIFY_WORKFLOW_URL", "http://127.0.0.1/v1/workflows/run")
    self.timeout = float(os.getenv("DIFY_TIMEOUT_SECONDS", "180"))

  @property
  def configured(self) -> bool:
    return bool(self.api_key and self.workflow_url)

  async def run_workflow(self, inputs: dict[str, Any], user: str = "rag-project-3") -> dict[str, Any]:
    if not self.configured:
      raise RuntimeError("DIFY_API_KEY and DIFY_WORKFLOW_URL must be configured.")

    payload = {
      "inputs": inputs,
      "response_mode": "blocking",
      "user": user,
    }
    headers = {"Authorization": f"Bearer {self.api_key}"}

    async with httpx.AsyncClient(timeout=self.timeout) as client:
      response = await client.post(self.workflow_url, json=payload, headers=headers)
      response.raise_for_status()
      return response.json()
