from fastapi import APIRouter, Depends, HTTPException

from services import institution_service
from services.auth_service import require_roles, ROLE_UNIVERSITY, ROLE_ADMIN

router = APIRouter(
    prefix="/institution",
    tags=["Institution (University)"],
)

_guard = require_roles(ROLE_UNIVERSITY)


def _institution_of(user: dict) -> str:
    """Resolve which institution the caller may read.

    Row scoping lives here. The name comes from the caller's signed JWT and is
    never accepted as a request parameter, so a university cannot read another's
    data by crafting the URL.

    ADMIN has no institution of its own, so it is given the first one for
    inspection purposes rather than being handed every institution's rows.
    """
    institution = user.get("institution")
    if institution:
        return institution

    if user.get("role") == ROLE_ADMIN:
        from services import _datasets as ds
        options = ds.institutions()
        if options:
            return options[0]['name']

    raise HTTPException(
        status_code=403,
        detail="This account is not linked to an institution.",
    )


@router.get("/me")
def get_my_institution(user: dict = Depends(_guard)):
    """Profile of the caller's own institution."""
    try:
        return institution_service.get_profile(_institution_of(user))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio")
def get_portfolio(user: dict = Depends(_guard)):
    """Every programme this institution runs, with its enrolment funnel and cost."""
    try:
        return institution_service.get_portfolio(_institution_of(user))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expansion")
def get_expansion(user: dict = Depends(_guard)):
    """Programmes ranked Expand / Hold / Consolidate against national demand,
    own momentum, competitor density and yield — with the factor breakdown."""
    try:
        return institution_service.get_expansion_opportunities(_institution_of(user))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resources")
def get_resources(user: dict = Depends(_guard)):
    """Recruitment funnel and cost per enrolment, overall and per programme."""
    try:
        return institution_service.get_resource_efficiency(_institution_of(user))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmark")
def get_benchmark(user: dict = Depends(_guard)):
    """Standing against the other institutions, anonymised as Peer A/B/C."""
    try:
        return institution_service.get_peer_benchmark(_institution_of(user))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
