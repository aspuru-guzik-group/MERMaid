# -*- coding: utf-8 -*-
"""Module containing the abstract base classes for a graph database schema."""
from dataclasses import dataclass, fields
from abc import ABC, abstractmethod
import json
from typing import Any, Generic, TypeVar, Type


@dataclass
class VertexBase(ABC):
    """Abstract base class for a graph database vertex."""

    @property
    @abstractmethod
    def label(self) -> str:
        """Returns the label of the vertex."""
        pass

    @property
    @abstractmethod
    def properties(self) -> dict:
        """Returns the properties of the vertex as a dictionary."""
        pass

    def to_json(self) -> str:
        """Serializes the vertex to JSON format."""
        return json.dumps({
            "label": self.label,
            "properties": self.properties
        })

    @classmethod
    @abstractmethod
    def from_dict(cls: Type["VertexBase"], properties: dict[str, str]) -> "VertexBase":
        """Creates a vertex instance from a dictionary of properties."""
        pass


TSource = TypeVar("TSource", bound=VertexBase)
TTarget = TypeVar("TTarget", bound=VertexBase)


@dataclass
class EdgeBase(Generic[TSource, TTarget], ABC):
    """Abstract base class for a graph database edge."""
    source: TSource
    target: TTarget

    @property
    @abstractmethod
    def label(self) -> str:
        """Returns the label of the edge."""
        pass

    @property
    @abstractmethod
    def properties(self) -> dict[str, Any]:
        """Returns the properties of the edge as a dictionary."""
        pass

    def to_json(self) -> str:
        """Serializes the edge to JSON format."""
        return json.dumps({
            "source": self.source.label,
            "target": self.target.label,
            "label": self.label,
            "properties": self.properties
        })

    @classmethod
    @abstractmethod
    def from_dict(
        cls: Type["EdgeBase"],
        properties: dict[str, str],
        source: TSource,
        target: TTarget
    ) -> "EdgeBase":
        """Creates an edge instance from a dictionary of properties."""
        pass


@dataclass
class Connection(ABC):
    """Abstract base class representing a connection between two vertices."""
    source: VertexBase
    target: VertexBase
    edge: EdgeBase

    @classmethod
    @abstractmethod
    def from_dict(cls: type["Connection"], conn_dict: dict[str, Any]) -> "Connection":
        """Creates a connection from a dictionary representation."""
        pass
