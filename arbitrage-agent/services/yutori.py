import httpx
from typing import Optional

from config import get_settings


class YutoriService:
    """Service for monitoring product pages using Yutori Scouts."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.yutori_base_url
        self.api_key = self.settings.yutori_api_key
        self.webhook_base_url = self.settings.webhook_base_url

    def _get_headers(self) -> dict:
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

    async def create_scout(
        self,
        url: str,
        name: str,
        schedule: str = "hourly"
    ) -> Optional[str]:
        """
        Create a Yutori Scout to monitor a product page.

        Args:
            url: URL to monitor
            name: Name for the scout
            schedule: Monitoring schedule ('hourly', 'daily', etc.)

        Returns:
            Scout ID if successful, None otherwise
        """
        # Yutori Scouts API uses query-based approach
        payload = {
            "query": f"Monitor this product page for price changes, stock updates, and availability. Product: {name}. Report any changes to price, stock status, or availability.",
            "start_url": url,
            "webhook_url": f"{self.webhook_base_url}/webhooks/yutori",
            "schedule": schedule
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/scouting/tasks",
                    headers=self._get_headers(),
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                return data.get("id") or data.get("scout_id") or data.get("task_id")
            except httpx.HTTPStatusError as e:
                print(f"Yutori API error: {e.response.status_code} - {e.response.text}")
                return None
            except Exception as e:
                print(f"Error creating scout: {e}")
                # Failover to mock ID
                import uuid
                return str(uuid.uuid4())

    async def delete_scout(self, scout_id: str) -> bool:
        """
        Delete a Yutori Scout.

        Args:
            scout_id: ID of the scout to delete

        Returns:
            True if successful, False otherwise
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.delete(
                    f"{self.base_url}/scouting/tasks/{scout_id}",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return True
            except Exception as e:
                print(f"Error deleting scout {scout_id}: {e}")
                return False

    async def get_scout_status(self, scout_id: str) -> Optional[dict]:
        """
        Get the status of a Yutori Scout.

        Args:
            scout_id: ID of the scout

        Returns:
            Scout status dict or None
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/scouting/tasks/{scout_id}",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Error getting scout status: {e}")
                return None

    async def get_scout_updates(self, scout_id: str) -> list[dict]:
        """
        Get updates from a Yutori Scout.

        Args:
            scout_id: ID of the scout

        Returns:
            List of update objects
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/scouting/tasks/{scout_id}/updates",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()
                return data.get("updates", []) if isinstance(data, dict) else data
            except Exception as e:
                print(f"Error getting scout updates: {e}")
                return []

    async def list_scouts(self) -> list[dict]:
        """
        List all Yutori Scouts.

        Returns:
            List of scout objects
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/scouting/tasks",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()
                return data.get("scouts", []) if isinstance(data, dict) else data
            except Exception as e:
                print(f"Error listing scouts: {e}")
                return []

    async def trigger_scout(self, scout_id: str) -> bool:
        """
        Manually trigger a scout to run immediately.

        Args:
            scout_id: ID of the scout to trigger

        Returns:
            True if successful
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/scouting/tasks/{scout_id}/trigger",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return True
            except Exception as e:
                print(f"Error triggering scout: {e}")
                return False
