from typing import Any, List, Literal
from pydantic import BaseModel, Field
from rich.console import RenderableType


class Option(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    text: str | None = None  # if not provided, the value will be used
    value: Any
    prefix: RenderableType | None = None
    postfix: RenderableType | None = None


class Options(BaseModel):
    items: List[Option] = Field(default_factory=list)

    def __len__(self):
        return len(self.items)


class FormField(BaseModel):
    placeholder: str | None = None
    title: str | None = None
    key: str
    type: Literal[
        "string",
        "number",
        "integer",
        "boolean",
        "autocomplete",
        "dateAutoDay",
        "hidden",
    ]
    autocomplete_selector: bool = True  # autocomplete fields as a selector field. If false, acts as regular optional autocomplete
    is_required: bool = False
    min: float | int | None = None
    max: float | int | None = None
    labels: List[str] | None = None  # for type "boolean"
    options: Options | None = None  # for type "autocomplete"
    default_value: Any = None
    default_value_text: str | None = None
    create_action: bool | None = None  # for type "autocomplete"


class Form(BaseModel):
    fields: List[FormField] = Field(default_factory=list)

    def __len__(self):
        return len(self.fields)
