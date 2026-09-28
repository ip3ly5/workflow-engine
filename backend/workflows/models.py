"""Data shapes for the test contracts; no transition or rule evaluation logic."""

from django.db import models


class WorkflowDefinition(models.Model):
    """Define a reusable workflow and its tasks and Links."""

    name = models.CharField(max_length=200)


class TaskDefinition(models.Model):
    """Define a task that belongs to a workflow."""

    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)


class WorkflowExecution(models.Model):
    """Store the state of one running workflow."""

    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE)
    state = models.CharField(max_length=100, default="pending")

    @property
    def workflow_execution(self):
        """Expose the owning run like TaskExecution does; this is the run itself."""
        return self


class TaskExecution(models.Model):
    """Store the state of a task in one workflow execution."""

    workflow_execution = models.ForeignKey(WorkflowExecution, on_delete=models.CASCADE)
    task = models.ForeignKey(TaskDefinition, on_delete=models.CASCADE)
    state = models.CharField(max_length=100, default="pending")

    class Meta:
        """Enforce one execution per task in each workflow run."""

        constraints = [
            models.UniqueConstraint(
                fields=["workflow_execution", "task"],
                name="one_task_per_workflow_execution",
            )
        ]


class Link(models.Model):
    """Describe a state change targeting either a workflow or a task."""

    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE)
    target_workflow = models.ForeignKey(
        WorkflowDefinition,
        null=True,
        blank=True,
        related_name="target_links",
        on_delete=models.CASCADE,
    )
    target_task = models.ForeignKey(
        TaskDefinition, null=True, blank=True, on_delete=models.CASCADE
    )
    target_state = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(target_workflow__isnull=False, target_task__isnull=True)
                    | models.Q(target_workflow__isnull=True, target_task__isnull=False)
                ),
                name="link_has_exactly_one_target",
            )
        ]


class LinkCondition(models.Model):
    """Describe a required state for either a workflow or a task."""

    link = models.ForeignKey(Link, related_name="conditions", on_delete=models.CASCADE)
    workflow = models.ForeignKey(
        WorkflowDefinition, null=True, blank=True, on_delete=models.CASCADE
    )
    task = models.ForeignKey(
        TaskDefinition, null=True, blank=True, on_delete=models.CASCADE
    )
    state = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(workflow__isnull=False, task__isnull=True)
                    | models.Q(workflow__isnull=True, task__isnull=False)
                ),
                name="condition_has_exactly_one_component",
            )
        ]
