from fastapi import APIRouter
from elasticsearch import Elasticsearch
from app.core.config import settings


router = APIRouter(prefix="/search", tags=["Search"])

es = Elasticsearch(settings.ELASTICSEARCH_URL)

@router.get("/messages")
def search_messages(query: str, conversation_id: str | None = None):
    must_conditions = []

    must_conditions.append({
        "bool": {
            "should": [
                {"match": {"content": {"query": query, "fuzziness": "AUTO"}}},
                {
                    "match_phrase_prefix": {"content": query}
                }
            ]
        }})

    if conversation_id:
        must_conditions.append({
            "term": {
                "conversation_id.keyword": conversation_id
            }
        })

    body = {
        "query": {
            "bool": {
                "must": must_conditions
            }
        }
    }

    res = es.search(index="messages", body=body)

    return [
        {
            "id": hit["_source"]["id"],
            "conversation_id": hit["_source"]["conversation_id"],
            "sender_id": hit["_source"]["sender_id"],
            "content": hit["_source"]["content"],
            "created_at": hit["_source"]["created_at"],
            "reply_to_message_id": hit["_source"]["reply_to_message_id"],
            "reply_to": hit["_source"]["reply_to"],
            "is_deleted": hit["_source"]["is_deleted"],
            "deleted_at": hit["_source"]["deleted_at"],
        }
        for hit in res["hits"]["hits"]
    ]
