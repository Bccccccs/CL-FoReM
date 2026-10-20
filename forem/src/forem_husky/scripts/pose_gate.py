"""Pure-python acceptance logic of the pose bridge (no ROS import, unit-testable on the host).

A sample is (frame_id, child_frame_id, stamp_ns, position[3], quaternion[4]). `PoseGate.check` returns
('accept', False) or ('reject', reason) and keeps the counters/state.

Reset handling (T3-A02). A simulation reset is NEVER inferred from the sample stamps: a delayed/old sample (10 s -> 8 s without a reset)
looks exactly like a reset to a stamp-only rule, and after a real reset queued old-epoch samples (10.02 s) interleave with new ones
(0.12 s). The authority is an INDEPENDENT simulation clock: the bridge feeds the /clock topic to `observe_clock`. A /clock rewind of more
than `reset_jump_ns` is the lifecycle event "simulation reset": the epoch counter is incremented once per event and the gate HALTS --
/gazebo/reset_simulation is not a supported operation for the Task3 core, so after the event nothing is published (every later sample is
rejected as 'halted', old-epoch and new alike) and the simulation + bridge must be restarted. Samples are otherwise accepted only if their
stamp is strictly increasing and not ahead of the simulation clock (+`future_tol_ns`), i.e. old/late samples are rejected, the original stamp
is never changed.
"""
import math

REASONS = ("nonfinite", "quat", "frame", "child", "stamp_zero", "backdated", "future", "halted", "no_clock")


class PoseGate:
    def __init__(self, expected_frames=("world", "map", "odom"), child_frame="base_footprint",
                 reset_jump_ns=1_000_000_000, quat_tol=0.05, future_tol_ns=1_000_000_000):
        self.expected_frames = set(expected_frames)
        self.child_frame = child_frame
        self.reset_jump_ns = int(reset_jump_ns)      # a /clock rewind larger than this is a simulation reset
        self.future_tol_ns = int(future_tol_ns)      # how far a sample stamp may lead the latest /clock value (transport skew)
        self.quat_tol = quat_tol
        self.last_stamp_ns = None
        self.clock_ns = None
        self.epoch = 0
        self.halted = False
        self.halt_reason = None
        self.counts = {"received": 0, "accepted": 0, "duplicate": 0, **{f"rejected_{r}": 0 for r in REASONS}}

    def observe_clock(self, clock_ns):
        """Feed the independent simulation clock (/clock). Returns 'reset' on a detected reset event (epoch incremented, gate halted),
        'ok' otherwise. A clock that merely stalls or jumps forward is not a reset; a small rewind (<= reset_jump_ns) is ignored here and
        its effect is covered by the strictly-increasing stamp rule."""
        clock_ns = int(clock_ns)
        event = "ok"
        if self.clock_ns is not None and clock_ns < self.clock_ns - self.reset_jump_ns:
            self.epoch += 1
            self.halted = True
            self.halt_reason = "simulation clock reset: %.3f s -> %.3f s (epoch %d)" % (self.clock_ns * 1e-9, clock_ns * 1e-9, self.epoch)
            event = "reset"
        if self.clock_ns is None or clock_ns >= self.clock_ns or event == "reset":
            self.clock_ns = clock_ns
        return event

    def check(self, frame_id, child_frame_id, stamp_ns, position, quaternion):
        self.counts["received"] += 1
        vals = list(position) + list(quaternion)
        if not all(math.isfinite(v) for v in vals):
            return self._rej("nonfinite")
        norm = math.sqrt(sum(v * v for v in quaternion))
        if abs(norm - 1.0) > self.quat_tol:
            return self._rej("quat")
        if frame_id not in self.expected_frames:
            return self._rej("frame")
        if child_frame_id and child_frame_id.lstrip("/") != self.child_frame:
            return self._rej("child")
        if stamp_ns == 0:
            return self._rej("stamp_zero")
        if self.halted:
            return self._rej("halted")
        if self.clock_ns is None:
            return self._rej("no_clock")
        if stamp_ns > self.clock_ns + self.future_tol_ns:
            return self._rej("future")               # ahead of the simulation clock: not from this simulation epoch
        if self.last_stamp_ns is not None:
            if stamp_ns == self.last_stamp_ns:
                self.counts["duplicate"] += 1
                return ("reject", "duplicate")
            if stamp_ns < self.last_stamp_ns:
                return self._rej("backdated")        # late/old sample, regardless of how far back; never a reset by itself
        self.last_stamp_ns = stamp_ns
        self.counts["accepted"] += 1
        return ("accept", False)

    def _rej(self, reason):
        self.counts[f"rejected_{reason}"] += 1
        return ("reject", reason)
