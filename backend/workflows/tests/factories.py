"""Small ORM fixtures only: setting a starting state never invokes the engine."""

from typing import TypedDict

from workflows.models import (
    Link,
    LinkCondition,
    TaskDefinition,
    TaskExecution,
    WorkflowDefinition,
    WorkflowExecution,
)


class OnboardingRun(TypedDict):
    workflow_definition: WorkflowDefinition
    workflow: WorkflowExecution
    signup: TaskExecution
    verify_email: TaskExecution
    add_profile: TaskExecution


def create_onboarding(
    workflow_state="pending",
    signup_state="pending",
    verify_email_state="pending",
    add_profile_state="pending",
) -> OnboardingRun:
    """Create one onboarding run; every starting state defaults to pending."""

    # Define the workflow and the three tasks that belong to it
    definition = WorkflowDefinition.objects.create(name="Onboarding")
    signup = TaskDefinition.objects.create(workflow=definition, name="Sign Up")
    verify_email = TaskDefinition.objects.create(
        workflow=definition, name="Verify Email"
    )
    add_profile = TaskDefinition.objects.create(workflow=definition, name="Add Profile")

    # Setting the rules

    start_signup = Link.objects.create(
        workflow=definition,
        target_task=signup,
        target_state="in_progress",
    )
    LinkCondition.objects.create(
        link=start_signup,
        workflow=definition,
        state="in_progress",
    )

    start_verify_email = Link.objects.create(
        workflow=definition,
        target_task=verify_email,
        target_state="in_progress",
    )
    LinkCondition.objects.create(
        link=start_verify_email,
        task=signup,
        state="completed",
    )

    start_add_profile = Link.objects.create(
        workflow=definition,
        target_task=add_profile,
        target_state="in_progress",
    )
    LinkCondition.objects.create(
        link=start_add_profile,
        task=signup,
        state="completed",
    )

    complete_workflow = Link.objects.create(
        workflow=definition,
        target_workflow=definition,
        target_state="completed",
    )
    LinkCondition.objects.create(
        link=complete_workflow,
        task=verify_email,
        state="completed",
    )
    LinkCondition.objects.create(
        link=complete_workflow,
        task=add_profile,
        state="completed",
    )

    workflow_execution = WorkflowExecution.objects.create(
        workflow=definition,
        state=workflow_state,
    )
    signup_execution = TaskExecution.objects.create(
        workflow_execution=workflow_execution,
        task=signup,
        state=signup_state,
    )
    verify_email_execution = TaskExecution.objects.create(
        workflow_execution=workflow_execution,
        task=verify_email,
        state=verify_email_state,
    )
    add_profile_execution = TaskExecution.objects.create(
        workflow_execution=workflow_execution,
        task=add_profile,
        state=add_profile_state,
    )

    return {
        "workflow_definition": definition,
        "workflow": workflow_execution,
        "signup": signup_execution,
        "verify_email": verify_email_execution,
        "add_profile": add_profile_execution,
    }
