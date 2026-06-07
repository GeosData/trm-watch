from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TRM_", env_file=".env", extra="ignore")

    # Tasa de Cambio Representativa del Mercado (TRM), datos.gov.co (Superfinanciera / SODA).
    base_url: str = "https://www.datos.gov.co/resource"
    dataset_id: str = "mcec-87by"
    app_token: str = ""  # optional, raises rate limits
    openai_api_key: str = ""
    judge_model: str = "gpt-4o-mini"
    # Path to the editable brief prompt. Empty = packaged default prompts/brief_es.txt.
    brief_prompt_path: str = ""

    @property
    def dataset_url(self) -> str:
        return f"{self.base_url}/{self.dataset_id}.json"


settings = Settings()
