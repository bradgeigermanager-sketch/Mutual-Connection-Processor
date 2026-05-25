"""
MODULE: network_api_router
VERSION: 1.0.2
TYPE: Service Router Layer (FastAPI)
USE: Exposes standard entry points for calculating mutual connections.
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI(title="Network Triangulation Service", version="1.0.2")

# --- Pydantic Presentation Schemas ---
class ConnectionVector(BaseModel):
    origin_to_proxy: float
    target_to_proxy: float

class MutualConnectionDetail(BaseModel):
    mutual_node_id: str
    display_name: str
    vector_strengths: ConnectionVector
    composite_score: float

class TriangulationResponse(BaseModel):
    status: str
    origin_id: str
    target_id: str
    mutual_count: int
    network_overlap_index: float
    shared_neighborhood: List[MutualConnectionDetail]

# --- Mock Context Loader (In-Production, this queries the DB models above) ---
def mock_load_adjacency_matrix() -> Dict[str, Dict[str, float]]:
    return {
        "id_brad":   {"id_sarah": 0.95, "id_john": 0.40, "id_alex": 0.85},
        "id_target": {"id_sarah": 0.80, "id_john": 0.90, "id_marcus": 0.60},
        "id_sarah":  {"id_brad": 0.95, "id_target": 0.80},
        "id_john":   {"id_brad": 0.40, "id_target": 0.90},
        "id_alex":   {"id_brad": 0.85},
        "id_marcus": {"id_target": 0.60}
    }

# --- Router Endpoints ---
@app.get("/api/v1/network/triangulate", response_model=TriangulationResponse)
async def get_mutual_connections(
    origin_id: str = Query(..., description="The unique ID of the requesting user (I)"),
    target_id: str = Query(..., description="The unique ID of the individual being scanned (You)"),
    min_threshold: float = Query(0.0, description="Minimum affinity filter threshold")
):
    graph = mock_load_adjacency_matrix()
    
    if origin_id not in graph or target_id not in graph:
        raise HTTPException(status_code=404, detail="Specified origin or target node identity not found.")
    
    # 1. Isolate overlaps
    origin_set = {k for k, v in graph[origin_id].items() if v >= min_threshold}
    target_set = {k for k, v in graph[target_id].items() if v >= min_threshold}
    mutuals = origin_set.intersection(target_set)
    
    # 2. Compile and score shared neighborhood array
    shared_list = []
    # Simple registry map for names in mock data setup
    names = {"id_sarah": "Sarah Connor", "id_john": "John Connor", "id_alex": "Alex Mercer"}
    
    for m_node in mutuals:
        w_orig = graph[origin_id][m_node]
        w_targ = graph[target_id][m_node]
        comp = round((w_orig * w_targ) ** 0.5, 4)
        
        shared_list.append(
            MutualConnectionDetail(
                mutual_node_id=m_node,
                display_name=names.get(m_node, "Unknown Node"),
                vector_strengths=ConnectionVector(origin_to_proxy=w_orig, target_to_proxy=w_targ),
                composite_score=comp
            )
        )
    
    # Sort descending by calculated score
    shared_list.sort(key=lambda x: x.composite_score, reverse=True)
    
    union_len = len(origin_set.union(target_set))
    jaccard_index = round(len(mutuals) / union_len, 4) if union_len > 0 else 0.0
    
    return TriangulationResponse(
        status="SUCCESS",
        origin_id=origin_id,
        target_id=target_id,
        mutual_count=len(mutuals),
        network_overlap_index=jaccard_index,
        shared_neighborhood=shared_list
    )

