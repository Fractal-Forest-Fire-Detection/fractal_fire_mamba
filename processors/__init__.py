"""Signal processors for fire detection"""
from .chemical_processor import ChemicalProcessor
from .environmental_processor import EnvironmentalContextProcessor
# from .visual_processor import VisualProcessor

__all__ = ['ChemicalProcessor', 'EnvironmentalContextProcessor']
