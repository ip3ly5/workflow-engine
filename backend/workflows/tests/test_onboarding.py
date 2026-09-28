from django.test import TestCase

from workflows.engine import WorkflowEngine
from workflows.models import Link, LinkCondition, WorkflowDefinition
from workflows.tests.factories import create_onboarding


class OnboardingTests(TestCase):
    """Specify onboarding state transitions through the public engine API."""

    def setUp(self):
        """Create an engine for each isolated test."""
        self.engine = WorkflowEngine()

    def assert_state(self, execution, expected_state):
        """Check one execution's saved state."""
        # Read from the database so changing only the Python object cannot pass.
        execution.refresh_from_db()
        self.assertEqual(execution.state, expected_state)

    def test_starting_workflow_starts_signup(self):
        """Starting the workflow starts the Sign Up task."""
        run = create_onboarding()

        self.engine.transition(run["workflow"], "in_progress")

        self.assert_state(run["workflow"], "in_progress")
        self.assert_state(run["signup"], "in_progress")

    def test_completing_signup_starts_both_parallel_tasks(self):
        """Completing Sign Up starts both onboarding branches."""
        run = create_onboarding(
            workflow_state="in_progress", signup_state="in_progress"
        )

        self.engine.transition(run["signup"], "completed")

        self.assert_state(run["signup"], "completed")
        self.assert_state(run["verify_email"], "in_progress")
        self.assert_state(run["add_profile"], "in_progress")

    def test_workflow_completes_only_after_both_tasks_complete(self):
        """The workflow completes when the final required branch completes."""
        run = create_onboarding(
            workflow_state="in_progress",
            signup_state="completed",
            verify_email_state="in_progress",
            add_profile_state="in_progress",
        )

        self.engine.transition(run["verify_email"], "completed")
        self.assert_state(run["workflow"], "in_progress")
        self.assert_state(run["verify_email"], "completed")

        self.engine.transition(run["add_profile"], "completed")
        self.assert_state(run["workflow"], "completed")
        self.assert_state(run["verify_email"], "completed")
        self.assert_state(run["add_profile"], "completed")

    def test_task_can_start_workflow_and_cascade_to_another_task(self):
        """A task can start its workflow and trigger a second Link."""
        run = create_onboarding()
        start_workflow = Link.objects.create(
            workflow=run["workflow_definition"],
            target_workflow=run["workflow_definition"],
            target_state="in_progress",
        )
        LinkCondition.objects.create(
            link=start_workflow,
            task=run["verify_email"].task,
            state="in_progress",
        )

        self.engine.transition(run["verify_email"], "in_progress")

        self.assert_state(run["verify_email"], "in_progress")
        self.assert_state(run["workflow"], "in_progress")
        self.assert_state(run["signup"], "in_progress")

    def test_task_can_move_back_to_a_previous_state(self):
        """A task can return to an earlier state."""
        # "From any state to any other state. Even going back to a previous state."
        run = create_onboarding(verify_email_state="completed")

        self.engine.transition(run["verify_email"], "in_progress")

        self.assert_state(run["verify_email"], "in_progress")
        self.assert_state(run["workflow"], "pending")

    def test_repeating_the_current_state_is_a_noop(self):
        """Repeating a task's current state leaves linked tasks unchanged."""
        run = create_onboarding(signup_state="in_progress")

        self.engine.transition(run["signup"], "in_progress")

        self.assert_state(run["signup"], "in_progress")
        self.assert_state(run["verify_email"], "pending")
        self.assert_state(run["add_profile"], "pending")

    def test_cascade_can_change_the_original_task_again(self):
        """Links can revisit the caller's task and update that same instance."""
        run = create_onboarding()
        start_workflow = Link.objects.create(
            workflow=run["workflow_definition"],
            target_workflow=run["workflow_definition"],
            target_state="in_progress",
        )
        LinkCondition.objects.create(
            link=start_workflow,
            task=run["verify_email"].task,
            state="in_progress",
        )
        complete_verify_email = Link.objects.create(
            workflow=run["workflow_definition"],
            target_task=run["verify_email"].task,
            target_state="completed",
        )
        LinkCondition.objects.create(
            link=complete_verify_email,
            workflow=run["workflow_definition"],
            state="in_progress",
        )

        self.engine.transition(run["verify_email"], "in_progress")

        self.assertEqual(run["verify_email"].state, "completed")
        self.assert_state(run["workflow"], "in_progress")
        self.assert_state(run["signup"], "in_progress")
        self.assert_state(run["verify_email"], "completed")
        self.assert_state(run["add_profile"], "pending")

    def test_failed_link_rolls_back_the_state_change(self):
        """A Link with a target in another workflow fails and rolls back."""
        run = create_onboarding(signup_state="in_progress")
        other_workflow = WorkflowDefinition.objects.create(name="Other workflow")
        invalid_link = Link.objects.create(
            workflow=run["workflow_definition"],
            target_workflow=other_workflow,
            target_state="completed",
        )
        LinkCondition.objects.create(
            link=invalid_link,
            task=run["signup"].task,
            state="completed",
        )

        with self.assertRaises(ValueError):
            self.engine.transition(run["signup"], "completed")

        self.assert_state(run["signup"], "in_progress")
        self.assert_state(run["verify_email"], "pending")
        self.assert_state(run["add_profile"], "pending")
