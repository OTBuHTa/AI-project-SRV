from __future__ import annotations

import uuid
from sqlalchemy.orm import Session

from app.models.core import Agent, Resource
from app.services.resource_health import evaluate_resource

def build_resource_context(db: Session, workspace_id: uuid.UUID, resource_id: uuid.UUID) -> dict | None:
    resource = db.get(Resource, resource_id)
    if not resource or resource.workspace_id != workspace_id:
        return None
    agent = (
        db.query(Agent)
        .filter(Agent.resource_id == resource.id, Agent.revoked_at.is_(None))
        .first()
    )
    if not agent:
        return {
            'resource_id': str(resource.id),
            'name': resource.name,
            'hostname': resource.hostname,
            'status': resource.status,
            'agent': None,
            'finding': 'No active agent is connected to this resource.',
        }
    assessment = evaluate_resource(agent, resource)
    return {
        'resource_id': str(resource.id),
        'name': resource.name,
        'hostname': resource.hostname or resource.name,
        'operating_system': resource.operating_system,
        'status': assessment['status'],
        'health_score': assessment['health_score'],
        'severity': assessment['severity'],
        'findings': assessment['findings'],
        'metrics': agent.last_metrics or {},
        'docker': (resource.metadata_json or {}).get('docker'),
        'last_seen_at': agent.last_seen_at.isoformat() if agent.last_seen_at else None,
    }

def deterministic_fallback(question: str, context: dict | None) -> str:
    if not context:
        return (
            'Локальная модель сейчас недоступна. AI Core сохранил запрос, но без выбранного '
            'ресурса не выполнял никаких инструментов. Подключение LLM можно восстановить без '
            'потери истории диалога.'
        )
    if context.get('agent') is None and 'finding' in context:
        return f"Ресурс {context.get('hostname') or context.get('name')} найден, но активный агент не подключён."
    metrics = context.get('metrics') or {}
    findings = '; '.join(context.get('findings') or [])
    return (
        f"Ресурс {context.get('hostname')} имеет статус {context.get('status')}, "
        f"health score {context.get('health_score')}/100. "
        f"CPU {metrics.get('cpu_percent', 'n/a')}%, RAM {metrics.get('memory_percent', 'n/a')}%, "
        f"disk {metrics.get('disk_percent', 'n/a')}%. Вывод: {findings}"
    )
