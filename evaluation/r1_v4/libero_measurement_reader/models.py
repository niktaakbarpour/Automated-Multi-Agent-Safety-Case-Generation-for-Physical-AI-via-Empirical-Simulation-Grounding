"""Measurement-only interfaces reusing V4 scalar/frame/contact/camera types."""
from dataclasses import dataclass,field
from typing import Any
from evaluation.r1_v4.contracts import Frame,Measurement,Contact,Camera,Uncertainty
@dataclass(frozen=True)
class Diagnostic:
 status:str
 code:str
 source:str
 frame:int|None=None
@dataclass(frozen=True)
class Channel:
 kind:str
 source_ref:str
 source_sha256:str
 hdf5_path:str
 phase:str
 shape:tuple[int,...]
 dtype:str
 frame:Frame
 uncertainty:Uncertainty
 measurement:Measurement
@dataclass(frozen=True)
class ContactRecord:
 geom1:int
 geom2:int
 owner1:str
 owner2:str
 distance:float
 world_position:tuple[float,...]
 normal:None=None
 force:None=None
@dataclass(frozen=True)
class Snapshot:
 index:int
 stage:str
 control_step:int
 endpoint_time:float
 host_timestamps:dict[str,Any]
 channels:tuple[Channel,...]
 contacts:tuple[ContactRecord,...]
 contact_bundle:Contact
 cameras:tuple[Camera,...]
 camera_references:tuple[dict,...]
 object_bindings:dict
 transform_guard:dict
 synthetic:bool=False
@dataclass
class ReadResult:
 reader_version:str='1.0.0'
 status:str='missing'
 execution_id:str|None=None
 synthetic:bool=False
 metadata:dict=field(default_factory=dict)
 reader_binding:dict=field(default_factory=dict)
 source_hashes:dict=field(default_factory=dict)
 native_geometry:dict=field(default_factory=dict)
 frames:list=field(default_factory=list)
 coverage:dict=field(default_factory=dict)
 diagnostics:list=field(default_factory=list)
 physical_safety_conclusion:bool=False
 empirical_admission_enabled:bool=False
 inferred_events:tuple=()
 checker_judgments:tuple=()
 evidence_records:tuple=()
 validation_scope:str='Stored measurement structure and provenance only; no physical predicates'
