import copy

from rich.text import Text

from Buckets.constants import COLORS
from Buckets.models.category import Nature
from Buckets.managers.categories import get_category_by_id
from Buckets.forms.form import Form, FormField, Option, Options


class CategoryForm:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ------------ Blueprints ------------ #

    FORM = Form(
        fields=[
            FormField(
                placeholder="My Category",
                title="Name",
                key="name",
                type="string",
                is_required=True,
            ),
            FormField(
                title="Nature",
                key="nature",
                type="autocomplete",
                options=Options(
                    items=[
                        Option(
                            text="Must",
                            value=Nature.MUST,
                            prefix=Text("●", style="red"),
                        ),
                        Option(
                            text="Need",
                            value=Nature.NEED,
                            prefix=Text("●", style="orange"),
                        ),
                        Option(
                            text="Want",
                            value=Nature.WANT,
                            prefix=Text("●", style="green"),
                        ),
                    ]
                ),
                is_required=True,
                placeholder="Select Nature",
            ),
            FormField(
                title="Color",
                key="color",
                type="autocomplete",
                options=Options(
                    items=[
                        Option(value=color, prefix=Text("●", style=color))
                        for color in COLORS
                    ]
                ),
                is_required=True,
                placeholder="Select Color",
            ),
        ]
    )

    def get_subcategory_form(self, parent_id: int) -> Form:
        subcategory_form = copy.deepcopy(self.FORM)
        subcategory_form.fields.append(
            FormField(
                key="parentCategoryId",
                type="hidden",
                default_value=str(parent_id),
            )
        )
        return subcategory_form

    def get_filled_form(self, category_id: int) -> Form:
        """Return a copy of the form with values from the record"""
        filled_form = copy.deepcopy(self.FORM)
        category = get_category_by_id(category_id)
        if category:
            for field in filled_form.fields:
                value = getattr(category, field.key)
                if field.key == "nature":
                    field.default_value = category.nature
                    field.default_value_text = category.nature.value
                elif field.key == "color":
                    field.default_value = category.color
                    field.default_value_text = category.color
                else:
                    field.default_value = str(value) if value is not None else ""

        return filled_form

    def get_form(self):
        return self.FORM
