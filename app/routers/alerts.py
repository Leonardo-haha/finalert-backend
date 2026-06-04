"""
Alert API Router

Endpoints for alert configuration and management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.database import get_db, Alert, AlertConfig
from app.models.schemas import AlertConfigResponse, AlertConfigCreate, AlertResponse
from app.services.alert import alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/configs", response_model=List[AlertConfigResponse])
async def get_alert_configs(db: Session = Depends(get_db)):
    """
    Get all alert configurations.
    """
    configs = db.query(AlertConfig).order_by(AlertConfig.created_at.desc()).all()
    return configs


@router.post("/configs", response_model=AlertConfigResponse)
async def create_alert_config(
    config: AlertConfigCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new alert configuration.
    """
    db_config = AlertConfig(
        name=config.name,
        instrument=config.instrument,
        sentiment_threshold=config.sentiment_threshold,
        impact_threshold=config.impact_threshold,
        enabled=config.enabled,
        webhook_url=config.webhook_url,
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.get("/configs/{config_id}", response_model=AlertConfigResponse)
async def get_alert_config(config_id: int, db: Session = Depends(get_db)):
    """
    Get a specific alert configuration.
    """
    config = db.query(AlertConfig).filter(AlertConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return config


@router.put("/configs/{config_id}", response_model=AlertConfigResponse)
async def update_alert_config(
    config_id: int,
    config: AlertConfigCreate,
    db: Session = Depends(get_db)
):
    """
    Update an existing alert configuration.
    """
    db_config = db.query(AlertConfig).filter(AlertConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    db_config.name = config.name
    db_config.instrument = config.instrument
    db_config.sentiment_threshold = config.sentiment_threshold
    db_config.impact_threshold = config.impact_threshold
    db_config.enabled = config.enabled
    db_config.webhook_url = config.webhook_url
    db_config.updated_at = datetime.now()

    db.commit()
    db.refresh(db_config)
    return db_config


@router.delete("/configs/{config_id}")
async def delete_alert_config(config_id: int, db: Session = Depends(get_db)):
    """
    Delete an alert configuration.
    """
    db_config = db.query(AlertConfig).filter(AlertConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    db.delete(db_config)
    db.commit()
    return {"message": "Configuration deleted"}


@router.get("/history", response_model=List[AlertResponse])
async def get_alert_history(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    acknowledged: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Get alert history.
    """
    query = db.query(Alert)

    if acknowledged is not None:
        query = query.filter(Alert.acknowledged == acknowledged)

    alerts = query.order_by(
        Alert.triggered_at.desc()
    ).offset(offset).limit(limit).all()

    return alerts


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """
    Acknowledge an alert.
    """
    success = alert_service.acknowledge_alert(db, alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert acknowledged"}


@router.post("/trigger")
async def trigger_test_alert(db: Session = Depends(get_db)):
    """
    Manually trigger a test alert to verify webhook configuration.
    """
    test_alert = {
        "id": 0,
        "config_id": 0,
        "headline": "Test Alert: Market Moved Significantly",
        "sentiment": 0.75,
        "impact_score": 85,
        "triggered_at": datetime.now().isoformat(),
        "webhook_url": None,
    }

    configs = db.query(AlertConfig).filter(AlertConfig.enabled == True).all()
    triggered = []

    for config in configs:
        if config.webhook_url:
            test_alert["webhook_url"] = config.webhook_url
            success = await alert_service.send_webhook(test_alert, config.webhook_url)
            triggered.append({
                "config_id": config.id,
                "name": config.name,
                "webhook_url": config.webhook_url,
                "success": success,
            })

    return {"test_results": triggered}
