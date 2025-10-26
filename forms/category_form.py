from rich.text import Text
from Buckets.constants import COLORS
from Buckets.models.category import Nature
from Buckets.managers.categories import get_category_by_id
from Buckets.forms.form import Form, FormField, Option, Options

# blueprint (never mutated)
_CATEGORY_FORM = Form(
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
                        text="Must", value=Nature.MUST, prefix=Text("●", style="red")
                    ),
                    Option(
                        text="Need", value=Nature.NEED, prefix=Text("●", style="orange")
                    ),
                    Option(
                        text="Want", value=Nature.WANT, prefix=Text("●", style="green")
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


class CategoryForm:
    def get_form(self) -> Form:
        return _CATEGORY_FORM.clone()

    def get_subcategory_form(self, parent_id: int) -> Form:
        f = _CATEGORY_FORM.clone()
        f.fields.append(
            FormField(
                key="parentCategoryId", type="hidden", default_value=str(parent_id)
            )
        )
        return f

    def get_filled_form(self, category_id: int) -> Form:
        f = _CATEGORY_FORM.clone()
        category = get_category_by_id(category_id)
        if not category:
            return f
        for field in f.fields:
            if field.key == "nature":
                field.default_value = category.nature
                field.default_value_text = category.nature.value
            elif field.key == "color":
                field.default_value = category.color
                field.default_value_text = category.color
            else:
                val = getattr(category, field.key)
                field.default_value = "" if val is None else str(val)
        return f
