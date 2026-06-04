"""
Alert Service

Handles alert creation, triggering, and webhook notifications.
"""

import httpx
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.database import Alert, AlertConfig, NewsArticle
from app.core.config import settings


class AlertService:
    """
    Service for managing and triggering alerts.
    """

    def __init__(self):
        """Initialize the alert service."""
        self.pending_alerts = []

    async def check_alerts(
        self,
        news: List[Dict],
        configs: List[AlertConfig],
        db: Session
    ) -> List[Dict]:
        """
        Check news against alert configurations.

        Args:
            news: List of news articles with sentiment data
            configs: Alert configurations
            db: Database session

        Returns:
            List of triggered alerts
        """
        triggered = []

        for article in news:
            for config in configs:
                if not config.enabled:
                    continue

                if self._should_trigger(article, config):
                    alert = self._create_alert(article, config, db)
                    if alert:
                        triggered.append(alert)
                        self.pending_alerts.append(alert)

        return triggered

    def _should_trigger(self, news: Dict, config: AlertConfig) -> bool:
        """
        Check if a news article should trigger an alert.

        Args:
            news: News article with sentiment data
            config: Alert configuration

        Returns:
            True if should trigger
        """
        # Check instrument match
        if config.instrument != "all":
            instruments = news.get("related_instruments", [])
            if config.instrument not in instruments:
                return False

        # Check sentiment threshold
        sentiment = news.get("sentiment_score", 0)
        if config.sentiment_threshold > 0:
            if sentiment < config.sentiment_threshold:
                return False
        elif config.sentiment_threshold < 0:
            if sentiment > config.sentiment_threshold:
                return False

        # Check impact threshold
        impact = news.get("impact_score", 0)
        if impact < config.impact_threshold:
            return False

        return True

    def _create_alert(
        self,
        news: Dict,
        config: AlertConfig,
        db: Session
    ) -> Optional[Dict]:
        """
        Create a triggered alert record.

        Args:
            news: News article data
            config: Alert configuration
            db: Database session

        Returns:
            Created alert dictionary
        """
        try:
            db_alert = Alert(
                config_id=config.id,
                news_id=news.get("id"),
                headline=news.get("headline", "")[:500],
                sentiment=news.get("sentiment_score", 0),
                impact_score=news.get("impact_score", 0),
                triggered_at=datetime.now(),
                acknowledged=False,
            )
            db.add(db_alert)
            db.commit()
            db.refresh(db_alert)

            return {
                "id": db_alert.id,
                "config_id": db_alert.config_id,
                "news_id": db_alert.news_id,
                "headline": db_alert.headline,
                "sentiment": db_alert.sentiment,
                "impact_score": db_alert.impact_score,
                "triggered_at": db_alert.triggered_at.isoformat(),
                "acknowledged": db_alert.acknowledged,
            }
        except Exception as e:
            print(f"Error creating alert: {e}")
            db.rollback()
            return None

    async def send_webhook(self, alert: Dict, webhook_url: str) -> bool:
        """
        Send alert to webhook URL.

        Args:
            alert: Alert data
            webhook_url: Webhook endpoint URL

        Returns:
            True if successful
        """
        if not webhook_url:
            return False

        payload = {
            "event": "alert_triggered",
            "timestamp": datetime.now().isoformat(),
            "alert": {
                "id": alert.get("id"),
                "headline": alert.get("headline"),
                "sentiment": alert.get("sentiment"),
                "sentiment_level": "bullish" if alert.get("sentiment", 0) > 0 else "bearish",
                "impact_score": alert.get("impact_score"),
                "triggered_at": alert.get("triggered_at"),
            },
            "metadata": {
                "source": "FinAlert API",
                "version": "1.0",
            }
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Error sending webhook: {e}")
            return False

    async def process_pending_alerts(self) -> None:
        """
        Process and send pending alerts via webhooks.
        """
        for alert in self.pending_alerts:
            if alert.get("webhook_url"):
                success = await self.send_webhook(alert, alert["webhook_url"])
                if success:
                    self.pending_alerts.remove(alert)

    def get_active_alerts(self, db: Session, limit: int = 50) -> List[Alert]:
        """
        Get recent active alerts.

        Args:
            db: Database session
            limit: Maximum number of alerts to return

        Returns:
            List of alerts
        """
        return db.query(Alert).order_by(
            Alert.triggered_at.desc()
        ).limit(limit).all()

    def acknowledge_alert(self, db: Session, alert_id: int) -> bool:
        """
        Mark an alert as acknowledged.

        Args:
            db: Database session
            alert_id: Alert ID

        Returns:
            True if successful
        """
        try:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if alert:
                alert.acknowledged = True
                db.commit()
                return True
            return False
        except Exception as e:
            print(f"Error acknowledging alert: {e}")
            db.rollback()
            return False


# Global instance
alert_service = AlertService()
