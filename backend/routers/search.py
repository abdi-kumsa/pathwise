"""
Cross-entity search — the backend for the global command bar.

Results are filtered by the caller's role on the server, not in the browser, so
a student never receives institution records in the first place. Each hit
carries the route the frontend should navigate to, keeping the role -> page
mapping in one place.
"""
from fastapi import APIRouter, Depends, Query
from typing import List

from services import _datasets as ds
from services.auth_service import (
    get_current_user,
    ROLE_ADMIN, ROLE_STUDENT, ROLE_MOE, ROLE_MOL, ROLE_UNIVERSITY,
)

router = APIRouter(prefix="/search", tags=["Search"])

# Which entity kinds each role may search. The command bar shows nothing a role
# cannot act on.
_VISIBLE = {
    ROLE_STUDENT:    {'occupation', 'program'},
    ROLE_MOL:        {'occupation', 'field'},
    ROLE_MOE:        {'field', 'program'},
    ROLE_UNIVERSITY: {'program', 'field'},
    ROLE_ADMIN:      {'occupation', 'field', 'program', 'institution'},
}

# Where selecting a result takes you, per role.
_ROUTES = {
    ROLE_STUDENT:    {'occupation': '/student/careers?job=', 'program': '/student/careers?program='},
    ROLE_MOL:        {'occupation': '/mol/occupations?job=', 'field': '/mol/supply-demand?field='},
    ROLE_MOE:        {'field': '/moe/fields?field=', 'program': '/moe/fields?program='},
    ROLE_UNIVERSITY: {'program': '/university/portfolio?program=', 'field': '/university/expansion?field='},
    ROLE_ADMIN:      {
        'occupation': '/mol/occupations?job=', 'field': '/moe/fields?field=',
        'program': '/university/portfolio?program=', 'institution': '/admin/institutions?name=',
    },
}


def _match(text: str, q: str) -> int:
    """Rank: 0 = prefix match, 1 = substring, -1 = no match."""
    t = text.lower()
    if t.startswith(q):
        return 0
    if q in t:
        return 1
    return -1


@router.get("")
def search(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(15, ge=1, le=50),
    user: dict = Depends(get_current_user),
):
    """Search occupations, fields, programmes and institutions at once."""
    query = q.strip().lower()
    role = user["role"]
    visible = _VISIBLE.get(role, set())
    routes = _ROUTES.get(role, {})

    hits: List[tuple] = []

    if 'occupation' in visible:
        for entry in ds.job_titles():
            r = _match(entry['job_title'], query)
            if r >= 0:
                hits.append((r, {
                    'kind': 'occupation', 'label': entry['job_title'],
                    'sublabel': entry['job_family'],
                    'route': routes.get('occupation', '') + entry['job_title'],
                }))

    if 'field' in visible:
        for field in ds.FIELDS:
            r = _match(field, query)
            if r >= 0:
                hits.append((r, {
                    'kind': 'field', 'label': field,
                    'sublabel': f"{len(ds.family_to_programs().get(field, []))} programme(s)",
                    'route': routes.get('field', '') + field,
                }))

    if 'program' in visible:
        prog_field = ds.program_to_family()
        for program in ds.PROGRAMS:
            r = _match(program, query)
            if r >= 0:
                hits.append((r, {
                    'kind': 'program', 'label': program,
                    'sublabel': prog_field.get(program, ''),
                    'route': routes.get('program', '') + program,
                }))

    if 'institution' in visible:
        for inst in ds.institutions():
            r = _match(inst['name'], query)
            if r >= 0:
                hits.append((r, {
                    'kind': 'institution', 'label': inst['name'],
                    'sublabel': f"{inst['type']} · {inst['state']}",
                    'route': routes.get('institution', '') + inst['name'],
                }))

    hits.sort(key=lambda h: (h[0], h[1]['label']))
    return {
        'query':   q,
        'role':    role,
        'results': [h[1] for h in hits[:limit]],
        'total':   len(hits),
    }
