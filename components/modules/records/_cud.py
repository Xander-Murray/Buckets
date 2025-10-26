from __future__ import annotations

from datetime import datetime

from Buckets.forms.form import Form
from Buckets.forms.record_forms import RecordForm
from Buckets.managers.record_templates import create_template_from_record
from Buckets.managers.records import (
    create_record,
    delete_record,
    get_record_by_id,
    update_record,
)
from Buckets.modals.confirmation import ConfirmationModal
from Buckets.modals.record import RecordModal
from Buckets.modals.transfer import TransferModal

class RecordCUD:
    """Create / Update / Delete actions for Records (no people, no splits)."""

    # ---------- Create ---------- #
    def action_new(self) -> None:
        def check_result(result) -> None:
            if not result:
                return
            try:
                # result["record"] comes from RecordModal
                create_record(result["record"])
                if result.get("createTemplate"):
                    create_template_from_record(result["record"])
            except Exception as e:
                self.app.notify(
                    title="Error", message=f"{e}", severity="error", timeout=10
                )
            else:
                self.app.notify(
                    title="Success",
                    message=(
                        "Record created"
                        if not result.get("createTemplate")
                        else "Record created and template saved"
                    ),
                    severity="information",
                    timeout=3,
                )
                # Rebuild list (if a template was created, parent may rebuild template pane)
                self.page_parent.rebuild(templates=bool(result.get("createTemplate")))

        self.app.push_screen(
            RecordModal(
                "New Record",
                form=RecordForm().get_form(default_values=self.page_parent.mode),
                date=self.page_parent.mode["date"],
            ),
            callback=check_result,
        )

    # ---------- Update ---------- #
    def action_edit(self) -> None:
        if not (hasattr(self, "current_row") and self.current_row):
            self.app.notify(
                title="Error", message="Nothing selected", severity="error", timeout=2
            )
            self.app.bell()
            return

        row_type, row_id = self.current_row.split("-", 1)

        def check_result_records(result) -> None:
            if not result:
                self.app.notify(
                    title="Discarded",
                    message="Record not updated",
                    severity="warning",
                    timeout=3,
                )
                return
            try:
                # When editing a normal record, modal returns {"record": {...}}
                # When editing a transfer via TransferModal, it returns the record fields directly
                payload = result["record"] if "record" in result else result
                update_record(row_id, payload)
            except Exception as e:
                self.app.notify(
                    title="Error", message=f"{e}", severity="error", timeout=10
                )
            else:
                self.app.notify(
                    title="Success",
                    message="Record updated",
                    severity="information",
                    timeout=3,
                )
                self.page_parent.rebuild()

        if row_type != "r":
            # Only row type we support now
            self.app.notify(
                title="Error",
                message="Unsupported selection",
                severity="error",
                timeout=2,
            )
            return

        record = get_record_by_id(row_id)
        if not record:
            self.app.notify(
                title="Error",
                message="Record not found",
                severity="error",
                timeout=2,
            )
            return

        if record.isTransfer:
            # Edit transfer via dedicated modal
            self.app.push_screen(
                TransferModal(title="Edit transfer", record=record),
                callback=check_result_records,
            )
        else:
            filled_form = RecordForm().get_filled_form(record.id)
            self.app.push_screen(
                RecordModal(
                    "Edit Record",
                    form=filled_form,
                    isEditing=True,
                ),
                callback=check_result_records,
            )

    # ---------- Delete ---------- #
    def action_delete(self) -> None:
        if not (hasattr(self, "current_row") and self.current_row):
            self.app.notify(
                title="Error", message="Nothing selected", severity="error", timeout=2
            )
            self.app.bell()
            return

        row_type, row_id = self.current_row.split("-", 1)
        if row_type != "r":
            self.app.notify(
                title="Error",
                message="Only records can be deleted.",
                severity="error",
                timeout=2,
            )
            return

        def check_delete(confirmed: bool) -> None:
            if not confirmed:
                return
            delete_record(row_id)
            self.app.notify(
                title="Success",
                message="Record deleted",
                severity="information",
                timeout=3,
            )
            self.page_parent.rebuild()

        self.app.push_screen(
            ConfirmationModal("Are you sure you want to delete this record?"),
            callback=check_delete,
        )

    # ---------- Transfer (Create) ---------- #
    def action_new_transfer(self) -> None:
        def check_result(result) -> None:
            if not result:
                return
            try:
                create_record(result)
            except Exception as e:
                self.app.notify(
                    title="Error", message=f"{e}", severity="error", timeout=10
                )
            else:
                self.app.notify(
                    title="Success",
                    message="Transfer created",
                    severity="information",
                    timeout=3,
                )
                self.page_parent.rebuild()

        self.app.push_screen(
            TransferModal(
                title="New transfer",
                defaultDate=self.page_parent.mode["date"].strftime("%d"),
            ),
            callback=check_result,
        )
