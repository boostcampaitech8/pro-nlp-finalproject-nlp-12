from fastapi import APIRouter
from app.core.chroma import get_collection

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/chroma")
def chroma_debug():
    col_default = get_collection()  # settings.CHROMA_COLLECTION
    col_v1 = get_collection("papers_embed_v1")

    peek_default = col_default.peek()
    peek_v1 = col_v1.peek()

    return {
        "default_collection": "settings.CHROMA_COLLECTION",
        "default_ids_sample": (peek_default.get("ids") or [])[:10],

        "named_collection": "papers_embed_v1",
        "named_ids_sample": (peek_v1.get("ids") or [])[:10],
    }

@router.get("/chroma_count")
def chroma_count():
    col = get_collection("papers_embed_v1")
    return {"count": col.count()}

@router.get("/chroma_has/{pid}")
def chroma_has(pid: int):
    col = get_collection("papers_embed_v1")
    got = col.get(ids=[str(pid)], include=["metadatas"])
    return {"pid": pid, "found_ids": got.get("ids"), "metas": got.get("metadatas")}
