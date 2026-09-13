"""
models.py
=========
SAFEMETRIC Evidence System Data Models.

Preserves the statutory connection between detected declarations, legal violations,
and the original package image substrate.

Strict Requirements:
Where OCR provides bounding boxes, store:
- page/image identifier
- bounding box
- OCR text
- confidence
- associated declaration
- associated rule

Every statutory violation must be directly traceable back to visual evidence.
"""

from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
import uuid
import datetime


@dataclass
class EvidenceItem:
    """
    Statutory Visual Evidence Record.
    Preserves connection between a detected declaration or statutory violation
    and the physical packaging image substrate.
    """
    # 6 Core Required Fields
    image_id: str                              # page/image identifier (file path, URI, or unique image token)
    bounding_box: Optional[List[List[int]]]    # 4-point polygon coordinates [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] or None
    ocr_text: Optional[str]                    # Raw OCR source text detected within region
    confidence: float                          # Optical recognition confidence (0.0 - 100.0%)
    associated_declaration: str                # Name of declaration field (e.g. 'mrp', 'net_quantity')
    associated_rule: Optional[str]             # Statutory rule ID (e.g. 'PCR-2011-R6-1-E-MRP')

    # Traceability & Statutory Context
    evidence_id: str = field(default_factory=lambda: f"ev_{uuid.uuid4().hex[:10]}")
    page_number: int = 1                       # Page number for multi-page labels / carton sides
    declaration_value: Optional[Any] = None    # Parsed structured value of the declaration
    legal_reference: Optional[str] = None      # Exact parliamentary act or rule section citation
    is_violation: bool = False                 # True if tied to a statutory violation or missing mandatory field
    violation_details: Optional[Dict[str, Any]] = None  # Issue, severity, rule reference, recommendation
    visual_status: str = "DETECTED_ON_IMAGE"   # DETECTED_ON_IMAGE | MISSING_FROM_IMAGE | LOW_CONFIDENCE | ADVISORY
    created_at: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Serializes evidence item into a JSON-compatible dictionary."""
        return asdict(self)

    @property
    def has_bounding_box(self) -> bool:
        """Indicates whether visual coordinate geometry is present."""
        return self.bounding_box is not None and len(self.bounding_box) >= 4

    def get_bounding_rect(self) -> Optional[Dict[str, int]]:
        """
        Computes the axis-aligned bounding rectangle [x, y, width, height]
        from polygon points for standard rendering and inspection overlays.
        """
        if not self.has_bounding_box:
            return None
        xs = [p[0] for p in self.bounding_box]
        ys = [p[1] for p in self.bounding_box]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        return {
            "x": int(min_x),
            "y": int(min_y),
            "width": int(max_x - min_x),
            "height": int(max_y - min_y)
        }


@dataclass
class EvidenceStore:
    """
    Repository for all visual evidence records linked to a specific inspection / commodity package image.
    Enforces bidirectional traceability between image regions, declarations, and violations.
    """
    image_id: str                              # Primary page/image identifier
    inspection_id: Optional[str] = None        # Associated inspection UUID or ID
    image_path: Optional[str] = None           # Path to the original raw package image
    page_count: int = 1                        # Total image pages / package panels
    items: List[EvidenceItem] = field(default_factory=list)

    def add_item(self, item: EvidenceItem) -> None:
        """Adds a verified evidence item to the store."""
        self.items.append(item)

    def get_item_by_id(self, evidence_id: str) -> Optional[EvidenceItem]:
        """Retrieves an evidence item by its unique evidence identifier."""
        for item in self.items:
            if item.evidence_id == evidence_id:
                return item
        return None

    def get_evidence_by_declaration(self, declaration_name: str) -> List[EvidenceItem]:
        """Finds all visual evidence records for a specific declaration key."""
        target = declaration_name.lower().strip()
        return [
            item for item in self.items
            if item.associated_declaration.lower().strip() == target
        ]

    def get_evidence_by_rule(self, rule_id: str) -> List[EvidenceItem]:
        """Finds all visual evidence records associated with a statutory rule."""
        target = rule_id.lower().strip()
        return [
            item for item in self.items
            if item.associated_rule and item.associated_rule.lower().strip() == target
        ]

    def get_violations_evidence(self) -> List[EvidenceItem]:
        """Returns all visual evidence records linked to statutory non-compliance violations."""
        return [item for item in self.items if item.is_violation]

    def get_detected_evidence(self) -> List[EvidenceItem]:
        """Returns all evidence items that were physically detected on the package image."""
        return [item for item in self.items if item.visual_status == "DETECTED_ON_IMAGE"]

    def get_missing_evidence(self) -> List[EvidenceItem]:
        """Returns evidence records representing missing mandatory statutory declarations."""
        return [item for item in self.items if item.visual_status == "MISSING_FROM_IMAGE"]

    def trace_violation(self, rule_id_or_field: str) -> Optional[EvidenceItem]:
        """
        Traces a statutory violation directly back to its visual evidence record.
        Lookup order:
        1. Violation by exact rule_id (e.g. 'PCR-2011-R6-1-E-MRP')
        2. Violation by declaration field name (e.g. 'mrp', 'net_quantity')
        3. Any evidence item matching rule_id
        """
        target = rule_id_or_field.lower().strip()
        # 1. Match violation by rule_id
        for item in self.items:
            if item.is_violation and item.associated_rule and item.associated_rule.lower().strip() == target:
                return item
        # 2. Match violation by declaration field
        for item in self.items:
            if item.is_violation and item.associated_declaration.lower().strip() == target:
                return item
        # 3. Match any rule association
        for item in self.items:
            if item.associated_rule and item.associated_rule.lower().strip() == target:
                return item
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the evidence store into a JSON-compatible manifest."""
        return {
            "image_id": self.image_id,
            "inspection_id": self.inspection_id,
            "image_path": self.image_path,
            "page_count": self.page_count,
            "total_evidence_items": len(self.items),
            "total_violations_linked": len(self.get_violations_evidence()),
            "detected_regions_count": len(self.get_detected_evidence()),
            "missing_declarations_count": len(self.get_missing_evidence()),
            "items": [item.to_dict() for item in self.items]
        }
