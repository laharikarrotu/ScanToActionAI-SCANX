"""
Drug Interaction Checker - Unique HealthScan Feature
Checks for drug-drug interactions, contraindications, and allergies
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import httpx
import os
import asyncio

class Medication(BaseModel):
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None  # oral, topical, etc.

class InteractionWarning(BaseModel):
    severity: str  # major, moderate, minor
    medication1: str
    medication2: str
    description: str
    recommendation: str

class InteractionChecker:
    """
    Checks for drug interactions using external APIs
    For MVP: Uses RxNav/RxNorm API (free) or DrugBank (requires API key)
    """
    
    def __init__(self):
        # For MVP, we'll use a combination of:
        # 1. RxNav API (free, no key needed) for drug name normalization
        # 2. Simple interaction database for common interactions
        # 3. Can upgrade to DrugBank API later
        self.common_interactions = self._load_common_interactions()
    
    def _load_common_interactions(self) -> Dict[str, List[str]]:
        """
        Load common drug interactions database
        In production, this would come from a proper medical database
        """
        return {
            "warfarin": ["aspirin", "ibuprofen", "naproxen", "heparin"],
            "aspirin": ["warfarin", "ibuprofen", "naproxen"],
            "ibuprofen": ["aspirin", "warfarin", "lithium"],
            "metformin": ["alcohol"],
            "digoxin": ["furosemide", "hydrochlorothiazide"],
            "lithium": ["ibuprofen", "naproxen", "diuretics"],
        }
    
    async def normalize_drug_name(self, drug_name: str) -> Optional[str]:
        """
        Normalize drug name using RxNav API
        Converts brand names to generic names
        """
        try:
            async with httpx.AsyncClient() as client:
                # RxNav API endpoint
                url = f"https://rxnav.nlm.nih.gov/REST/drugs.json"
                params = {"name": drug_name}
                response = await client.get(url, params=params, timeout=5.0)
                
                if response.status_code == 200:
                    data = response.json()
                    if "drugGroup" in data and "conceptGroup" in data["drugGroup"]:
                        # Extract first concept name (generic name)
                        concepts = data["drugGroup"]["conceptGroup"]
                        if concepts and len(concepts) > 0:
                            if "conceptProperties" in concepts[0]:
                                props = concepts[0]["conceptProperties"]
                                if props and len(props) > 0:
                                    return props[0].get("name", drug_name.lower())
                
                # Fallback: return lowercase version
                return drug_name.lower()
        except Exception:
            return drug_name.lower()
    
    async def check_interactions(
        self, 
        medications: List[Medication],
        allergies: Optional[List[str]] = None
    ) -> List[InteractionWarning]:
        """
        Check for interactions between medications
        """
        warnings = []
        
        # Normalize all medication names
        normalized_meds = []
        for med in medications:
            normalized_name = await self.normalize_drug_name(med.name)
            normalized_meds.append((med, normalized_name))
        
        # Check pairwise interactions
        for i, (med1, norm1) in enumerate(normalized_meds):
            for j, (med2, norm2) in enumerate(normalized_meds):
                if i >= j:  # Avoid duplicate checks
                    continue
                
                # Check against interaction database
                interactions = self._check_interaction(norm1, norm2)
                for interaction in interactions:
                    warnings.append(InteractionWarning(
                        severity=interaction["severity"],
                        medication1=med1.name,
                        medication2=med2.name,
                        description=interaction["description"],
                        recommendation=interaction["recommendation"]
                    ))
        
        # Check for allergies
        if allergies:
            for med, norm_name in normalized_meds:
                for allergy in allergies:
                    if allergy.lower() in norm_name or norm_name in allergy.lower():
                        warnings.append(InteractionWarning(
                            severity="major",
                            medication1=med.name,
                            medication2=allergy,
                            description=f"{med.name} may contain or interact with {allergy}",
                            recommendation="Do not take this medication. Consult your doctor immediately."
                        ))
        
        return warnings
    
    def _check_interaction(self, drug1: str, drug2: str) -> List[Dict[str, str]]:
        """
        Check if two drugs have known interactions
        Returns list of interaction details
        """
        interactions = []
        
        # Check if drug1 interacts with drug2
        if drug1 in self.common_interactions:
            if drug2 in self.common_interactions[drug1]:
                interactions.append({
                    "severity": "major" if drug1 in ["warfarin", "digoxin", "lithium"] else "moderate",
                    "description": f"{drug1} and {drug2} may interact",
                    "recommendation": "Consult your doctor before taking these medications together"
                })
        
        # Check reverse (drug2 interacts with drug1)
        if drug2 in self.common_interactions:
            if drug1 in self.common_interactions[drug2]:
                interactions.append({
                    "severity": "major" if drug2 in ["warfarin", "digoxin", "lithium"] else "moderate",
                    "description": f"{drug2} and {drug1} may interact",
                    "recommendation": "Consult your doctor before taking these medications together"
                })
        
        return interactions
    
    def get_severity_color(self, severity: str) -> str:
        """Get color code for severity level"""
        colors = {
            "major": "#DC3545",  # Red
            "moderate": "#FFC107",  # Yellow
            "minor": "#17A2B8"  # Blue
        }
        return colors.get(severity, "#6C757D")

