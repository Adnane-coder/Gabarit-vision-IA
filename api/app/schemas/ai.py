from pydantic import BaseModel, ConfigDict


class AIStatus(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    available: bool
    mode: str
    model_loaded: bool
    model_name: str
