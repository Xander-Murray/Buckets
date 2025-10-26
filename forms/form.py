from typing import Any, List, Literal
from pydantic import BaseModel, Field
from rich.console import RenderableType


class Option(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    text: str | None = None
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
    autocomplete_selector: bool = True
    is_required: bool = False
    min: float | int | None = None
    max: float | int | None = None
    labels: List[str] | None = None
    options: Options | None = None
    default_value: Any = None
    default_value_text: str | None = None
    create_action: bool | None = None


class Form(BaseModel):
    fields: List[FormField] = Field(default_factory=list)

    def __len__(self):
        return len(self.fields)

    def clone(self) -> "Form":
        # pydantic v2
        return self.model_copy(deep=True)
