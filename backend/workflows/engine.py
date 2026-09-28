from django.db import transaction

from workflows.models import Link, TaskExecution, WorkflowExecution


class WorkflowEngine:
    """Apply state changes and cascading Links to workflow executions."""

    @transaction.atomic
    def transition(
        self, execution: WorkflowExecution | TaskExecution, state: str
    ) -> None:
        """Change an execution's state atomically and apply its matching Links.

        Accept a WorkflowExecution or TaskExecution;
        An unchanged state is a no-op, including for downstream transitions.

        Each change can trigger Links that add further changes to a list.
        Process that list in order, saving the whole cascade only if every step
        succeeds. The atomic decorator rolls back database changes on failure.
        """
        if not isinstance(execution, (WorkflowExecution, TaskExecution)):
            raise TypeError("Expected a WorkflowExecution or TaskExecution.")

        workflow_execution = execution.workflow_execution

        task_executions_by_id = {}
        for task_execution in workflow_execution.taskexecution_set.all():
            task_executions_by_id[task_execution.task_id] = task_execution
        if isinstance(execution, TaskExecution):
            task_executions_by_id[execution.task_id] = execution
        workflow_links = Link.objects.filter(workflow_id=workflow_execution.workflow_id)

        pending_transitions = [(execution, state)]
        while pending_transitions:
            current_execution, target_state = pending_transitions.pop(0)
            if current_execution.state == target_state:
                continue

            current_execution.state = target_state
            current_execution.save(update_fields=["state"])

            if isinstance(current_execution, TaskExecution):
                affected_links = workflow_links.filter(
                    conditions__task_id=current_execution.task_id,
                    conditions__state=target_state,
                )
            else:
                affected_links = workflow_links.filter(
                    conditions__workflow_id=workflow_execution.workflow_id,
                    conditions__state=target_state,
                )

            for link in affected_links.distinct():
                all_conditions_match = True
                for condition in link.conditions.all():
                    if (
                        condition.workflow_id is not None
                        and condition.workflow_id != workflow_execution.workflow_id
                    ):
                        raise ValueError(
                            "A Link condition must belong to this workflow."
                        )

                    if condition.workflow_id is not None:
                        condition_execution = workflow_execution
                    else:
                        condition_execution = task_executions_by_id[condition.task_id]
                    if condition_execution.state != condition.state:
                        all_conditions_match = False
                        break

                if not all_conditions_match:
                    continue

                if (
                    link.target_workflow_id is not None
                    and link.target_workflow_id != workflow_execution.workflow_id
                ):
                    raise ValueError("A Link target must belong to this workflow.")

                if link.target_workflow_id is not None:
                    target_execution = workflow_execution
                else:
                    target_execution = task_executions_by_id[link.target_task_id]
                pending_transitions.append((target_execution, link.target_state))
