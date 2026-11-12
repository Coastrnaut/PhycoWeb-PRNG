"""Feature 004: the operation-count cost model (research R5; spec FR-022, FR-026; T073).

Every count here is worked by hand from R5's table, and the two files of known results under
research/004/validation/ are reproduced exactly. The implied throughput stands beside the goal of
10⁸ words per second and decides nothing. This file makes no security claim.
"""
import importlib.util
import sys
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for place in (str(ROOT / "research/004"), str(ROOT / "research/004/tools")):
    if place not in sys.path:
        sys.path.insert(0, place)

import costmodel  # noqa: E402
import ir  # noqa: E402

from protocol.evidence import Refused  # noqa: E402

from tests.support_004 import pin_feature_004  # noqa: E402

setUpModule, tearDownModule = pin_feature_004()

N, W = 4, 32
P, V = ir.PRESSURE, ir.VEIN


def known(name):
    path = ROOT / "research/004/validation" / f"{name}.py"
    spec = importlib.util.spec_from_file_location("known_" + name.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def word(i, j, kind, n=N):
    return ir.Lane(ir.lane(n, i, j, kind))


def each_class(update, n=N):
    return tuple(ir.Phase(colour, tuple(update(i, j) for i, j in ir.nodes_of(n, colour)))
                 for colour in range(ir.colours(n)))


def counted(phases, rounds=32, rate=640, n=N, w=W):
    return costmodel.count(ir.load(ir.Program("stated", n, w, phases)), rounds, rate)


def on_pressure(expr):
    """`expr(i, j)` XORed into the pressure lane of every node, one phase per class."""
    return each_class(lambda i, j: ir.Mix(ir.lane(N, i, j, P), "xor", expr(i, j)))


def on_vein(op, expr):
    return each_class(lambda i, j: ir.Mix(ir.lane(N, i, j, V), op, expr(i, j)))


def fold(first, *others):
    for other in others:
        first = ir.Xor(first, other)
    return first


def rotations_of(i, j, count):
    return fold(word(i, j, V), *(ir.Rotl(word(i, j, V), t) for t in range(1, count)))


class KnownResults(unittest.TestCase):
    """R5's hand-counted examples, entered in the provenance log before this tool was drafted."""

    def check(self, want, found):
        for name in ("luts", "chains", "phases", "flip_flops", "cost"):
            self.assertEqual(found[name], want[name], name)
        self.assertEqual(tuple(found["depth"]), tuple(want["depth"]))

    def test_the_first_file_reproduces_exactly(self):
        m = known("costmodel-examples")
        for label, builder, want in m.EXAMPLES:
            with self.subTest(label):
                self.check(want, costmodel.count(ir.load(m.build(label, builder)), m.R, m.RATE))

    def test_the_second_file_reproduces_exactly(self):
        m = known("costmodel-examples-second")
        for label, builder, want in m.EXAMPLES:
            with self.subTest(label):
                loaded = ir.load(m.build(label, builder, want["n"], want["w"]))
                self.check(want, costmodel.count(loaded, want["rounds"], want["rate"]))

    def test_validation_refinds_both_files(self):
        for name in ("costmodel-examples", "costmodel-examples-second"):
            result = costmodel.validation(name, known(name), None)
            self.assertTrue(result["re_found"], name)
            self.assertEqual(result["validated_kind"], costmodel.KIND)

    def test_validation_fails_on_a_wrong_expectation(self):
        module = known("costmodel-examples")
        label, builder, want = module.EXAMPLES[1]
        module.EXAMPLES = ((label, builder, dict(want, luts=want["luts"] + 1)),)
        result = costmodel.validation("costmodel-examples", module, None)
        self.assertFalse(result["re_found"])


class TheTable(unittest.TestCase):

    def test_rotations_cost_nothing(self):
        found = counted(each_class(lambda i, j: ir.Rot(ir.lane(N, i, j, P), 7)))
        self.assertEqual((found["luts"], found["chains"], found["depth"]), (0, 0, [0, 0]))

    def test_wiring_into_an_addition_adds_nothing_to_it(self):
        """A rotated or shifted word, or a neighbour's, reaches the adder through wires alone."""
        for expr in (lambda i, j: ir.Rotl(word(i, j, P), 9), lambda i, j: ir.Shr(word(i, j, P), 3),
                     lambda i, j: ir.Shl(word(i, j, P), 3), lambda i, j: word(i, j + 1, P)):
            self.assertEqual(counted(on_vein("add", expr))["luts"], W)

    def test_a_bitwise_function_of_up_to_six_inputs_takes_one_lut_per_bit(self):
        for count, lanes in ((1, 2), (5, 6)):
            found = counted(on_pressure(lambda i, j: rotations_of(i, j, count)))
            self.assertEqual((found["luts"], found["depth"]), (W, [1, 1]), lanes)

    def test_the_bound_of_six_and_each_step_above_it(self):
        """w·⌈(k - 1)/5⌉: k = 7 and 11 take 2w, and k = 12 and 16 take 3w; the update's own pressure
        lane is one of the k, so that `count` rotations of V give k = count + 1."""
        for k, width in ((7, 2), (11, 2), (12, 3), (16, 3), (17, 4)):
            found = counted(on_pressure(lambda i, j: rotations_of(i, j, k - 1)))
            self.assertEqual((found["luts"], found["depth"]), (width * W, [width, width]), k)

    def test_a_constants_bits_count_as_inputs(self):
        """Pressure, five rotations of V and one constant: k = 7, where k = 6 fits one LUT."""
        found = counted(on_pressure(lambda i, j: fold(rotations_of(i, j, 5), ir.Constant(0))))
        self.assertEqual(found["luts"], 2 * W)

    def test_an_input_bit_counts_once(self):
        """V and V again are one input bit per output bit, so k = 2."""
        found = counted(on_pressure(lambda i, j: ir.Xor(word(i, j, V), word(i, j, V))))
        self.assertEqual(found["luts"], W)

    def test_k_is_the_largest_over_the_output_bits(self):
        """Shifts leave some output bits with fewer inputs: V >> 3 and V << 5 reach bit 10 both,
        bit 0 only the first and bit 31 only the second, and k is 3, from the middle bits."""
        expr = lambda i, j: ir.Xor(ir.Shr(word(i, j, V), 3), ir.Shl(word(i, j, V), 5))  # noqa: E731
        self.assertEqual(costmodel.fan_in(expr(0, 0), W), 2)
        self.assertEqual(counted(on_pressure(expr))["luts"], W)

    def test_a_shift_past_the_output_bit_reads_nothing_there(self):
        self.assertEqual(costmodel.input_bits(ir.Shr(word(0, 0, V), 3), 31, W), set())
        self.assertEqual(costmodel.input_bits(ir.Shl(word(0, 0, V), 3), 0, W), set())

    def test_a_rotation_wraps_in_the_bits_it_reads(self):
        lane = ir.lane(N, 0, 0, V)
        self.assertEqual(costmodel.input_bits(ir.Rotl(ir.Lane(lane), 3), 0, W), {("lane", lane, 29)})
        self.assertEqual(costmodel.input_bits(ir.Rotl(ir.Lane(lane), 3), 5, W), {("lane", lane, 2)})

    def test_addition_and_subtraction_take_w_and_one_chain(self):
        for op in ("add", "sub"):
            found = counted(on_vein(op, lambda i, j: word(i, j, P)))
            self.assertEqual((found["luts"], found["chains"], found["depth"]), (W, 1, [1, 1]), op)

    def test_a_function_before_an_addition_counts_apart_from_it(self):
        """V add (P xor P(east)): w for the function, w for the addition, two levels."""
        found = counted(on_vein("add", lambda i, j: ir.Xor(word(i, j, P), word(i, j + 1, P))))
        self.assertEqual((found["luts"], found["depth"]), (2 * W, [2, 2]))

    def test_a_not_before_an_addition_is_a_function_and_not_a_wire(self):
        found = counted(on_vein("add", lambda i, j: ir.Not(word(i, j, P))))
        self.assertEqual((found["luts"], found["depth"]), (2 * W, [2, 2]))

    def test_no_fusion_between_listed_operations(self):
        """Two updates of a lane, each of k = 2, take 2w, though one 3-input LUT could hold both."""
        first = on_pressure(lambda i, j: ir.Rotl(word(i, j, V), 1))
        second = on_pressure(lambda i, j: ir.Rotl(word(i, j, V), 2))
        self.assertEqual(counted(first + second)["luts"], 2 * W)

    def test_an_update_counts_once_at_the_node_that_computes_it(self):
        """Three updates among 16 nodes: 3w/16 per node and round."""
        phases = (ir.Phase(0, (ir.Mix(ir.lane(N, 0, 0, P), "xor", word(0, 1, V)),)),
                  ir.Phase(1, (ir.Mix(ir.lane(N, 0, 1, P), "xor", word(0, 0, V)),
                               ir.Mix(ir.lane(N, 1, 2, P), "xor", word(1, 1, V)))))
        self.assertEqual(counted(phases)["luts"], Fraction(3 * W, 16))


class CarryChains(unittest.TestCase):

    def test_parallel_additions_are_one_chain(self):
        self.assertEqual(counted(on_vein("add", lambda i, j: word(i, j, P)))["chains"], 1)

    def test_a_path_through_two_additions_counts_two(self):
        phases = (ir.Phase(0, tuple(ir.Mix(ir.lane(N, i, j, V), "add", word(i, j, P))
                                    for i, j in ir.nodes_of(N, 0))),
                  ir.Phase(1, tuple(ir.Mix(ir.lane(N, i, j, V), "add", word(i, j + 1, V))
                                    for i, j in ir.nodes_of(N, 1))))
        found = counted(phases)
        self.assertEqual(found["chains"], 2)
        self.assertEqual(found["chains_per_phase"], [1, 1], "each stage holds one")

    def test_a_rotation_keeps_a_lanes_additions(self):
        """Add into V, rotate V in a later phase, then read it in an addition: two on one path."""
        i, j, near = 0, 0, (0, 1)
        phases = (ir.Phase(0, (ir.Mix(ir.lane(N, i, j, V), "add", word(i, j, P)),)),
                  ir.Phase(0, (ir.Rot(ir.lane(N, i, j, V), 5),)),
                  ir.Phase(1, (ir.Mix(ir.lane(N, *near, V), "add", word(i, j, V)),)))
        self.assertEqual(counted(phases)["chains"], 2)

    def test_a_bitwise_update_passes_a_path_on(self):
        """An XOR adds no chain, but what it reads stays on the path it writes."""
        i, j, near = 0, 0, (0, 1)
        phases = (ir.Phase(0, (ir.Mix(ir.lane(N, i, j, V), "add", word(i, j, P)),)),
                  ir.Phase(0, (ir.Mix(ir.lane(N, i, j, P), "xor", word(i, j, V)),)),
                  ir.Phase(1, (ir.Mix(ir.lane(N, *near, V), "add", word(i, j, P)),)))
        self.assertEqual(counted(phases)["chains"], 2)

    def test_a_lane_no_path_reaches_stays_at_zero(self):
        found = counted(on_pressure(lambda i, j: word(i, j, V)))
        self.assertEqual((found["chains"], found["chains_per_phase"]), (0, [0, 0]))


class Reported(unittest.TestCase):

    def test_flip_flops_are_two_words_per_node(self):
        self.assertEqual(counted(on_pressure(lambda i, j: word(i, j, V)))["flip_flops"], 2 * W)

    def test_cost_per_output_bit_is_exact(self):
        """L = 32, n² = 16, P = 2, R = 32, r = 640: 32 · 16 · 2 · 32 / 640 = 51.2 LUT-cycles."""
        found = counted(on_pressure(lambda i, j: word(i, j, V)))
        self.assertEqual(found["cost"], Fraction(256, 5))

    def test_a_list_the_loader_did_not_pass_is_refused(self):
        program = ir.Program("stated", N, W, on_pressure(lambda i, j: word(i, j, V)))
        with self.assertRaises(Refused):
            costmodel.count(program, 32, 640)

    def test_a_round_count_or_rate_that_is_no_positive_integer_is_refused(self):
        loaded = ir.load(ir.Program("stated", N, W, on_pressure(lambda i, j: word(i, j, V))))
        for rounds, rate in ((0, 640), (32, 0), (1.5, 640), (32, -640)):
            with self.assertRaises(Refused):
                costmodel.count(loaded, rounds, rate)

    def test_the_figures_a_record_holds_are_plain_json(self):
        fields = costmodel.record_fields(counted(on_pressure(lambda i, j: word(i, j, V))))
        self.assertEqual((fields["luts"], fields["cost"]), ("32", "256/5"))


class Throughput(unittest.TestCase):
    """R5's worked rate at 4×4: at i = 32 and t_s = t_o = 0, 640 bits per 84 cycles at R = 32 and per
    148 at R = 64, about 0.48 and 0.27 × 10⁸ words per second, both below the goal."""

    def test_the_cycles_of_a_call(self):
        self.assertEqual(costmodel.call_cycles(640, 2, 32, 32), 84)
        self.assertEqual(costmodel.call_cycles(640, 2, 64, 32), 148)
        self.assertEqual(costmodel.call_cycles(640, 2, 32, 32, 3, 5), 92)
        self.assertEqual(costmodel.call_cycles(640, 2, 32, 33), 64 + 20, "⌈640/33⌉ = 20")
        self.assertEqual(costmodel.call_cycles(640, 2, 32, 64), 64 + 10)

    def test_the_rate_reads_rs_cycles(self):
        self.assertEqual(costmodel.rate_per_call(640, 2, 32, 32), Fraction(640, 84))

    def test_r5s_two_rates(self):
        for rounds, cycles in ((32, 84), (64, 148)):
            rate = costmodel.rate_per_call(640, 2, rounds, 32)
            self.assertEqual(rate, Fraction(640, cycles))
        self.assertEqual(round(float(costmodel.words_per_second(Fraction(640, 84))) / 1e6, 1), 47.6)
        self.assertEqual(round(float(costmodel.words_per_second(Fraction(640, 148))) / 1e6, 1), 27.0)

    def test_a_request_counts_its_calls_its_forget_and_its_clearing(self):
        """2¹⁹ bits at r = 640: 820 calls of 64 cycles, 16,384 words out, one forget call of 64 and
        no tree: 52,480 + 16,384 + 64 = 68,928 cycles, then 7 of clearing and 100 of instantiate."""
        self.assertEqual(costmodel.request_cycles(2 ** 19, 640, 2, 32, 32), 68928)
        self.assertEqual(costmodel.request_cycles(2 ** 19, 640, 2, 32, 32, clearing=7,
                                                  instantiate_share=Fraction(100)), 69035)

    def test_each_call_of_a_request_takes_the_trees(self):
        """Two bits, one output call and a forget: (64 + 3 + 5) + ⌈2/32⌉ + (64 + 3) = 140."""
        self.assertEqual(costmodel.request_cycles(2, 640, 2, 32, 32, 3, 5), 140)

    def test_a_block_boundary_takes_no_extra_call(self):
        self.assertEqual(costmodel.request_cycles(640, 640, 2, 32, 32), 64 + 20 + 64)
        self.assertEqual(costmodel.request_cycles(641, 640, 2, 32, 32), 2 * 64 + 21 + 64)

    def test_the_goal_stands_beside_the_figures_and_decides_nothing(self):
        found = costmodel.throughput(640, 2, 32, 32, 2 ** 19)
        self.assertEqual(found["throughput_goal"], 10 ** 8)
        self.assertEqual(found["rate_before_forget"], str(costmodel.words_per_second(
            Fraction(640, 84))))
        self.assertEqual(found["bits_per_cycle_before_forget"], "160/21")
        self.assertEqual(found["interface_bits_per_cycle"], 32)
        self.assertEqual(found["throughput_implied"], str(costmodel.words_per_second(
            Fraction(2 ** 19, 68928))))
        self.assertNotIn("meets_goal", found)


if __name__ == "__main__":
    unittest.main()
