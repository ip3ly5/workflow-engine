# Introduction

Effectively, the task is asking us to take an issue of state management for linked events and build it in the "right" way.
When one thing changes state, should something else automatically change too?

I could do something like this: 

if signup.state == "completed":
    verify_email.state = "in_progress"
    add_profile.state = "in_progress"

But that doesn't really make a very nice codebase if we just keep needing to extend "if statements" until the end of time.
and god forbid we do something like this eventually:

if workflow.name == "customer_onboarding":
    ...

elif workflow.name == "supplier_onboarding":

Therefore we offload the logic to the data layer instead.

I can imagine that in the manufacturing and suppliers business, customers may ask for bespoke solutions, 
and rather than whitelabelling the entire software and having to maintain various versions it would be nice to just have a core "Engine" class
that doesn't need to know what "signup" or "verify_profile" does.

Building a "generic" workflow builder is a useful exercise, but maintaining an engine that attempts to solve every possible use case quickly becomes difficult. For this reason, I developed `engine.py` to address the five core test cases according to the task. The engine.py implementation was largely produced with AI, and I deliberately did not spend significant time optimising it, as meaningful optimisation and architectural decisions are difficult to make without a more clearly defined scope or specific use case.

# The workflow engine

The best place to start is with models.py

- **WorkflowDefinition**  
    Defines a reusable workflow and gives it a name. It is the parent of the tasks and links that belong to that workflow.
- **WorkflowExecution**  
    Represents one running instance of a workflow. It tracks the workflow’s current state, such as `pending`, `in_progress`, or `completed`.
- **TaskDefinition** 
    Defines a task that belongs to a workflow. It describes what the task is, not its current state.
- **TaskExecution** 
    Represents a task within a specific workflow run. It tracks that task’s current state.
- **Link**  
    Defines what should change when a rule is satisfied. It targets either a task or the workflow and sets its new state.
- **LinkCondition**  
    Defines what must be true before a `Link` can run. It checks the state of a task or workflow.

Put simply:

The Definitions describe the structure, the Executions store the live state,
and the Links & LinkConditions describe the rules connecting those states.

In factories.py, I create an example onboarding flow under the create_onboarding function. 
Here you can see how a "workflow" can be programmed with rules.

In tests/test_onboarding.py I wrote some tests that achieve the scenarios outputted in the task. I additionally added a "rollback" test, which ensured that 
should one of the tasks fail, it safely rolls back.

There are many things I would change about this implementation, but I took it as more of an architecture exercise as mentioned in the task,
thank you for a task that respects applicants time, it was a fun and thought provoking task.