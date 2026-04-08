from typing import List, Union
import numpy as np
from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer
from app.config import settings
from app.core.redis_client import redis_client
from app.core.logger import logger
import json
import hashlib


class EmbeddingService:
    def __init__(self):
        self.use_openai = bool(settings.OPENAI_API_KEY)

        if self.use_openai:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_EMBEDDING_MODEL
            logger.info(f"Using OpenAI embeddings: {self.model}")
        else:
            logger.info(f"Using local embedding model: {settings.LOCAL_EMBEDDING_MODEL}")
            self.model = SentenceTransformer(settings.LOCAL_EMBEDDING_MODEL)

        self.cache_ttl = 3600  # 1 hour cache

    async def embed(self, text: str) -> List[float]:
        """Generate embedding for single text"""

        # Check cache
        cache_key = self._get_cache_key(text)
        cached = await redis_client.get(cache_key)

        if cached:
            logger.debug(f"Cache hit for embedding: {cache_key[:16]}...")
            return json.loads(cached)

        # Generate embedding
        if self.use_openai:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text[:8000]  # Truncate to max tokens
            )
            embedding = response.data[0].embedding
        else:
            embedding = self.model.encode(text).tolist()

        # Cache result
        await redis_client.setex(
            cache_key,
            self.cache_ttl,
            json.dumps(embedding)
        )

        return embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""

        if not texts:
            return []

        logger.info(f"Generating embeddings for {len(texts)} texts")

        if self.use_openai:
            # OpenAI has batch limits
            batch_size = 100
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(embeddings)

            return all_embeddings
        else:
            # Local model can handle all at once
            embeddings = self.model.encode(texts)
            return embeddings.tolist()

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"embed:{self.model}:{text_hash}"