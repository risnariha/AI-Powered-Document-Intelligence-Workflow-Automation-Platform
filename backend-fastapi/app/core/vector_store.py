from qdrant_client import QdrantClient
from qdrant_client.http import models
from typing import List, Dict, Any, Optional
import uuid

from app.config import settings
from app.core.logger import logger


class VectorStore:
    """Qdrant vector database wrapper"""

    def __init__(self):
        self.client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        self.collection_name = settings.QDRANT_COLLECTION
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure collection exists"""
        try:
            collections = self.client.get_collections()
            if not any(c.name == self.collection_name for c in collections.collections):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=settings.VECTOR_SIZE,
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created vector collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")

    async def upsert(self, points: List[Dict[str, Any]]):
        """Insert or update vectors"""
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=point.get("id", str(uuid.uuid4())),
                        vector=point["vector"],
                        payload=point.get("payload", {})
                    )
                    for point in points
                ]
            )
            logger.debug(f"Upserted {len(points)} vectors")
        except Exception as e:
            logger.error(f"Failed to upsert vectors: {e}")

    async def search(
            self,
            query_vector: List[float],
            limit: int = 10,
            score_threshold: float = 0.7,
            filter_conditions: Optional[Dict] = None
    ) -> List[Dict]:
        """Search for similar vectors"""
        try:
            filter_obj = None
            if filter_conditions:
                filter_obj = models.Filter(
                    must=[
                        models.FieldCondition(
                            key=k,
                            match=models.MatchValue(value=v)
                        )
                        for k, v in filter_conditions.items()
                    ]
                )

            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filter_obj
            )

            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload
                }
                for hit in results
            ]
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            return []

    async def delete(self, point_ids: List[str]):
        """Delete vectors by ID"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsSelector(points=point_ids)
            )
            logger.debug(f"Deleted {len(point_ids)} vectors")
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")


vector_store = VectorStore()