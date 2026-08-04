import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any

logger = logging.getLogger("socialpilot.webhooks.youtube")

class YouTubeWebhookHandler:
    """YouTube PubSubHubbub Atom Notification Event Listener."""

    @staticmethod
    def parse_atom_feed(xml_content: str) -> Dict[str, Any]:
        try:
            root = ET.fromstring(xml_content)
            entry = root.find("{http://www.w3.org/2005/Atom}entry")
            if entry is not None:
                video_id = entry.find("{http://www.youtube.com/xml/schemas/2015}videoId")
                channel_id = entry.find("{http://www.youtube.com/xml/schemas/2015}channelId")
                title = entry.find("{http://www.w3.org/2005/Atom}title")
                return {
                    "platform": "youtube",
                    "video_id": video_id.text if video_id is not None else None,
                    "channel_id": channel_id.text if channel_id is not None else None,
                    "title": title.text if title is not None else None
                }
        except Exception as e:
            logger.warning(f"YouTube XML parsing warning: {e}")

        return {"platform": "youtube", "raw_xml": xml_content[:200]}
