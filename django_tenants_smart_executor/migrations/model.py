__all__ = [
    "CreateModel",
    "AlterIndexTogether",
    "AlterModelManagers",
    "AlterModelOptions",
    "AlterModelTable",
    "AlterModelTableComment",
    "AlterOrderWithRespectTo",
    "AlterUniqueTogether",
    "DeleteModel",
    "RenameModel",
]

from django.db.migrations import AlterIndexTogether as OriginalAlterIndexTogether
from django.db.migrations import AlterModelManagers as OriginalAlterModelManagers
from django.db.migrations import AlterModelOptions as OriginalAlterModelOptions
from django.db.migrations import AlterModelTable as OriginalAlterModelTable
from django.db.migrations import AlterModelTableComment as OriginalAlterModelTableComment
from django.db.migrations import AlterOrderWithRespectTo as OriginalAlterOrderWithRespectTo
from django.db.migrations import AlterUniqueTogether as OriginalAlterUniqueTogether
from django.db.migrations import CreateModel as OriginalCreateModel
from django.db.migrations import DeleteModel as OriginalDeleteModel
from django.db.migrations import RenameModel as OriginalRenameModel
from django.db.migrations.state import ModelState

from ._limit import should_limit_state_apply


class CreateModel(OriginalCreateModel):
    def state_forwards(self, app_label, state):
        if should_limit_state_apply("CreateModel", app_label):
            # we need the models to live in the state for database forwards,
            # but we do not need all the fields/options/bases/managers
            state.add_model(
                ModelState(
                    app_label,
                    self.name,
                    [],
                    {},
                    (),
                    [],
                )
            )
            return
        super().state_forwards(app_label, state)


class AlterIndexTogether(OriginalAlterIndexTogether):
    def state_forwards(self, app_label, state):
        if should_limit_state_apply("AlterIndexTogether", app_label):
            return
        super().state_forwards(app_label, state)


class AlterModelManagers(OriginalAlterModelManagers):
    def state_forwards(self, app_label, state):
        if should_limit_state_apply("AlterModelManagers", app_label):
            return
        super().state_forwards(app_label, state)


class AlterModelOptions(OriginalAlterModelOptions):
    def state_forwards(self, app_label, state):
        if should_limit_state_apply("AlterModelOptions", app_label):
            return
        super().state_forwards(app_label, state)


class AlterModelTable(OriginalAlterModelTable):
    def state_forwards(self, app_label, state):
        if should_limit_state_apply("AlterModelTable", app_label):
            return
        super().state_forwards(app_label, state)


class AlterModelTableComment(OriginalAlterModelTableComment):
    def state_forwards(self, app_label, state):
        if should_limit_state_apply("AlterModelTableComment", app_label):
            return
        super().state_forwards(app_label, state)


class AlterOrderWithRespectTo(OriginalAlterOrderWithRespectTo):
    def state_forwards(self, app_label, state):
        if should_limit_state_apply("AlterOrderWithRespectTo", app_label):
            return
        super().state_forwards(app_label, state)


class AlterUniqueTogether(OriginalAlterUniqueTogether):
    def state_forwards(self, app_label, state):
        if should_limit_state_apply("AlterUniqueTogether", app_label):
            return
        super().state_forwards(app_label, state)


class DeleteModel(OriginalDeleteModel):
    def state_forwards(self, app_label, state):
        # included for completeness, we need the deletes to happen as we add it in CreateModel
        super().state_forwards(app_label, state)


class RenameModel(OriginalRenameModel):
    def state_forwards(self, app_label, state):
        # included for completeness, we need the renames to happen as we add it in CreateModel
        super().state_forwards(app_label, state)
