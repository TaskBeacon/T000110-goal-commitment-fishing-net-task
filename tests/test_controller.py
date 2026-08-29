from src.utils import FishingNetController


SCRIPT = [
    {"net_size": 20, "offers": {"crab": 5, "octopus": 4, "fish": 3}, "display_order": ["crab", "octopus", "fish"]},
    {"offers": {"crab": 5, "octopus": 7, "fish": 3}, "display_order": ["crab", "octopus", "fish"]},
    {"offers": {"crab": -2, "octopus": 9, "fish": 4}, "display_order": ["octopus", "crab", "fish"]},
    {"offers": {"crab": 10, "octopus": 5, "fish": 2}, "display_order": ["octopus", "crab", "fish"]},
    {"offers": {"crab": 12, "octopus": 7, "fish": 1}, "display_order": ["octopus", "crab", "fish"]},
    {"net_size": 18, "offers": {"crab": 4, "octopus": 6, "fish": 5}, "display_order": ["fish", "octopus", "crab"]},
]


def test_scripted_goal_state_machine() -> None:
    controller = FishingNetController(schedule_mode="scripted", scripted_trials=SCRIPT)
    outcomes = []
    plans = []
    for trial in range(len(SCRIPT)):
        plan = controller.next_trial(session_trial=trial, total_trials=len(SCRIPT))
        plans.append(plan)
        outcomes.append(controller.apply_choice(plan, "1"))

    assert [row["choice_type"] for row in outcomes[:5]] == [
        "initial",
        "persistence",
        "abandonment",
        "persistence",
        "persistence",
    ]
    assert outcomes[2]["abandoned_quantity"] == 10
    assert outcomes[4]["goal_completed"] is True
    assert outcomes[4]["points_after"] == 1
    assert plans[5].goal_started is True
    assert plans[5].goal_index == 2
    assert plans[5].accumulated == 0


def test_negative_offer_never_reduces_net_below_zero() -> None:
    script = [
        {"net_size": 20, "offers": {"crab": -5, "octopus": 1, "fish": 1}, "display_order": ["crab", "octopus", "fish"]}
    ]
    controller = FishingNetController(schedule_mode="scripted", scripted_trials=script)
    plan = controller.next_trial(session_trial=0, total_trials=1)
    outcome = controller.apply_choice(plan, "1")
    assert outcome["accumulated_after"] == 0


def test_stochastic_schedule_is_seed_reproducible() -> None:
    left = FishingNetController(seed=42)
    right = FishingNetController(seed=42)
    left_plan = left.next_trial(session_trial=0, total_trials=10)
    right_plan = right.next_trial(session_trial=0, total_trials=10)
    assert left_plan.net_size == right_plan.net_size
    assert left_plan.offers == right_plan.offers
    assert left_plan.display_order == right_plan.display_order

