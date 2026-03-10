from __future__ import annotations

from .thin_kb_service import ThinKBService


class WritebackService:
    def __init__(self, kb_service: ThinKBService):
        self.kb_service = kb_service

    def promote_candidate(self, *args, **kwargs):
        return self.kb_service.promote_candidate(*args, **kwargs)

    def deprecate_object(self, *args, **kwargs):
        return self.kb_service.deprecate_object(*args, **kwargs)
