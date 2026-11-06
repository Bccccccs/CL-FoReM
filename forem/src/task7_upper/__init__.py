"""Task7.21 upper-network modules. Defaults: SRC-0903; implementation evidence: SRC-0503/0504."""
from .bias import BiasLayer
from .candidate_encoder import CandidateEncoder
from .heads import Heads
from .model import UpperModel
from .vcm import VCM, ObservationEncoder, MemoryRetrieval
from .world_model import WorldModel

__all__ = ['BiasLayer', 'CandidateEncoder', 'Heads', 'UpperModel', 'VCM', 'WorldModel', 'ObservationEncoder', 'MemoryRetrieval']
