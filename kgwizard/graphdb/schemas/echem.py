# -*- coding: utf-8 -*-
"""Module containing the classes and types to create the desired graph database
schema."""
from dataclasses import dataclass, fields
import inspect
import json
from typing import Any, Generic, TypeVar, Type
import sys
import types

def sink(_: Any) -> None: pass

@dataclass
class VertexBase:
    @property
    def label(self) -> str:
        return self.__class__.__name__

    @property
    def properties(self) -> dict:
        return {
            field.name: getattr(self, field.name)
            for field in fields(self)
        }

    def to_json(self) -> str:
        return json.dumps({
            "label": self.label,
            "properties": self.properties
        })

    @classmethod
    def from_dict(
        cls: Type['VertexBase'],
        properties: dict[str, str]
    ) -> 'VertexBase':
        type_dict = get_types_from_class(cls)

        typed_properties = {
            k: apply_type_from_list(type_dict[k], v)
            for k, v
            in properties.items()}
        return cls(**typed_properties)


TSource = TypeVar("TSource", bound=VertexBase)
TTarget = TypeVar("TTarget", bound=VertexBase)


@dataclass
class EdgeBase(Generic[TSource, TTarget]):
    source: TSource
    target: TTarget

    @property
    def label(self) -> str:
        return self.__class__.__name__

    @property
    def properties(self) -> dict[str, Any]:
        return {
            field.name: getattr(self, field.name) 
            for field in fields(self)
            if field.name not in ("source", "target")
        }

    def to_json(self) -> str:
        return json.dumps({
            "source": self.source.label,
            "target": self.target.label,
            "label": self.label,
            "properties": self.properties
        })

    @classmethod
    def from_dict(
        cls: Type['EdgeBase'],
        properties: dict[str, str],
        source: TSource,
        target: TTarget
    ) -> 'EdgeBase':
        type_dict = get_types_from_class(cls)

        typed_properties = {
            k: apply_type_from_list(type_dict[k], v)
            for k, v
            in properties.items()}
        return cls(
            source=source,
            target=target,
            **typed_properties)


ELabel = TypeVar("ELabel", bound=EdgeBase)


@dataclass
class Connection:
    source: VertexBase
    target: VertexBase
    edge: EdgeBase

    @classmethod
    def from_dict(
        cls: type["Connection"]
        , conn_dict: dict[str, Any]
    ) -> "Connection":
        return cls(
            source=build_node_from_dict(conn_dict["source"])
            , target=build_node_from_dict(conn_dict["target"])
            , edge=build_edge_from_dict(conn_dict)
        )


def get_type_from_annotation(
    annotation_type: types.UnionType | type
) -> list[type]:
    if hasattr(annotation_type, '__args__'):
        non_none_types = [t if t is not type(None) else sink for t in annotation_type.__args__]
    else:
        non_none_types = [annotation_type]
    return non_none_types


def get_types_from_class(
    cls: VertexBase | EdgeBase
) -> dict[str, list[type]]:
    return {
        k: get_type_from_annotation(v) for k, v in cls.__annotations__.items()
    }


def apply_type_from_list(
    type_list: list[type]
    , value: str
) -> str | Any:
    if type_list:
        for t in type_list:
            try: return t(value)
            except (ValueError, TypeError): continue
    return value


def build_node_from_dict(
    node_dict: dict[str, Any]
) -> VertexBase:
    prop: dict[str, str]
    try: 
        prop = node_dict["properties"]
    except KeyError:
        prop = {k: v for k, v in node_dict.items() if k != "label"}
    return VERTEX_CLASSES[node_dict["label"]].from_dict(prop)


def build_edge_from_dict(
    edge_dict: dict[str, Any]
) -> EdgeBase:
    return EDGE_CLASSES[edge_dict["label"]].from_dict(
        properties=edge_dict["properties"],
        source=VERTEX_CLASSES[edge_dict["source"]["label"]],
        target=VERTEX_CLASSES[edge_dict["target"]["label"]]
    )
    

@dataclass
class Study(VertexBase):
    name: str


@dataclass
class Quantity(VertexBase):
    unit: str | None
    value: float


@dataclass
class Compound(VertexBase):
    name: str | None


@dataclass
class Material(VertexBase):
    name: str


@dataclass
class Atmosphere(VertexBase):
    name: str | None


@dataclass
class Comment(VertexBase):
    text: str


@dataclass 
class MaterialFamily(VertexBase):
    name: str


@dataclass
class Reaction(VertexBase):
    uuid: str


TEdgeCompound = EdgeBase[Reaction, Compound]
TEdgeMaterial = EdgeBase[Reaction, Material]
TEdgeQuantity = EdgeBase[Reaction, Quantity]


@dataclass
class HasElectrolyte(TEdgeCompound):
    value: float | None = None
    unit: str | None = None


@dataclass
class HasProduct(TEdgeCompound):
    value: float | None = None
    unit: str | None = None


@dataclass
class HasReactant(TEdgeCompound):
    value: float | None = None
    unit: str | None = None


@dataclass
class HasSolvent(TEdgeCompound):
    value: float | None = None
    unit: str | None = None


@dataclass
class HasAnode(TEdgeMaterial):
    pass


@dataclass
class HasCathode(TEdgeMaterial):
    pass


@dataclass
class HasDuration(TEdgeQuantity):
    pass


@dataclass
class HasTemperature(TEdgeQuantity):
    pass


@dataclass
class HasCurrent(TEdgeQuantity):
    pass

@dataclass
class HasComment(EdgeBase[Reaction, Comment]):
    pass


@dataclass
class HasAtmosphere(EdgeBase[Reaction, Atmosphere]):
    pass

@dataclass
class HasReaction(EdgeBase[Study, Reaction]):
    pass

@dataclass
class IsMemberOfFamily(EdgeBase[Material, MaterialFamily]):
    pass


VERTEX_CLASSES = dict(
    (name, obj) for name, obj
    in inspect.getmembers(sys.modules[__name__])
    if inspect.isclass(obj) and issubclass(obj, VertexBase)
)


EDGE_CLASSES = dict(
    (name, obj) for name, obj
    in inspect.getmembers(sys.modules[__name__])
    if inspect.isclass(obj) and issubclass(obj, EdgeBase)
)
