# StrikeEdge Enterprise Architecture Baseline

- Edge: CloudFront + static web distribution.
- API: FastAPI behind API Gateway.
- Realtime: websocket channels for scan and alert fanout.
- Data: Aurora + Redis + queue workers for ingestion and screening.
- AI: orchestrator + specialist agents with structured outputs.
