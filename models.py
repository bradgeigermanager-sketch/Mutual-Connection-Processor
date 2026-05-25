"""
MODULE: network_schema_models
VERSION: 1.1.0
TYPE: Database Object Mapping (SQLAlchemy ORM)
USE: Establishes identity nodes, directed relationship edges, and interaction telemetry.
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import declarative_base, relationship
import uuid

Base = declarative_base()

class IdentityNode(Base):
    """
    [SLOT: IDENTITY_REGISTRY]
    Represents an entity/node within the identity network map.
    """
    __tablename__ = "identity_nodes"

    node_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    display_name = Column(String(100), nullable=False)
    network_class = Column(String(30), default="STANDARD")  # e.g., HUMAN, PROXY, ORGANIZATION
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    edges_out = relationship("RelationshipEdge", foreign_keys="RelationshipEdge.source_id", back_populates="source")
    edges_in = relationship("RelationshipEdge", foreign_keys="RelationshipEdge.destination_id", back_populates="destination")


class RelationshipEdge(Base):
    """
    [SLOT: RELATIONSHIP_GRAPH_EDGES]
    A directed graph link connecting Source to Destination with dynamic weighting.
    """
    __tablename__ = "relationship_edges"

    edge_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), ForeignKey("identity_nodes.node_id"), nullable=False)
    destination_id = Column(String(36), ForeignKey("identity_nodes.node_id"), nullable=False)
    
    # Proximity metrics calculated by pipeline telemetry
    base_weight = Column(Float, default=0.5)      # Manual baseline or initial index
    telemetry_score = Column(Float, default=0.0)  # Calculated score based on activity density
    composite_weight = Column(Float, default=0.5) # Final normalized vector (0.0 to 1.0)
    
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Constraints to prevent duplicate mapping arrays
    __table_args__ = (UniqueConstraint('source_id', 'destination_id', name='_source_dest_uc'),)

    source = relationship("IdentityNode", foreign_keys=[source_id], back_populates="edges_out")
    destination = relationship("IdentityNode", foreign_keys=[destination_id], back_populates="edges_in")
  
