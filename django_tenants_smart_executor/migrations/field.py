__all__ = ["AddField", "RemoveField", "AlterField", "RenameField"]

from django.db.migrations import AddField as OriginalAddField
from django.db.migrations import AlterField as OriginalAlterField
from django.db.migrations import RemoveField as OriginalRemoveField
from django.db.migrations import RenameField as OriginalRenameField

from ._limit import should_limit_state_apply


class AddField(OriginalAddField):
    def state_forwards(self, app_label, state):
        if should_limit_state_apply("AddField", app_label):
            return
        super().state_forwards(app_label, state)


class RemoveField(OriginalRemoveField):
    def state_forwards(self, app_label, state):
        if should_limit_state_apply("RemoveField", app_label):
            return
        super().state_forwards(app_label, state)


class AlterField(OriginalAlterField):
    def state_forwards(self, app_label, state):
        if should_limit_state_apply("AlterField", app_label):
            return
        super().state_forwards(app_label, state)


class RenameField(OriginalRenameField):
    def state_forwards(self, app_label, state):
        if should_limit_state_apply("RenameField", app_label):
            return
        super().state_forwards(app_label, state)
