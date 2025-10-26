from datetime import datetime

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Label

from Buckets.components.fields import Field, Fields
from Buckets.config import CONFIG
from Buckets.forms.form import Form
from Buckets.forms.record_forms import RecordForm
from Buckets.managers.record_templates import get_template_by_id
from Buckets.modals.base_widget import ModalContainer
from Buckets.modals.input import InputModal
from Buckets.utils.validation import validateForm


class RecordModal(InputModal):
    """Modal for creating/editing a record (no people/splits)."""

    isEditing = False

    BINDINGS = [
        Binding(
            CONFIG.hotkeys.record_modal.submit_and_template,
            "submit_and_template",
            "Submit & Template",
            priority=True,
        ),
    ]

    def __init__(
        self,
        title: str,
        form: Form = Form(),
        isEditing: bool = False,
        date: datetime = datetime.now(),
    ):
        super().__init__(title, form)
        self.record_form = RecordForm()
        self.isEditing = isEditing
        if isEditing:
            self._bindings.key_to_bindings.clear()
            self.refresh_bindings()
        self.date = date
        self.shift_pressed = False  # used for "Submit & Template"

    def _update_errors(self, errors: dict) -> None:
        # Clear previous error labels
        previousErrors = self.query(".error")
        for error in previousErrors:
            error.remove()
        # Show current field errors
        for key, value in errors.items():
            field = self.query_one(f"#row-field-{key}")
            field.mount(Label(value, classes="error"))

    def on_auto_complete_selected(self, event) -> None:
        """
        If the label field is an autocomplete and user selects a template,
        populate the rest of the fields from that template.
        """
        if "field-label" not in event.input.id:
            return

        template = get_template_by_id(event.input.heldValue)
        if not template:
            return

        for field in self.form.fields[1:-1]:
            has_held_value = field.type in ["autocomplete"]
            field_widget = self.query_one(f"#field-{field.key}")
            if not has_held_value:
                if field.type == "boolean":
                    field_widget.value = getattr(template, field.key)
                else:
                    field_widget.value = str(getattr(template, field.key))
            else:
                # Autocomplete-backed field
                field_widget.heldValue = getattr(template, field.key)
                if "Id" in field.key:
                    # Update displayed text via the related object name
                    field_widget.value = str(
                        getattr(getattr(template, field.key.replace("Id", "")), "name")
                    )
                # Also ping the controller to refresh postfix/prefix, etc.
                controller: Field = self.query_one(f"#field-{field.key}-controller")
                template_value = getattr(template, field.key)
                for index, option in enumerate(field.options.items):
                    if option.value == template_value:
                        controller.handle_select_index(index)
                        break

        self.app.notify(
            title="Success",
            message="Template applied",
            severity="information",
            timeout=3,
        )

    # ---------- Actions ---------- #

    def action_submit_and_template(self) -> None:
        self.shift_pressed = True
        self.action_submit()

    def action_submit(self) -> None:
        result_form, errors, is_valid = validateForm(self, self.form)
        if is_valid:
            self.dismiss({"record": result_form, "createTemplate": self.shift_pressed})
            return
        self._update_errors(errors)

    # ---------- View ---------- #

    def compose(self) -> ComposeResult:
        yield ModalContainer(
            Fields(self.form),
            Container(id="no-splits-placeholder"),  # keeps layout stable; harmless
        )
