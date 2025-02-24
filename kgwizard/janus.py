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
    """
    Establish a connection to a Gremlin server.

    :param direction: The network direction (e.g., 'ws' or 'wss') used for the connection.
    :type direction: str
    :param port: The port number on which the Gremlin server is running.
    :type port: int
    :param graph_name: The name of the graph to connect to.
    :type graph_name: str
    :return: A `DriverRemoteConnection` instance for interacting with the Gremlin server.
    :rtype: DriverRemoteConnection
    """
    return DriverRemoteConnection(
        f'{direction}:{port}/gremlin'
        , graph_name
        , message_serializer=serializer.GraphSONSerializersV3d0())


def get_traversal(
    connection: DriverRemoteConnection
) -> GraphTraversalSource:
    """
    Create a graph traversal source using a remote connection.

    :param connection: The remote connection to a Gremlin server.
    :type connection: DriverRemoteConnection
    :return: A `GraphTraversalSource` instance for executing Gremlin queries.
    :rtype: GraphTraversalSource
    """
    return Graph().traversal().withRemote(connection)


def get_vertex(
    vertex: VertexBase
    , graph: GraphTraversalSource
) -> Vertex | None:
    """
    Retrieve an existing vertex from the graph based on its label and properties.

    :param vertex: The vertex object containing the label and properties to search for.
    :type vertex: VertexBase
    :param graph: The graph traversal source used to execute the query.
    :type graph: GraphTraversalSource
    :return: The matching vertex if found, otherwise ``None``.
    :rtype: Vertex | None
    """
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
    """
    Retrieve all vertices of a specified type from the graph.

    :param vertex_type: The class representing the vertex type to query.
    :type vertex_type: Type[VertexBase]
    :param graph: The graph traversal source used to execute the query.
    :type graph: GraphTraversalSource
    :return: A list of dictionaries representing the properties of matching vertices.
    :rtype: list[dict[str, Any]]
    """
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
    """
    Retrieve a list of vertex names from the database for a given vertex type.

    :param vertex_type: The class representing the vertex type to query.
    :type vertex_type: Type[VertexBase]
    :param graph: The graph traversal source used to execute the query.
    :type graph: GraphTraversalSource
    :return: A list of vertex names extracted from the database.
    :rtype: list[str]
    """
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
    """
    Retrieve all edges of a specified type from the graph.

    :param edge_type: The class representing the edge type to query.
    :type edge_type: Type[EdgeBase]
    :param graph: The graph traversal source used to execute the query.
    :type graph: GraphTraversalSource
    :return: A list of dictionaries representing the properties of matching edges.
    :rtype: list[dict[str, Any]]
    """
    return (
        graph
        . E()
        . hasLabel(edge_type.__name__)
        . valueMap()
        . toList()
    )


def add_connection(
    connection: Connection
    , graph: GraphTraversalSource
) -> Edge:
    """
    Add a connection (edge) between two vertices in the graph.

    :param connection: The connection object containing source, target, and edge properties.
    :type connection: Connection
    :param graph: The graph traversal source used to execute the query.
    :type graph: GraphTraversalSource
    :return: The created edge in the graph.
    :rtype: Edge
    :raises ValueError: If the edge could not be created in the database.
    """
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
    """
    Add a vertex to the graph, optionally avoiding duplication.

    :param vertex: The vertex object containing the label and properties.
    :type vertex: VertexBase
    :param graph: The graph traversal source used to execute the query.
    :type graph: GraphTraversalSource
    :param force: If ``True``, always creates a new vertex. If ``False``, checks for an existing vertex first.
    :type force: bool, optional
    :return: The created or retrieved vertex.
    :rtype: Vertex
    :raises ValueError: If the vertex could not be retrieved or created.
    """
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
    """
    Add an edge between two vertices in the graph.

    :param edge: The edge object containing the label, source, target, and properties.
    :type edge: EdgeBase
    :param graph: The graph traversal source used to execute the query.
    :type graph: GraphTraversalSource
    :param force: If ``True``, always creates a new edge. If ``False``, behavior is undefined
                  (consider implementing a check for existing edges).
    :type force: bool, optional
    :return: The created edge.
    :rtype: Edge
    :raises StopIteration: If the source or target vertex does not exist in the graph.
    """
    source = graph.V().has('name', edge.source).next()
    target = graph.V().has('name', edge.target).next()
    edge_traversal = graph.V(source.id).addE(edge.label).to(graph.V(target.id))
    for key, value in edge.properties.items():
        edge_traversal = edge_traversal.property(key, value)
    return edge_traversal.next()
