from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    auto_clean_train_no: bool = Field(True, title='是否自动清理存储的车次信息')
    max_saved_train_no_days: int = Field(7, title='存储车次信息保留天数', gt=0)
    max_cached_days: int = Field(3, title='缓存保留天数', gt=0)
    fetch_concurrency: dict = Field({
        'fetch_trains': 5,
        'fetch_train_schedule': 5,
        'fetch_train_no': 10,
    })
    sqlite_dir: str = Field(None, title='sqlite存放路径')
