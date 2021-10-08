from pydantic import BaseModel
# from typing import Optional
from datetime import datetime

# ! THESE MODELS ARE CREATED ONLY FOR INPUT FROM REQUESTS


class DBConnectionModel(BaseModel):
    username: str
    password: str


class MedicalRecordModel(BaseModel):
    uuid: str = None  # Optional[str]
    firstname: str
    lastname: str
    nic_nb: str
    email: str
    phone_nb: str
    birthday: str
    created_at: datetime = None  # Optional[datetime]


class FileModel(BaseModel):
    uuid: str = None
    parent_uuid: str = None
    name: str = None
    format: str = None
    type: str = None
    path: str = None


class ExcelNodeModel(BaseModel):
    parent_uuid: str = None
    name: str = None
    value: float = None


class IDOnlyModel(BaseModel):
    uuid: str
