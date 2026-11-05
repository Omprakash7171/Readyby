"""The status machine is the contract between the customer app and the café."""

from __future__ import annotations

from django.test import SimpleTestCase

from orders.models import OrderStatus
from orders.presentation import STATUS_LABEL, progress_rank
from orders.state import (
    ALLOWED_TRANSITIONS,
    BOARD_COLUMNS,
    MERCHANT_ACTIONS,
    can_transition,
    customer_may_cancel,
    is_terminal,
    merchant_may_cancel,
    merchant_may_reject,
    next_status,
)

HAPPY_PATH = [
    OrderStatus.PLACED,
    OrderStatus.ACCEPTED,
    OrderStatus.PREPARING,
    OrderStatus.READY,
    OrderStatus.COLLECTED,
]


class FakeOrder:
    """The permission helpers only ever read ``status``."""

    def __init__(self, status: str) -> None:
        self.status = status


class TransitionTableTests(SimpleTestCase):
    def test_the_happy_path_is_allowed(self):
        for current, following in zip(HAPPY_PATH, HAPPY_PATH[1:]):
            with self.subTest(current=current, following=following):
                self.assertTrue(can_transition(current, following))

    def test_every_status_is_declared(self):
        for status in OrderStatus.values:
            self.assertIn(status, ALLOWED_TRANSITIONS)

    def test_no_status_may_skip_a_stage(self):
        forbidden = [
            (OrderStatus.PLACED, OrderStatus.PREPARING),
            (OrderStatus.PLACED, OrderStatus.READY),
            (OrderStatus.PLACED, OrderStatus.COLLECTED),
            (OrderStatus.ACCEPTED, OrderStatus.READY),
            (OrderStatus.ACCEPTED, OrderStatus.COLLECTED),
            (OrderStatus.PREPARING, OrderStatus.COLLECTED),
        ]
        for current, target in forbidden:
            with self.subTest(current=current, target=target):
                self.assertFalse(can_transition(current, target))

    def test_no_status_may_go_backwards(self):
        for current, following in zip(HAPPY_PATH, HAPPY_PATH[1:]):
            with self.subTest(current=current, following=following):
                self.assertFalse(can_transition(following, current))

    def test_cannot_resurrect_a_finished_order(self):
        for finished in (
            OrderStatus.COLLECTED,
            OrderStatus.REJECTED,
            OrderStatus.CANCELLED,
        ):
            for target in OrderStatus.values:
                with self.subTest(finished=finished, target=target):
                    self.assertFalse(can_transition(finished, target))
                    self.assertTrue(is_terminal(finished))

    def test_preparing_orders_cannot_be_cancelled(self):
        """Once the drink is on the bar, the café must finish it."""
        self.assertFalse(can_transition(OrderStatus.PREPARING, OrderStatus.CANCELLED))


class NextStatusTests(SimpleTestCase):
    def test_next_status_follows_the_happy_path(self):
        self.assertEqual(next_status(OrderStatus.PLACED), OrderStatus.ACCEPTED)
        self.assertEqual(next_status(OrderStatus.ACCEPTED), OrderStatus.PREPARING)
        self.assertEqual(next_status(OrderStatus.PREPARING), OrderStatus.READY)
        self.assertEqual(next_status(OrderStatus.READY), OrderStatus.COLLECTED)

    def test_next_status_is_none_at_the_end(self):
        self.assertIsNone(next_status(OrderStatus.COLLECTED))
        self.assertIsNone(next_status(OrderStatus.CANCELLED))


