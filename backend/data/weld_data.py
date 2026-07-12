"""Weld data models: standardized schemas for welding parameters."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class WeldProcess(str, Enum):
    SMAW="SMAW"; GMAW="GMAW"; GTAW="GTAW"; FCAW="FCAW"; SAW="SAW"
    PAW="PAW"; LBW="LBW"; EBW="EBW"; RSW="RSW"; FRW="FRW"

class JointType(str, Enum):
    BUTT="butt"; LAP="lap"; TEE="tee"; CORNER="corner"; EDGE="edge"

class WeldPosition(str, Enum):
    FLAT="1G"; HORIZONTAL="2G"; VERTICAL_UP="3G"; OVERHEAD="4G"
    PIPE_HORIZONTAL="5G"; PIPE_INCLINED="6G"

class Environment(str, Enum):
    INDOOR_STANDARD="indoor_standard"; INLAND="inland"; COASTAL="coastal"; UNDERWATER="underwater"
    ULTRA_LOW_TEMP="ultra_low_temp"; ULTRA_HIGH_TEMP="ultra_high_temp"
    HIGH_HUMIDITY="high_humidity"; CORROSIVE_CHEMICAL="corrosive_chemical"
    VACUUM="vacuum"; NUCLEAR="nuclear"; DEEP_SEA="deep_sea"; SPACE="space"

@dataclass
class MaterialSpec:
    name:str=""; grade:str=""; composition:dict=field(default_factory=dict)
    density:float=7850.0; melting_point:float=1500.0; boiling_point:float=2900.0
    thermal_conductivity:float=50.0; specific_heat:float=500.0; cte:float=12.0e-6
    youngs_modulus:float=200e9; yield_strength:float=250e6; tensile_strength:float=400e6
    poisson_ratio:float=0.3; electrical_resistivity:float=1.7e-7; magnetic_permeability:float=1.0
    carbon_equivalent:Optional[float]=None

@dataclass
class WeldParameters:
    process:WeldProcess=field(default_factory=lambda:WeldProcess.GTAW)
    current:float=150.0; voltage:float=20.0; travel_speed:float=2.0
    arc_efficiency:float=0.75; wire_feed_rate:Optional[float]=None
    gas_flow_rate:Optional[float]=None; electrode_diameter:Optional[float]=None
    torch_angle:float=90.0; travel_angle:float=0.0; stickout:float=10.0
    arc_length:float=3.0; polarity:str="DCEN"; pulse_frequency:Optional[float]=None
    preheat_temp:float=25.0; interpass_temp:float=150.0

@dataclass
class WeldJoint:
    joint_type: JointType=field(default_factory=lambda:JointType.BUTT)
    position: WeldPosition=field(default_factory=lambda:WeldPosition.FLAT)
    plate_thickness:float=10.0; root_gap:float=1.0; root_face:float=1.5
    bevel_angle:float=30.0; groove_type:str="V"; number_of_passes:int=3

@dataclass
class WeldInput:
    id:str=""; base_material:MaterialSpec=field(default_factory=MaterialSpec)
    filler_material:Optional[MaterialSpec]=None
    parameters:WeldParameters=field(default_factory=WeldParameters)
    joint:WeldJoint=field(default_factory=WeldJoint)
    environment:Environment=field(default_factory=lambda:Environment.INDOOR_STANDARD)
    notes:str=""

