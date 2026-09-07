import enum


class UnitStatus(str, enum.Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"


class Confidence(str, enum.Enum):
    HIGH = "high"
    LOW = "low"
    NOT_FOUND = "not_found"


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EDITED = "edited"  # LeaseField only


class Severity(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RuleVerdict(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_DETERMINABLE = "NOT_DETERMINABLE"


class JobType(str, enum.Enum):
    LEASE_EXTRACTION = "lease_extraction"
    PHOTO_ANALYSIS = "photo_analysis"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"
