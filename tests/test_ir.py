"""Feature 004: operation lists (spec FR-018 to FR-020; research R11, R13, R14; T046).

The lists here are stated by hand, and their inputs come from protocol/devinputs_v3.py, as every use's
do. research/004/candidates/ is read as it fills. This file makes no security claim.
"""
import ast
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

from protocol import devinputs_v3

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "research/004/candidates"
if str(ROOT / "research/004") not in sys.path:
    sys.path.insert(0, str(ROOT / "research/004"))

import ir  # noqa: E402


P, V = 0, 1


def stated_list(n: int, w: int) -> "ir.Program":
    """A two- or three-colour list: each colour's veins take their neighbours' pressure, its
    pressure takes its veins, and one round constant enters at a node of each colour's phase."""
    a, b = max(1, w // 4), max(1, w // 2 - 1)
    phases = []
    for colour in range(ir.colours(n)):
        veins, pressure, turns = [], [], []
        for i, j in ir.nodes_of(n, colour):
            east = ir.lane(n, i, (j + 1) % n, P)
            south = ir.lane(n, (i + 1) % n, j, P)
            read = ir.Xor(ir.Rotl(ir.Lane(east), a), ir.Lane(south))
            veins.append(ir.Mix(ir.lane(n, i, j, V), "add", read))
            own = ir.Lane(ir.lane(n, i, j, V))
            pressure.append(ir.Mix(ir.lane(n, i, j, P), "xor",
                                   ir.And(ir.Rotl(own, b), ir.Not(ir.Shr(own, 1)))))
            turns.append(ir.Rot(ir.lane(n, i, j, V), a))
        phases.append(ir.Phase(colour, tuple(veins)))
        phases.append(ir.Phase(colour, tuple(pressure)))
        phases.append(ir.Phase(colour, tuple(turns)))
        i, j = ir.nodes_of(n, colour)[0]
        phases.append(ir.Phase(colour, (ir.Mix(ir.lane(n, i, j, P), "sub", ir.Constant(0)),)))
    return ir.Program("stated", n, w, tuple(phases))


def two_steps_east(n: int, w: int) -> "ir.Program":
    """One update takes a node's own vein, and another writes the vein two steps east of it, which
    at 2×2 is that node itself, where a node's opposite neighbours coincide (R14)."""
    first = ir.Mix(ir.lane(n, 0, 0, P), "xor", ir.Lane(ir.lane(n, 0, 0, V)))
    second = ir.Mix(ir.lane(n, 0, 2, V), "xor", ir.Lane(ir.lane(n, 0, 3, P)))
    one, other = ir.colour(n, 0, 0), ir.colour(n, 0, 2)
    if one == other:
        return ir.Program("two steps east", n, w, (ir.Phase(one, (first, second)),))
    return ir.Program("two steps east", n, w, (ir.Phase(one, (first,)), ir.Phase(other, (second,))))


def coincides_at(pair):
    """Two updates that share a node, and so break the rule, at the one size and width `pair`, and
    that stand in two phases of two colours everywhere else."""
    def build(n: int, w: int) -> "ir.Program":
        j = 0 if (n, w) == pair else 1
        first = ir.Mix(ir.lane(n, 0, 0, P), "xor", ir.Lane(ir.lane(n, 0, 0, V)))
        second = ir.Mix(ir.lane(n, 0, j, V), "xor", ir.Lane(ir.lane(n, 1, j, P)))
        if j == 0:
            return ir.Program("coincides", n, w, (ir.Phase(0, (first, second)),))
        return ir.Program("coincides", n, w,
                          (ir.Phase(0, (first,)), ir.Phase(ir.colour(n, 0, 1), (second,))))
    return build


def single(n: int, w: int, *updates) -> "ir.Program":
    return ir.Program("one phase", n, w, (ir.Phase(0, tuple(updates)),))


def states(n: int, w: int, count: int = 16):
    return [list(value) for value in devinputs_v3.load("dev", "state", ("dev",), count, n=n, w=w)]


def round_constants(n: int, w: int, rounds: int):
    """A stated table for these tests, not a constant rule: a counter under the width's mask."""
    return [(((r * 2 + 1) * 0x9D) & ((1 << w) - 1),) for r in range(rounds)]


class Colouring(unittest.TestCase):

    def links(self, n: int):
        for i in range(n):
            for j in range(n):
                yield (i, j), ((i + 1) % n, j)
                yield (i, j), (i, (j + 1) % n)

    def test_two_colours_for_every_even_n(self):
        for n in range(2, 17, 2):
            self.assertEqual(ir.colours(n), 2)
            for a, b in self.links(n):
                self.assertNotEqual(ir.colour(n, *a), ir.colour(n, *b), (n, a, b))

    def test_three_colours_for_every_odd_n_wrap_around_links_included(self):
        for n in range(3, 16, 2):
            self.assertEqual(ir.colours(n), 3)
            for a, b in self.links(n):
                self.assertNotEqual(ir.colour(n, *a), ir.colour(n, *b), (n, a, b))
            self.assertEqual({ir.colour(n, i, j) for i in range(n) for j in range(n)}, {0, 1, 2})

    def test_the_simple_rule_fails_where_the_spec_says(self):
        """So that the test above can fail: (i + j) mod 3 at n = 7 and 13."""
        broken = [n for n in range(3, 16, 2) if any(
            (a[0] + a[1]) % 3 == (b[0] + b[1]) % 3 for a, b in self.links(n))]
        self.assertIn(7, broken)
        self.assertIn(13, broken)

    def test_every_node_has_one_colour_class(self):
        for n in (2, 3, 4, 5, 8, 16):
            found = sorted(node for c in range(ir.colours(n)) for node in ir.nodes_of(n, c))
            self.assertEqual(found, [(i, j) for i in range(n) for j in range(n)])

    def test_lanes_are_numbered_by_node_then_kind(self):
        self.assertEqual(ir.lane(4, 0, 0, P), 0)
        self.assertEqual(ir.lane(4, 0, 0, V), 1)
        self.assertEqual(ir.lane(4, 1, 2, V), 2 * (4 + 2) + 1)
        self.assertEqual(ir.node_of(4, 13), (1, 2))

    def test_lanes_and_colours_wrap_around_the_torus(self):
        self.assertEqual(ir.lane(4, 4, -1, P), ir.lane(4, 0, 3, P))
        for n in (2, 3, 4, 5, 7):
            for i in range(-1, n + 2):
                for j in range(-1, n + 2):
                    self.assertEqual(ir.colour(n, i, j), ir.colour(n, i % n, j % n), (n, i, j))


class Loader(unittest.TestCase):

    N, W = 4, 8

    def refused(self, program, words: str):
        with self.assertRaisesRegex(ir.ListRefused, words):
            ir.load(program)

    def lanes(self):
        return ir.lane(4, 0, 0, P), ir.lane(4, 0, 0, V), ir.lane(4, 0, 1, P), ir.lane(4, 1, 0, P)

    def test_a_stated_list_loads_at_every_supported_size(self):
        for n, w in devinputs_v3.PAIRS:
            ir.load(stated_list(n, w))

    def test_every_size_is_checked_by_one_call(self):
        self.assertEqual(len(ir.check_every_size(stated_list)), len(devinputs_v3.PAIRS))

    def test_a_list_that_breaks_the_rule_at_one_size_only_is_refused_there(self):
        with self.assertRaisesRegex(ir.ListRefused, "n=2"):
            ir.check_every_size(two_steps_east)
        for n, w in devinputs_v3.PAIRS:
            if n == 2:
                with self.assertRaisesRegex(ir.ListRefused, "reads a lane"):
                    ir.load(two_steps_east(n, w))
            else:
                ir.load(two_steps_east(n, w))

    def test_every_size_and_width_is_reached(self):
        for pair in devinputs_v3.PAIRS:
            with self.assertRaisesRegex(ir.ListRefused, f"n={pair[0]}, w={pair[1]}: .*reads a lane"):
                ir.check_every_size(coincides_at(pair))
            for n, w in devinputs_v3.PAIRS:
                if (n, w) != pair:
                    ir.load(coincides_at(pair)(n, w))

    def test_only_the_two_forms_load(self):
        p, _, _, _ = self.lanes()
        self.refused(single(4, 8, ("not", "an", "update")), "form")
        self.refused(single(4, 8, ir.Lane(p)), "form")

    def test_a_mix_that_reads_its_own_lane_is_refused(self):
        p, _, _, _ = self.lanes()
        self.refused(single(4, 8, ir.Mix(p, "xor", ir.Lane(p))), "dst")
        self.refused(single(4, 8, ir.Mix(p, "add", ir.Rotl(ir.Lane(p), 1))), "dst")

    def test_only_three_operators_mix(self):
        p, v, _, _ = self.lanes()
        self.refused(single(4, 8, ir.Mix(p, "mul", ir.Lane(v))), "operator")

    def test_no_addition_or_data_dependent_amount_can_stand_in_f(self):
        p, v, _, _ = self.lanes()
        self.refused(single(4, 8, ir.Mix(p, "xor", ("add", ir.Lane(v), ir.Lane(v)))), "expression")
        self.refused(single(4, 8, ir.Mix(p, "xor", ir.Rotl(ir.Lane(v), ir.Lane(v)))), "amount")
        self.refused(single(4, 8, ir.Rot(p, ir.Lane(v))), "amount")
        self.refused(single(4, 8, ir.Rot(p, True)), "amount")

    def test_a_constant_comes_from_the_table_alone(self):
        p, _, _, _ = self.lanes()
        self.refused(single(4, 8, ir.Mix(p, "xor", 0x5A)), "expression")
        self.refused(single(4, 8, ir.Mix(p, "xor", ir.Constant(-1))), "constant")
        self.refused(single(4, 8, ir.Mix(p, "xor", ir.Constant(True))), "constant")
        self.assertFalse(hasattr(ir, "Literal"))

    def test_a_rotation_or_shift_of_0_or_w_is_refused(self):
        p, v, _, _ = self.lanes()
        for amount in (0, 8, 9, -1):
            self.refused(single(4, 8, ir.Rot(p, amount)), "amount")
            self.refused(single(4, 8, ir.Mix(p, "xor", ir.Rotl(ir.Lane(v), amount))), "amount")
            self.refused(single(4, 8, ir.Mix(p, "xor", ir.Shr(ir.Lane(v), amount))), "amount")
            self.refused(single(4, 8, ir.Mix(p, "xor", ir.Shl(ir.Lane(v), amount))), "amount")

    def test_a_lane_outside_the_state_is_refused(self):
        p, _, _, _ = self.lanes()
        self.refused(single(4, 8, ir.Mix(32, "xor", ir.Lane(p))), "outside the state")
        self.refused(single(4, 8, ir.Mix(-1, "xor", ir.Lane(p))), "outside the state")
        self.refused(single(4, 8, ir.Mix(p, "xor", ir.Lane(32))), "outside the state")
        self.refused(single(4, 8, ir.Mix(p, "xor", ir.Lane(-1))), "outside the state")
        self.refused(single(4, 8, ir.Rot(32, 1)), "outside the state")
        self.refused(single(4, 8, ir.Rot(-1, 1)), "outside the state")

    def test_the_inside_of_f_is_checked_at_every_depth(self):
        p, v, _, _ = self.lanes()
        bad = ir.Rotl(ir.Lane(v), 0)
        good = ir.Lane(v)
        for expr in (ir.Rotl(bad, 1), ir.Shl(bad, 1), ir.Shr(bad, 1), ir.Not(bad),
                     ir.Xor(good, bad), ir.Xor(bad, good), ir.And(good, bad), ir.And(bad, good),
                     ir.Or(good, bad), ir.Or(bad, good), ir.Not(ir.Xor(good, ir.Not(bad)))):
            self.refused(single(4, 8, ir.Mix(p, "xor", expr)), "amount")

    def test_an_update_may_not_read_a_lane_another_of_its_phase_writes(self):
        p, v, east, _ = self.lanes()
        self.refused(single(4, 8, ir.Mix(v, "xor", ir.Lane(p)), ir.Mix(p, "xor", ir.Lane(east))),
                     "reads a lane")
        self.refused(single(4, 8, ir.Mix(v, "xor", ir.Lane(p)), ir.Rot(p, 1)), "reads a lane")

    def test_the_rule_looks_both_ways_along_a_phase(self):
        p, v, east, _ = self.lanes()
        reader, writer = ir.Mix(v, "xor", ir.Lane(p)), ir.Mix(p, "xor", ir.Lane(east))
        self.refused(single(4, 8, reader, writer), "reads a lane")
        self.refused(single(4, 8, writer, reader), "reads a lane")

    def test_two_updates_of_one_lane_in_a_phase_are_refused(self):
        p, v, east, _ = self.lanes()
        self.refused(single(4, 8, ir.Mix(p, "xor", ir.Lane(v)), ir.Mix(p, "add", ir.Lane(east))),
                     "reads a lane")
        self.refused(single(4, 8, ir.Rot(p, 1), ir.Rot(p, 2)), "reads a lane")

    def test_the_same_updates_in_two_phases_load(self):
        p, v, east, _ = self.lanes()
        ir.load(ir.Program("two phases", 4, 8, (
            ir.Phase(0, (ir.Mix(v, "xor", ir.Lane(p)),)),
            ir.Phase(0, (ir.Mix(p, "xor", ir.Lane(east)),)))))

    def test_data_flows_only_between_direct_neighbours(self):
        p, _, _, _ = self.lanes()
        far = ir.lane(4, 2, 0, P)
        diagonal = ir.lane(4, 1, 1, P)
        self.refused(single(4, 8, ir.Mix(p, "xor", ir.Lane(far))), "neighbour")
        self.refused(single(4, 8, ir.Mix(p, "xor", ir.Lane(diagonal))), "neighbour")

    def test_the_wrap_around_links_are_direct(self):
        p, _, _, _ = self.lanes()
        ir.load(single(4, 8, ir.Mix(p, "xor", ir.Lane(ir.lane(4, 3, 0, P)))))
        ir.load(single(4, 8, ir.Mix(p, "xor", ir.Lane(ir.lane(4, 0, 3, P)))))

    def four(self):
        return [ir.lane(4, 0, 1, P), ir.lane(4, 0, 3, P), ir.lane(4, 1, 0, P), ir.lane(4, 3, 0, P)]

    def test_a_node_receives_at_most_four_channels_per_phase(self):
        p, v, _, _ = self.lanes()
        reads = self.four()
        expr = ir.Lane(reads[0])
        for lane in reads[1:]:
            expr = ir.Xor(expr, ir.Lane(lane))
        ir.load(single(4, 8, ir.Mix(p, "xor", expr)))
        fifth = ir.Xor(expr, ir.Lane(ir.lane(4, 0, 1, V)))
        self.refused(single(4, 8, ir.Mix(p, "xor", fifth)), "channels")

    def test_channels_are_counted_per_node_across_its_updates(self):
        p, v, _, _ = self.lanes()
        reads = self.four()
        split = ir.Program("split", 4, 8, (ir.Phase(0, (
            ir.Mix(p, "xor", ir.Xor(ir.Lane(reads[0]), ir.Lane(reads[1]))),
            ir.Mix(v, "xor", ir.Xor(ir.Xor(ir.Lane(reads[2]), ir.Lane(reads[3])),
                                    ir.Lane(ir.lane(4, 0, 1, V))))),),))
        self.refused(split, "channels")

    def test_one_word_read_twice_by_a_node_is_one_channel(self):
        p, v, _, _ = self.lanes()
        reads = self.four()
        ir.load(ir.Program("shared", 4, 8, (ir.Phase(0, (
            ir.Mix(p, "xor", ir.Xor(ir.Xor(ir.Lane(reads[0]), ir.Lane(reads[1])), ir.Lane(reads[2]))),
            ir.Mix(v, "xor", ir.Xor(ir.Lane(reads[0]), ir.Lane(reads[3])))),),)))

    def test_a_nodes_own_lanes_are_no_channel(self):
        p, v, _, _ = self.lanes()
        reads = self.four()
        expr = ir.Lane(v)
        for lane in reads:
            expr = ir.Xor(expr, ir.Lane(lane))
        ir.load(single(4, 8, ir.Mix(p, "xor", expr)))

    def test_at_two_by_two_two_channels_from_each_of_two_neighbours(self):
        expr = ir.Xor(ir.Xor(ir.Lane(ir.lane(2, 0, 1, P)), ir.Lane(ir.lane(2, 0, 1, V))),
                      ir.Xor(ir.Lane(ir.lane(2, 1, 0, P)), ir.Lane(ir.lane(2, 1, 0, V))))
        ir.load(single(2, 16, ir.Mix(ir.lane(2, 0, 0, P), "xor", expr)))

    def test_an_update_outside_its_phases_colour_is_refused(self):
        other = ir.lane(4, 0, 1, P)
        self.assertNotEqual(ir.colour(4, 0, 1), 0)
        self.refused(single(4, 8, ir.Rot(other, 1)), "colour")

    def test_an_unknown_colour_is_refused(self):
        self.refused(ir.Program("no colour", 4, 8, (ir.Phase(2, ()),)), "colour")

    def test_an_empty_list_is_refused(self):
        self.refused(ir.Program("empty", 4, 8, ()), "phase")

    def test_a_size_or_width_outside_the_supported_pairs_is_refused(self):
        for n, w in ((5, 8), (4, 4), (16, 64), (4.0, 8), ("4", 8)):
            self.refused(ir.Program("size", n, w, (ir.Phase(0, ()),)), "no supported")

    def test_exploration_sizes_load_when_asked(self):
        p = ir.lane(5, 0, 0, P)
        ir.load(ir.Program("explore", 5, 16, (ir.Phase(0, (ir.Rot(p, 1),)),)), exploration=True)

    def test_exploration_stops_at_the_sizes_of_the_spec(self):
        for n, w in ((1, 8), (17, 8), (5, 4), (5, 64), (5.0, 8)):
            with self.assertRaisesRegex(ir.ListRefused, "no supported"):
                ir.load(ir.Program("size", n, w, (ir.Phase(0, ()),)), exploration=True)

    def test_a_refusal_is_the_writers_refusal(self):
        from protocol.evidence import Refused
        self.assertTrue(issubclass(ir.ListRefused, Refused))


class Expressions(unittest.TestCase):
    """Each operation of F, on stated values at w = 8, in both interpreters."""

    def result(self, expr, a=0xB4, b=0x0F, operator="xor", start=0):
        lanes = [0] * 8
        src, other, dst = ir.lane(2, 0, 1, P), ir.lane(2, 1, 0, P), ir.lane(2, 0, 0, P)
        lanes[src], lanes[other], lanes[dst] = a, b, start
        loaded = ir.load(ir.Program("one", 2, 8, (ir.Phase(0, (
            ir.Mix(dst, operator, expr(ir.Lane(src), ir.Lane(other))),)),)))
        scalar = ir.permute(loaded, lanes)[dst]
        batch = ir.permute_batch(loaded, np.array(lanes, dtype=np.uint64).reshape(8, 1))
        self.assertEqual(batch.dtype, np.uint64)
        self.assertEqual(int(batch[dst, 0]), scalar)
        return scalar

    def test_rotate(self):
        self.assertEqual(self.result(lambda a, b: ir.Rotl(a, 3)), 0xA5)

    def test_shifts_fill_with_zeros(self):
        self.assertEqual(self.result(lambda a, b: ir.Shl(a, 2)), 0xD0)
        self.assertEqual(self.result(lambda a, b: ir.Shr(a, 2)), 0x2D)

    def test_bitwise(self):
        self.assertEqual(self.result(lambda a, b: ir.Xor(a, b)), 0xBB)
        self.assertEqual(self.result(lambda a, b: ir.And(a, b)), 0x04)
        self.assertEqual(self.result(lambda a, b: ir.Or(a, b)), 0xBF)
        self.assertEqual(self.result(lambda a, b: ir.Not(a)), 0x4B)

    def test_add_and_subtract_wrap_at_the_width(self):
        self.assertEqual(self.result(lambda a, b: a, operator="add", start=0x7F), 0x33)
        self.assertEqual(self.result(lambda a, b: a, operator="sub", start=0x10), 0x5C)

    def test_xor(self):
        self.assertEqual(self.result(lambda a, b: a, operator="xor", start=0xFF), 0x4B)

    def test_a_rotation_update(self):
        lanes = [0] * 8
        lanes[0] = 0x81
        loaded = ir.load(ir.Program("rot", 2, 8, (ir.Phase(0, (ir.Rot(0, 1),)),)))
        self.assertEqual(ir.permute(loaded, lanes)[0], 0x03)

    def test_a_constant_reads_its_round(self):
        loaded = ir.load(ir.Program("const", 2, 8, (ir.Phase(0, (
            ir.Mix(0, "xor", ir.Constant(1)),)),)))
        table = [(0x00, 0x11), (0x00, 0x22)]
        self.assertEqual(ir.permute(loaded, [0] * 8, table)[0], 0x33)

    def test_every_step_is_masked_before_the_next(self):
        """Research R11: masked to w bits after every operation, not only at the end."""
        self.assertEqual(self.result(lambda a, b: ir.Shr(ir.Shl(a, 2), 2)), 0x34)
        self.assertEqual(self.result(lambda a, b: ir.Shr(ir.Not(a), 1)), 0x25)
        self.assertEqual(self.result(lambda a, b: ir.Shr(ir.Rotl(a, 3), 1)), 0x52)

    def test_w_4_masks_every_operation(self):
        loaded = ir.load(stated_list(2, 4))
        for value in states(2, 4):
            out = ir.permute(loaded, value, round_constants(2, 4, 3))
            self.assertTrue(all(0 <= word < 16 for word in out))


class Interpreters(unittest.TestCase):

    def sizes(self):
        return devinputs_v3.PAIRS

    def test_the_two_interpreters_agree_at_every_size(self):
        for n, w in self.sizes():
            loaded = ir.load(stated_list(n, w))
            table = round_constants(n, w, 4)
            values = states(n, w)
            batch = ir.permute_batch(loaded, np.array(values, dtype=np.uint64).T, table)
            for index, value in enumerate(values):
                self.assertEqual(ir.permute(loaded, value, table),
                                 [int(word) for word in batch[:, index]], (n, w))

    def test_a_phase_reads_the_values_at_its_start_which_is_list_order_here(self):
        loaded = ir.load(stated_list(4, 16))
        table = round_constants(4, 16, 3)
        for value in states(4, 16, 4):
            self.assertEqual(ir.permute(loaded, value, table),
                             self.in_list_order(loaded, value, table))

    def test_both_interpreters_read_the_values_at_the_phases_start(self):
        """On a list the loader would refuse, so that list order gives another answer."""
        lanes = [0] * 8
        lanes[0], lanes[1], lanes[2] = 0x01, 0x02, 0x04
        updates = (ir.Mix(1, "xor", ir.Lane(2)), ir.Mix(0, "xor", ir.Lane(1)))
        broken = ir.Loaded(ir.Program("unloaded", 2, 8, (ir.Phase(0, updates),)))
        self.assertEqual(ir.permute(broken, lanes)[:2], [0x03, 0x06])
        out = ir.permute_batch(broken, np.array([lanes], dtype=np.uint64).T)
        self.assertEqual([int(word) for word in out[:2, 0]], [0x03, 0x06])

    def in_list_order(self, loaded, value, table):
        state = list(value)
        mask = (1 << loaded.program.w) - 1
        for constants in table:
            for phase in loaded.program.phases:
                for update in phase.updates:
                    single_phase = ir.Program("step", loaded.program.n, loaded.program.w,
                                              (ir.Phase(phase.colour, (update,)),))
                    state = ir.permute(ir.load(single_phase), state, [constants])
        self.assertTrue(all(word <= mask for word in state))
        return state

    def test_the_input_is_left_as_it_was(self):
        loaded = ir.load(stated_list(4, 8))
        value = states(4, 8, 1)[0]
        before = list(value)
        table = round_constants(4, 8, 2)
        ir.permute(loaded, value, table)
        self.assertEqual(value, before)
        array = np.array([value], dtype=np.uint64).T
        copy = array.copy()
        ir.permute_batch(loaded, array, table)
        self.assertTrue((array == copy).all())

    def test_the_batch_takes_explicit_uint64_alone(self):
        loaded = ir.load(stated_list(2, 8))
        with self.assertRaisesRegex(ir.ListRefused, "uint64"):
            ir.permute_batch(loaded, np.zeros((8, 1), dtype=np.int64))

    def test_a_state_of_the_wrong_length_is_refused(self):
        loaded = ir.load(stated_list(2, 8))
        with self.assertRaisesRegex(ir.ListRefused, "lanes"):
            ir.permute(loaded, [0] * 7)
        with self.assertRaisesRegex(ir.ListRefused, "lanes"):
            ir.permute_batch(loaded, np.zeros((7, 1), dtype=np.uint64))

    def test_a_word_beyond_the_width_is_refused(self):
        loaded = ir.load(stated_list(2, 8))
        with self.assertRaisesRegex(ir.ListRefused, "width"):
            ir.permute(loaded, [256] + [0] * 7)
        with self.assertRaisesRegex(ir.ListRefused, "width"):
            ir.permute_batch(loaded, np.array([[256]] + [[0]] * 7, dtype=np.uint64))

    def test_an_interpreter_takes_a_loaded_list_alone(self):
        with self.assertRaises(ir.ListRefused):
            ir.permute(stated_list(2, 8), [0] * 8)
        with self.assertRaises(ir.ListRefused):
            ir.permute_batch(stated_list(2, 8), np.zeros((8, 1), dtype=np.uint64))

    def test_a_list_with_constants_needs_its_table(self):
        loaded = ir.load(stated_list(2, 8))
        with self.assertRaisesRegex(ir.ListRefused, "constant"):
            ir.permute(loaded, [0] * 8)
        with self.assertRaisesRegex(ir.ListRefused, "constant"):
            ir.permute_batch(loaded, np.zeros((8, 1), dtype=np.uint64))

    def test_a_table_that_does_not_fit_the_list_is_refused(self):
        loaded = ir.load(ir.Program("c", 2, 8, (ir.Phase(0, (
            ir.Mix(0, "xor", ir.Constant(1)),)),)))
        for table, words in (([(1,)], "column 1"), ([(1, 256)], "width"), ([(1, -1)], "width"),
                             ([(1, 2.0)], "width")):
            with self.assertRaisesRegex(ir.ListRefused, words):
                ir.permute(loaded, [0] * 8, table)
        with self.assertRaisesRegex(ir.ListRefused, "rows"):
            ir.permute(loaded, [0] * 8, [(1, 2)], rounds=2)
        ir.permute(loaded, [0] * 8, [(1, 2)], rounds=1)

    def test_rounds_is_a_positive_integer(self):
        loaded = ir.load(ir.Program("rot", 2, 8, (ir.Phase(0, (ir.Rot(0, 1),)),)))
        for rounds in (0, -1, True, 1.0):
            with self.assertRaisesRegex(ir.ListRefused, "rounds"):
                ir.permute(loaded, [0] * 8, rounds=rounds)

    def test_several_rounds_are_several_passes(self):
        loaded = ir.load(ir.Program("rot", 2, 8, (ir.Phase(0, (ir.Rot(0, 1),)),)))
        self.assertEqual(ir.permute(loaded, [1] + [0] * 7, rounds=3)[0], 8)


class Inverse(unittest.TestCase):

    def test_the_inverse_undoes_the_permutation_at_every_size(self):
        for n, w in devinputs_v3.PAIRS:
            loaded = ir.load(stated_list(n, w))
            table = round_constants(n, w, 4)
            for value in states(n, w, 6):
                forward = ir.permute(loaded, value, table)
                self.assertNotEqual(forward, value)
                self.assertEqual(ir.permute_inverse(loaded, forward, table), value, (n, w))
                self.assertEqual(ir.permute(loaded, ir.permute_inverse(loaded, value, table), table),
                                 value, (n, w))

    def test_the_batch_inverse_agrees(self):
        loaded = ir.load(stated_list(4, 32))
        table = round_constants(4, 32, 5)
        values = np.array(states(4, 32), dtype=np.uint64).T
        forward = ir.permute_batch(loaded, values, table)
        self.assertTrue((ir.permute_batch_inverse(loaded, forward, table) == values).all())

    def test_the_inverse_is_derived_phase_by_phase(self):
        p, v = ir.lane(4, 0, 0, P), ir.lane(4, 0, 0, V)
        east = ir.Lane(ir.lane(4, 0, 1, P))
        program = ir.Program("list", 4, 8, (
            ir.Phase(0, (ir.Mix(p, "add", east), ir.Mix(v, "sub", east))),
            ir.Phase(0, (ir.Mix(p, "xor", east), ir.Rot(v, 3)))))
        inverse = ir.invert(program)
        self.assertEqual(inverse.phases[0].updates, (ir.Mix(p, "xor", east), ir.Rot(v, 5)))
        self.assertEqual(inverse.phases[1].updates, (ir.Mix(p, "sub", east), ir.Mix(v, "add", east)))

    def test_the_inverse_of_the_inverse_is_the_list(self):
        program = stated_list(4, 16)
        self.assertEqual(ir.invert(ir.invert(program)), program)

    def test_the_inverse_passes_the_loader(self):
        for n, w in devinputs_v3.PAIRS:
            ir.load(ir.invert(stated_list(n, w)))

    def test_constants_are_read_in_reverse(self):
        loaded = ir.load(ir.Program("c", 2, 8, (
            ir.Phase(0, (ir.Mix(0, "add", ir.Constant(0)),)), ir.Phase(0, (ir.Rot(0, 1),)))))
        table = [(3,), (5,)]
        forward = ir.permute(loaded, [7] + [0] * 7, table)
        self.assertEqual(ir.permute_inverse(loaded, forward, table)[0], 7)


class Candidates(unittest.TestCase):
    """Every list under research/004/candidates/ at every size, as the directory fills (FR-019)."""

    def test_the_rule_holds_on_every_candidate_at_every_size(self):
        modules = ir.candidate_modules()
        names = sorted(path.stem for path in CANDIDATES.glob("cand-*.py"))
        self.assertEqual(sorted(modules), names)
        for name, build in modules.items():
            self.assertEqual(len(ir.check_every_size(build)), len(devinputs_v3.PAIRS), name)

    def test_a_candidate_module_is_read_from_its_build_function(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cand-X9.py"
            path.write_text("def build(n, w):\n    return None\n", encoding="utf-8")
            modules = ir.candidate_modules(Path(tmp))
            self.assertEqual(list(modules), ["cand-X9"])
            self.assertIsNone(modules["cand-X9"](2, 8))

    def test_a_module_with_no_build_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "cand-X9.py").write_text("x = 1\n", encoding="utf-8")
            with self.assertRaisesRegex(ir.ListRefused, "build"):
                ir.candidate_modules(Path(tmp))


class TheModule(unittest.TestCase):

    def test_the_candidate_log_takes_the_modules_sha256(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cand-X9.py"
            path.write_bytes(b"def build(n, w):\n    pass\n")
            self.assertEqual(ir.oplist_sha256(path), hashlib.sha256(path.read_bytes()).hexdigest())

    def test_the_model_never_imports_it(self):
        for path in sorted((ROOT / "phycoweb").rglob("*.py")):
            tree = ast.parse(path.read_bytes().decode("utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                for name in names:
                    self.assertNotIn("research", name, path.name)
                    self.assertNotEqual(name.split(".")[-1], "ir", path.name)

    def test_two_forms_with_the_same_fields_are_never_equal(self):
        """So that an inverse compared with its list cannot pass on the wrong operation."""
        self.assertNotEqual(ir.Xor(ir.Lane(0), ir.Lane(1)), ir.And(ir.Lane(0), ir.Lane(1)))
        self.assertNotEqual(ir.Shl(ir.Lane(0), 1), ir.Shr(ir.Lane(0), 1))
        self.assertNotEqual(ir.Lane(0), ir.Constant(0))


if __name__ == "__main__":
    unittest.main()
