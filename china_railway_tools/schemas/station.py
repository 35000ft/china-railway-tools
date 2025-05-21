from pydantic import BaseModel, ConfigDict


class Station(BaseModel):
    name: str
    pinyin: str
    pinyin_abbr: str
    code: str
    city: str
    model_config = ConfigDict(from_attributes=True)
