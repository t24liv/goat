from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, root_validator, validator
from sqlmodel import SQLModel

from src.schemas.isochrone import (
    CalculationTypes,
    IsochroneAccessMode,
    IsochroneCyclingProfile,
    IsochroneScenario,
    IsochroneWalkingProfile,
)


class ComputePoiUser(SQLModel):
    data_upload_id: int


class HeatmapWalkingBulkResolution(int, Enum):
    """H3 Resolution Bulk."""

    resolution = 6


class HeatmapWalkingCalculationResolution(int, Enum):
    """H3 Resolution Calculation."""

    resolution = 10


class HeatmapMode(Enum):
    walking = "walking"
    cycking = "cycling"
    
class HeatmapProfile(Enum):
    standard = "standard"


class HeatmapType(Enum):
    modified_gaussian = "modified_gaussian"
    combined_cumulative_modified_gaussian = "combined_cumulative_modified_gaussian"
    connectivity = "connectivity"
    cumulative = "cumulative"
    closest_average = "closest_average"


class ReturnTypeHeatmap(Enum):
    geojson = "geojson"
    csv = "csv"
    geobuf = "geobuf"
    pbf = "pbf"
    shapefile = "shapefile"


class AnalysisUnit(Enum):
    hexagon = "hexagon"
    square = "square"
    building = "building"
    point = "point"


class HeatmapBaseSpeed(Enum):
    """Speed in km/h"""

    walking = 5.0
    cycling = 15.0


class HeatmapBase(BaseModel):
    max_traveltime: int
    weight: int


class HeatmapConfigGravity(HeatmapBase):
    sensitivity: int


class HeatmapConfigCombinedGravity(HeatmapConfigGravity):
    static_traveltime: int


class HeatmapClosestAverage(HeatmapBase):
    max_count: int


class HeatmapConfigConnectivity(BaseModel):
    max_traveltime: int = Field(None, le=25)


class HeatmapSettings(BaseModel):
    """Setting for different heatmap types"""

    study_area_ids: List[int]
    resolution: int = Field(None, ge=6, le=10)
    mode: HeatmapMode = Field(HeatmapMode.walking.value, description="Isochrone Mode")
    walking_profile: Optional[IsochroneWalkingProfile] = Field(
        IsochroneWalkingProfile.STANDARD.value,
        description="Walking profile.",
    )
    cycling_profile: Optional[IsochroneCyclingProfile] = Field(
        IsochroneCyclingProfile.STANDARD.value,
        description="Cycling profile.",
    )
    scenario: Optional[IsochroneScenario] = Field(
        {
            "id": 1,
            "modus": CalculationTypes.default,
        },
        description="Isochrone scenario parameters. Only supported for POIs and Building scenario at the moment",
    )
    analysis_unit: AnalysisUnit = Field(
        AnalysisUnit.hexagon, description="Analysis unit for the heatmap"
    )
    analysis_unit_size: Optional[int] = Field(10, description="Size of the analysis")
    heatmap_type: HeatmapType = Field(
        HeatmapType.modified_gaussian, description="Type of heatmap to compute"
    )
    heatmap_config: dict

    @validator("heatmap_config")
    def heatmap_config_schema_connectivity(cls, value, values):

        if values["heatmap_type"] != HeatmapType.connectivity:
            return value
        else:
            return HeatmapConfigConnectivity(**value)

    @validator("heatmap_config")
    def heatmap_config_schema(cls, value, values):
        """
        Validate each part of heatmap_config against validator class corresponding to heatmap_type
        """
        if values["heatmap_type"] == HeatmapType.connectivity:
            # This validator should not apply to connectivity heatmap
            return value

        validator_classes = {
            "modified_gaussian": HeatmapConfigGravity,
            "combined_cumulative_modified_gaussian": HeatmapConfigCombinedGravity,
            "closest_average": HeatmapClosestAverage,
        }

        heatmap_type = values["heatmap_type"].value
        if heatmap_type not in validator_classes.keys():
            raise ValueError(f"Validation for type {heatmap_type} not found.")
        validator_class = validator_classes[heatmap_type]
        heatmap_config = value
        for category in heatmap_config:
            validator_class(**heatmap_config[category])

        return value

    # TODO: Remove this validator when we have a proper schema for heatmap_config
    @validator("heatmap_config", pre=True)
    def pass_poi_to_heatmap_config(cls, value):
        poi = value.get("poi")
        if poi:
            return poi
        else:
            return value

class BulkTravelTime(BaseModel):
    west: list[int]
    north: list[int]
    zoom: list[int]
    width: list[int]
    height: list[int]
    grid_ids: list[int]
    travel_times: list[list[int]]


"""
Body of the request
"""
request_examples_ = {
    "compute_poi_user": {"data_upload_id": 1},
    "heatmap_configuration": """{"supermarket":{"sensitivity":250000,"weight":1}}""",
}

