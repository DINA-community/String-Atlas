import os
import redis
from qdrant_client import QdrantClient

redis_host = os.environ.get("REDIS_HOST", "redis2026")
redis_port = os.environ.get("REDIS_PORT", 6379)
redis_client =  redis.Redis(host=redis_host, port=redis_port, decode_responses=True)


qdrant_host = os.environ.get("QDRANT_HOST", "qdrant2026")
qdrant_port = int(os.environ.get("QDRANT_PORT", 6333))
qdrant_client = QdrantClient(
    host=qdrant_host,
    port=qdrant_port
)
