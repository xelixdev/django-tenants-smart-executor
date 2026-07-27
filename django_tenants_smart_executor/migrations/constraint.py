__all__ = ["AddConstraint", "RemoveConstraint", "AlterConstraint"]

from django.db.migrations import AddConstraint as OriginalAddConstraint
from django.db.migrations import AlterConstraint as OriginalAlterConstraint
from django.db.migrations import RemoveConstraint as OriginalRemoveConstraint

from ._limit import should_limit_state_apply


class AddConstraint(OriginalAddConstraint):
    def state_forwards(self, app_label, state):
        if should_limit_state_apply("AddConstraint", app_label):
            return
        super().state_forwards(app_label, state)


class RemoveConstraint(OriginalRemoveConstraint):
    def state_forwards(self, app_label, state):
        if should_limit_state_apply("RemoveConstraint", app_label):
            return
        super().state_forwards(app_label, state)


class AlterConstraint(OriginalAlterConstraint):
    def state_forwards(self, app_label, state):
        if should_limit_state_apply("AlterConstraint", app_label):
            return
        super().state_forwards(app_label, state)
