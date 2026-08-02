from fastapi import FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

app = FastAPI()


class Settings(BaseSettings):

  model_config = SettingsConfigDict(env_file=".env")

  database_url: str

settings = Settings()


engine = create_async_engine(settings.database_url)

session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
  )


# print(settings.model_config, settings.database_url)