class CancellationPermissionTests(SimpleTestCase):
    def test_a_customer_can_walk_away_before_it_is_made(self):
        self.assertTrue(customer_may_cancel(FakeOrder(OrderStatus.PLACED)))
        self.assertTrue(customer_may_cancel(FakeOrder(OrderStatus.ACCEPTED)))
        self.assertFalse(customer_may_cancel(FakeOrder(OrderStatus.PREPARING)))
        self.assertFalse(customer_may_cancel(FakeOrder(OrderStatus.READY)))
        self.assertFalse(customer_may_cancel(FakeOrder(OrderStatus.COLLECTED)))

    def test_a_cafe_may_decline_up_to_the_moment_of_preparation(self):
        self.assertTrue(merchant_may_cancel(FakeOrder(OrderStatus.PLACED)))
        self.assertTrue(merchant_may_cancel(FakeOrder(OrderStatus.ACCEPTED)))
        self.assertFalse(merchant_may_cancel(FakeOrder(OrderStatus.PREPARING)))
        self.assertFalse(merchant_may_cancel(FakeOrder(OrderStatus.READY)))
        self.assertFalse(merchant_may_cancel(FakeOrder(OrderStatus.COLLECTED)))

    def test_cancellation_permission_agrees_with_the_transition_table(self):
        """The helpers and the table must never contradict each other."""
        for status in OrderStatus.values:
            order = FakeOrder(status)
            if customer_may_cancel(order) or merchant_may_cancel(order):
                with self.subTest(status=status):
                    self.assertTrue(can_transition(status, OrderStatus.CANCELLED))


class RejectionTests(SimpleTestCase):
    """``REJECTED`` is the café saying no. It is not a customer cancellation."""

    def test_a_cafe_may_reject_a_new_order(self):
        self.assertTrue(can_transition(OrderStatus.PLACED, OrderStatus.REJECTED))

    def test_rejection_is_only_reachable_from_placed(self):
        for status in OrderStatus.values:
            if status == OrderStatus.PLACED:
                continue
            with self.subTest(status=status):
                self.assertFalse(can_transition(status, OrderStatus.REJECTED))

    def test_only_a_placed_order_may_be_rejected(self):
        self.assertTrue(merchant_may_reject(FakeOrder(OrderStatus.PLACED)))
        self.assertFalse(merchant_may_reject(FakeOrder(OrderStatus.ACCEPTED)))
        self.assertFalse(merchant_may_reject(FakeOrder(OrderStatus.PREPARING)))
        self.assertFalse(merchant_may_reject(FakeOrder(OrderStatus.READY)))
        self.assertFalse(merchant_may_reject(FakeOrder(OrderStatus.REJECTED)))

    def test_rejection_permission_agrees_with_the_transition_table(self):
        for status in OrderStatus.values:
            with self.subTest(status=status):
                self.assertEqual(
                    merchant_may_reject(FakeOrder(status)),
                    can_transition(status, OrderStatus.REJECTED),
                )

    def test_a_rejected_order_has_no_next_step(self):
        self.assertIsNone(next_status(OrderStatus.REJECTED))
        self.assertIsNone(MERCHANT_ACTIONS[OrderStatus.REJECTED])

    def test_rejection_is_distinct_from_cancellation(self):
        """Both are reachable from PLACED, so neither may imply the other."""
        self.assertTrue(can_transition(OrderStatus.PLACED, OrderStatus.CANCELLED))
        self.assertNotEqual(OrderStatus.REJECTED, OrderStatus.CANCELLED)
        self.assertNotEqual(STATUS_LABEL[OrderStatus.REJECTED], STATUS_LABEL[OrderStatus.CANCELLED])


class BoardAndPresentationTests(SimpleTestCase):
    def test_every_status_appears_in_exactly_one_board_column(self):
        columns = [status for statuses in BOARD_COLUMNS.values() for status in statuses]
        self.assertEqual(sorted(columns), sorted(OrderStatus.values))

    def test_every_status_has_a_merchant_action_or_is_terminal(self):
        for status in OrderStatus.values:
            with self.subTest(status=status):
                action = MERCHANT_ACTIONS[status]
                if is_terminal(status):
                    self.assertIsNone(action)
                else:
                    self.assertIsNotNone(action)

    def test_merchant_actions_only_offer_legal_transitions(self):
        for status, action in MERCHANT_ACTIONS.items():
            if action is None:
                continue
            target, _label = action
            with self.subTest(status=status):
                self.assertTrue(can_transition(status, target))

    def test_every_status_has_customer_facing_copy(self):
        for status in OrderStatus.values:
            self.assertTrue(STATUS_LABEL[status])

    def test_progress_rank_increases_along_the_happy_path(self):
        ranks = [progress_rank(status) for status in HAPPY_PATH]
        self.assertEqual(ranks, sorted(ranks))
        self.assertEqual(progress_rank(OrderStatus.CANCELLED), -1)