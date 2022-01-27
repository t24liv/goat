from enum import Enum, IntEnum
from typing import Dict, List, Optional, Union

from geojson_pydantic.features import Feature, FeatureCollection
from geojson_pydantic.geometries import MultiPolygon, Polygon
from pydantic import BaseModel, root_validator

"""
Body of the request
"""


class ModusEnum(int, Enum):
    default = 1
    scenario = 2
    comparision = 3

    @classmethod
    def __get_validators__(cls):
        cls.lookup = {v: k.value for v, k in cls.__members__.items()}
        yield cls.validate

    @classmethod
    def validate(cls, v):
        try:
            return cls.lookup[v]
        except KeyError:
            raise ValueError("invalid modus value")


class IsochroneBase(BaseModel):
    user_id: int
    minutes: int
    speed: float
    n: int
    modus: ModusEnum
    routing_profile: str
    max_cutoff: Optional[int] = None

    @root_validator
    def compute_values(cls, values):
        """Compute values."""
        # convert speed from km/h to m/s
        values["speed"] = values["speed"] / 3.6
        # convert minutes to seconds (max_cutoff is in seconds)
        values["max_cutoff"] = values["minutes"] * 60
        return values


class IsochroneSingle(IsochroneBase):
    x: float
    y: float
    concavity: float
    scenario_id: int

    class Config:
        schema_extra = {
            "example": {
                "user_id": 0,
                "minutes": 10,
                "speed": 5,
                "n": 2,
                "modus": "default",
                "x": 11.5696284,
                "y": 48.1502132,
                "concavity": 0.00003,
                "routing_profile": "walking_standard",
                "scenario_id": 0,
            }
        }


class IsochroneMulti(IsochroneBase):
    alphashape_parameter: str
    region_type: str
    region: List[str]
    scenario_id: int
    amenities: List[str]

    class Config:
        schema_extra = {
            "example": {
                "user_id": 119,
                "minutes": 10,
                "speed": 5,
                "n": 2,
                "modus": "default",
                "alphashape_parameter": "0.00003",
                "region_type": "study_area",
                "region": ["Altstadt-Mitte"],
                "routing_profile": "walking_standard",
                "scenario_id": 0,
                "amenities": [
                    "nursery",
                    "kindergarten",
                    "grundschule",
                    "realschule",
                    "werkrealschule",
                    "gymnasium",
                    "library",
                ],
            }
        }


class IsochroneMultiCountPois(BaseModel):
    amenities: List[str]
    minutes: int
    modus: str
    region: str
    region_type: str
    scenario_id: str
    speed: int
    user_id: int

    class Config:
        schema_extra = {
            "example": {
                "region_type": "study_area",
                "region": "POINT(7.8383676846236225 48.02455137958364)",
                "user_id": 120,
                "scenario_id": "0",
                "modus": "default",
                "minutes": 10,
                "speed": 5,
                "amenities": [
                    "nursery",
                    "kindergarten",
                    "grundschule",
                    "realschule",
                    "werkrealschule",
                    "gymnasium",
                    "library",
                ],
            }
        }


class IsochroneExport(BaseModel):
    """Isochrone export DTO"""

    return_type: str
    objectid: int


"""
Response DTOs
"""

# Shared properties
class IsochronePropertiesShared(BaseModel):
    gid: int
    step: int
    modus: int
    speed: int
    objectid: int
    parent_id: int
    coordinates: List


class IsochroneSingleProperties(IsochronePropertiesShared):
    starting_point: str
    sum_pois: Dict


# Single Isochrone
class IsochroneSingleFeature(Feature):
    geometry: Union[Polygon, MultiPolygon]
    properties: IsochroneSingleProperties


class IsochroneSingleCollection(FeatureCollection):
    features: List[IsochroneSingleFeature]


# Multi Isochrone
class IsochroneMultiProperties(IsochronePropertiesShared):
    userid: str
    population: List
    scenario_id: int
    routing_profile: str
    alphashape_parameter: str


class IsochroneMultiFeature(Feature):
    geometry: Union[Polygon, MultiPolygon]
    properties: IsochroneMultiProperties


class IsochroneMultiCollection(FeatureCollection):
    features: List[IsochroneMultiFeature]


# Count pois (multi-isochrone) TODO: THERE IS NO NEED IN THE CLIENT TO HAVE THIS AS FEATURE COLLECTION


class IsochroneMultiCountPoisProperties(BaseModel):
    gid: int
    count_pois: int
    region_name: str


class IsochroneMultiCountPoisFeature(Feature):
    geometry: Union[Polygon, MultiPolygon]
    properties: IsochroneMultiCountPoisProperties


class IsochroneMultiCountPoisCollection(FeatureCollection):
    features: List[IsochroneMultiCountPoisFeature]