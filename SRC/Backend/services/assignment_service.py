from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AssignmentCandidate:
    resource_id: UUID
    available: bool = True
    skills: set[str] | None = None
    workload: int = 0
    location: str | None = None
    languages: set[str] | None = None


@dataclass(frozen=True)
class AssignmentRequest:
    required_skills: set[str] | None = None
    preferred_resource_id: UUID | None = None
    location: str | None = None
    language: str | None = None


def choose_resource(candidates: list[AssignmentCandidate], request: AssignmentRequest) -> UUID | None:
    eligible = [candidate for candidate in candidates if candidate.available]
    if request.required_skills:
        eligible = [candidate for candidate in eligible if request.required_skills.issubset(candidate.skills or set())]
    if request.location:
        same_location = [candidate for candidate in eligible if candidate.location == request.location]
        if same_location:
            eligible = same_location
    if request.preferred_resource_id and any(candidate.resource_id == request.preferred_resource_id for candidate in eligible):
        return request.preferred_resource_id
    if request.language:
        language_matches = [candidate for candidate in eligible if request.language in (candidate.languages or set())]
        if language_matches:
            eligible = language_matches
    if not eligible:
        return None
    return sorted(eligible, key=lambda candidate: (candidate.workload, str(candidate.resource_id)))[0].resource_id
