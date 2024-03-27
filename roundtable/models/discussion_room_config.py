from roundtable.models.custom_base_model import CustomBaseModel


class DiscussionRoomConfig(CustomBaseModel):
    base_url: str
    api_key: str
    llm_model_name: str
    code_model_name: str
