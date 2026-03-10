from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from fastapi import Header, HTTPException, Request

from packages.core.config import agent_token, operator_token


Role = Literal["agent", "operator"]


@dataclass(frozen=True)
class ServiceAuth:
    agent_service_token: str
    operator_service_token: str

    def resolve_role(self, token: str | None) -> Role:
        if token == self.operator_service_token:
            return "operator"
        if token == self.agent_service_token:
            return "agent"
        raise HTTPException(status_code=401, detail="Missing or invalid x-service-token")

    def require(self, token: str | None, *, role: Role) -> Role:
        resolved = self.resolve_role(token)
        if role == "operator" and resolved != "operator":
            raise HTTPException(status_code=403, detail="Operator token required")
        return resolved


def default_service_auth(*, allow_insecure_defaults: bool = False) -> ServiceAuth:
    return ServiceAuth(
        agent_service_token=agent_token(allow_insecure_default=allow_insecure_defaults),
        operator_service_token=operator_token(allow_insecure_default=allow_insecure_defaults),
    )


def install_auth(app, service_auth: ServiceAuth) -> None:
    app.state.service_auth = service_auth


def require_agent_access(request: Request, x_service_token: str | None = Header(None, alias="x-service-token")) -> str:
    service_auth: ServiceAuth = request.app.state.service_auth
    return service_auth.require(x_service_token, role="agent")


def require_operator_access(request: Request, x_service_token: str | None = Header(None, alias="x-service-token")) -> str:
    service_auth: ServiceAuth = request.app.state.service_auth
    return service_auth.require(x_service_token, role="operator")
