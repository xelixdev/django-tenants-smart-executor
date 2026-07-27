__all__ = ["AddIndex", "RemoveIndex", "RenameIndex"]

from django.db.migrations import AddIndex as OriginalAddIndex
from django.db.migrations import RemoveIndex as OriginalRemoveIndex
from django.db.migrations import RenameIndex as OriginalRenameIndex

from ._limit import should_limit_state_apply


class AddIndex(OriginalAddIndex):
    def state_forwards(self, app_label, state):
        if should_limit_state_apply("AddIndex", app_label):
            return
        super().state_forwards(app_label, state)


class RemoveIndex(OriginalRemoveIndex):
    def state_forwards(self, app_label, state):
        if should_limit_state_apply("RemoveIndex", app_label):
            return
        super().state_forwards(app_label, state)


class RenameIndex(OriginalRenameIndex):
    def state_forwards(self, app_label, state):
        if should_limit_state_apply("RenameIndex", app_label):
            return
        super().state_forwards(app_label, state)
