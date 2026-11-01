from src.config import RETRIEVAL_K


def get_retriever(vector_store, selected_sources=None, k=RETRIEVAL_K):
    if selected_sources is not None and not selected_sources:
        raise ValueError("Select at least one indexed document.")
    search_kwargs = {"k": k}
    if selected_sources is not None:
        search_kwargs["filter"] = {"source": {"$in": list(selected_sources)}}
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs,
    )