request_examples = {
    "modified_gaussian_hexagon_10": {
        "summary": "Gravity heatmap with hexagon resolution 10",
        "value": {
            "mode": "walking",
            "study_area_ids": [91620000],
            "walking_profile": "standard",
            "scenario": {
                "id": 1,
                "name": "default",
            },
            "heatmap_type": "modified_gaussian",
            "analysis_unit": "hexagon",
            "resolution": 10,
            "heatmap_config": {
                "poi": {
                    "atm": {"weight": 1, "sensitivity": 250000, "max_traveltime": 20},
                    "bar": {"weight": 1, "sensitivity": 250000, "max_traveltime": 20},
                    "gym": {"weight": 1, "sensitivity": 350000, "max_traveltime": 20},
                },
            },
        },
    },
    "connectivity_heatmap_6": {
        "summary": "Connectivity heatmap with hexagon resolution 6",
        "value": {
            "mode": "walking",
            "study_area_ids": [91620000],
            "walking_profile": "standard",
            "scenario": {
                "id": 1,
                "name": "default",
            },
            "heatmap_type": "connectivity",
            "analysis_unit": "hexagon",
            "resolution": 6,
            "heatmap_config": {
                "max_traveltime": 20,
            },
        },
    },
    "modified_gaussian_hexagon_9": {
        "summary": "Gravity heatmap with hexagon resolution 9",
        "value": {
            "mode": "walking",
            "study_area_ids": [91620000],
            "walking_profile": "standard",
            "scenario": {
                "id": 1,
                "name": "default",
            },
            "heatmap_type": "modified_gaussian",
            "analysis_unit": "hexagon",
            "resolution": 9,
            "heatmap_config": {
                "poi": {
                    "atm": {"weight": 1, "sensitivity": 250000, "max_traveltime": 20},
                    "bar": {"weight": 1, "sensitivity": 250000, "max_traveltime": 20},
                    "gym": {"weight": 1, "sensitivity": 350000, "max_traveltime": 20},
                },
            },
        },
    },
    "modified_gaussian_hexagon_6": {
        "summary": "Gravity heatmap with hexagon resolution 6",
        "value": {
            "mode": "walking",
            "study_area_ids": [91620000],
            "walking_profile": "standard",
            "scenario": {
                "id": 1,
                "name": "default",
            },
            "heatmap_type": "modified_gaussian",
            "analysis_unit": "hexagon",
            "resolution": 6,
            "heatmap_config": {
                "poi": {
                    "atm": {"weight": 1, "sensitivity": 250000, "max_traveltime": 20},
                    "bar": {"weight": 1, "sensitivity": 250000, "max_traveltime": 20},
                    "gym": {"weight": 1, "sensitivity": 350000, "max_traveltime": 20},
                },
            },
        },
    },
    "combined_modified_gaussian_hexagon_6": {
        "summary": "Combined Gravity heatmap with hexagon resolution 6",
        "value": {
            "mode": "walking",
            "study_area_ids": [91620000],
            "walking_profile": "standard",
            "scenario": {
                "id": 1,
                "name": "default",
            },
            "heatmap_type": "combined_cumulative_modified_gaussian",
            "analysis_unit": "hexagon",
            "resolution": 6,
            "heatmap_config": {
                "poi": {
                    "atm": {
                        "weight": 1,
                        "sensitivity": 250000,
                        "max_traveltime": 20,
                        "static_traveltime": 5,
                    },
                    "bar": {
                        "weight": 1,
                        "sensitivity": 250000,
                        "max_traveltime": 20,
                        "static_traveltime": 5,
                    },
                    "gym": {
                        "weight": 1,
                        "sensitivity": 350000,
                        "max_traveltime": 20,
                        "static_traveltime": 5,
                    },
                },
            },
        },
    },
    "closest_average_hexagon_10": {
        "summary": "Closest average heatmap with hexagon resolution 10",
        "value": {
            "mode": "walking",
            "study_area_ids": [91620000],
            "walking_profile": "standard",
            "scenario": {
                "id": 1,
                "name": "default",
            },
            "heatmap_type": "closest_average",
            "analysis_unit": "hexagon",
            "resolution": 10,
            "heatmap_config": {
                "poi": {
                    "atm": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "bar": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "gym": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "pub": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "bank": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "cafe": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "fuel": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "park": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "yoga": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "hotel": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "bakery": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "cinema": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "forest": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "museum": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "butcher": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "dentist": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "nursery": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "bus_stop": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "pharmacy": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "post_box": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "fast_food": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "gymnasium": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "nightclub": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "recycling": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "tram_stop": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "playground": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "realschule": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "restaurant": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "car_sharing": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "convenience": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "grundschule": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "hypermarket": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "marketplace": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "post_office": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "supermarket": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "bike_sharing": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "discount_gym": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "kindergarten": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "rail_station": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "subway_entrance": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "charging_station": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "organic_supermarket": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "discount_supermarket": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "general_practitioner": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "swimming_pool_outdoor": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "hauptschule_mittelschule": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                },
            },
        },
    },
    "closest_average_hexagon_9": {
        "summary": "Closest average hexagon with resolution 9",
        "value": {
            "mode": "walking",
            "study_area_ids": [91620000],
            "walking_profile": "standard",
            "scenario": {
                "id": 1,
                "name": "default",
            },
            "heatmap_type": "closest_average",
            "analysis_unit": "hexagon",
            "resolution": 9,
            "heatmap_config": {
                "poi": {
                    "atm": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "bar": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "gym": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                },
            },
        },
    },
    "closest_average_hexagon_6": {
        "summary": "Closest average hexagon with resolution 6",
        "value": {
            "mode": "walking",
            "study_area_ids": [91620000],
            "walking_profile": "standard",
            "scenario": {
                "id": 1,
                "name": "default",
            },
            "heatmap_type": "closest_average",
            "analysis_unit": "hexagon",
            "resolution": 6,
            "heatmap_config": {
                "poi": {
                    "atm": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "bar": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                    "gym": {"weight": 1, "max_count": 1, "max_traveltime": 20},
                },
            },
        },
    },
    "connectivity_heatmap_10": {
        "summary": "Connectivity heatmap with hexagon resolution 10",
        "value": {
            "mode": "walking",
            "study_area_ids": [91620000],
            "walking_profile": "standard",
            "scenario": {
                "id": 1,
                "name": "default",
            },
            "heatmap_type": "connectivity",
            "analysis_unit": "hexagon",
            "resolution": 10,
            "heatmap_config": {"max_traveltime": 10},
        },
    },
}
