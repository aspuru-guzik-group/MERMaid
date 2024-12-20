# -*- coding: utf-8 -*-
"""Janusgraph database interface."""
from typing import Any, Type
from itertools import chain
from gremlin_python.structure.graph import Edge, Graph, Vertex
from gremlin_python.driver import serializer
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.graph_traversal import GraphTraversalSource, __

from schema import VertexBase, EdgeBase, Connection

def connect(
    direction: str
    , port: int
    , graph_name: str
) -> DriverRemoteConnection:
    return DriverRemoteConnection(
        f'{direction}:{port}/gremlin'
        , graph_name
        , message_serializer=serializer.GraphSONSerializersV3d0())


def get_traversal(
    connection: DriverRemoteConnection
) -> GraphTraversalSource:
    return Graph().traversal().withRemote(connection)


def get_vertex(
    vertex: VertexBase
    , graph: GraphTraversalSource
) -> Vertex | None:
    vertex_existing = graph.V().hasLabel(vertex.label)
    for key, value in vertex.properties.items():
        vertex_existing.has(key, value)

    if vertex_existing.hasNext():
        if type(v := vertex_existing.next()) == Vertex:
            return v

    return None


def get_vertices(
    vertex_type: Type[VertexBase]
    , graph: GraphTraversalSource
) -> list[dict[str, Any]]:
    return (
        graph
        .V()
        .hasLabel(vertex_type.__name__)
        .valueMap()
        .toList()
    )


def get_vnamelist_from_db(
    vertex_type: Type[VertexBase]
    , graph: GraphTraversalSource
) -> list[str]:
    return list(chain.from_iterable(
        map(
            lambda x: x["name"]
            , get_vertices(vertex_type, graph)
        )
    ))


def get_edges(
    edge_type: Type[EdgeBase]
    , graph: GraphTraversalSource
) -> list[dict[str, Any]]:
    return (
        graph
        . E()
        . hasLabel(edge_type.__name__)
        . valueMap()
        . toList()
    )


# def get_edge(
#     edge: EdgeBase
#     , graph: GraphTraversalSource
# ) -> Edge | None:
#     source_vertex = get_vertex(edge.source) or return None
#     target_vertex = get_vertex(edge.target) or return None

#     existing_edge = (
#         graph
#         .V(source_vertex.id)
#         .outE(edge.label)
#         .where(__.inV()
#         .hasId(target_vertex.id)
#     )
#     for key, value in properties.items():
#         existing_edge = existing_edge.has(key, value)

#     if existing_edge.hasNext():
#         return existing_edge.next()

#     return None


def add_connection(
    connection: Connection
    , graph: GraphTraversalSource
) -> Edge:
    source_vertex = add_vertex(connection.source, graph)
    target_vertex = add_vertex(connection.target, graph)

    edge_traversal = (
        graph.V(source_vertex.id)
        .as_("source")
        .V(target_vertex.id)
        .as_("target")
        .addE(connection.edge.label)
        .from_("source")
    )
    
    for key, value in connection.edge.properties.items():
        edge_traversal = edge_traversal.property(key, value)

    edge = edge_traversal.next()

    if type(edge) != Edge:
        raise ValueError("""
            Unable to create the edge in the database.
        """)
    return edge


def add_vertex(
    vertex: VertexBase
    , graph: GraphTraversalSource
    , force: bool = False
) -> Vertex:
    if not force:
        if ev := get_vertex(vertex, graph):
            return ev

    new_vertex = graph.addV(vertex.label)
    for key, value in vertex.properties.items():
        new_vertex = new_vertex.property(key, value)

    if type(v := new_vertex.next()) != Vertex:
        # Unrecheable
        raise ValueError("""
            Unable to get matching vertex neither create it in the database.
        """)
    return new_vertex


def add_edge(
    edge: EdgeBase
    , graph: GraphTraversalSource
    , force: bool = False
) -> Edge:
    source = graph.V().has('name', edge.source).next()
    target = graph.V().has('name', edge.target).next()
    edge_traversal = graph.V(source.id).addE(edge.label).to(graph.V(target.id))
    for key, value in edge.properties.items():
        edge_traversal = edge_traversal.property(key, value)
    return edge_traversal.next()
