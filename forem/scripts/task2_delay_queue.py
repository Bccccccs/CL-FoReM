#!/usr/bin/env python3
"""Pure fixed-delay FIFO queue for whole JointTrajectory commands (task2.2). stdlib only: no ROS, no numpy, no sleep, no wall clock.

All times are integer nanoseconds of SIMULATION time handed in by the caller. The queue never reads any clock itself, so it cannot be
driven by the host wall clock: it releases an entry only when the caller's `advance(now_ns)` has `now_ns >= recv_ns + delay_ns`.

Contract (exp2.1 section 2):
  * entries are identified by (epoch, seq); epoch must equal the queue epoch, seq is strictly increasing inside an epoch
  * release order is (t_due, seq), FIFO; capacity is hard: a full queue raises QueueError, nothing is dropped silently
  * invalid arguments (non-int / bool / negative / overflowing times, bad delay or capacity) raise QueueError with a reject event
  * the simulation clock going backwards (advance or enqueue time below the last one seen) empties the queue, bumps the epoch and
    reports every discarded entry; an explicit reset(new_epoch, now) does the same without needing a backward step
  * every operation returns structured events; the caller adds run-id / publish times and writes them out

Also holds `validate_command`, the supported-message check of the proxy (exp2.1 section 1): a plain-dict command record in the task1-command/1
layout is accepted only if it is the frozen header.stamp=0 two-point trajectory; anything else is rejected, never rewritten.
"""
import hashlib
import json
import math

INT_MAX = 2 ** 62     # far beyond any simulated time in ns, keeps arithmetic exact


class QueueError(Exception):
    """Fatal queue misuse. `.event` is the reject event describing it; the run must be treated as invalid."""

    def __init__(self, message, event=None):
        super().__init__(message)
        self.event = event or {"type": "reject", "reason": message}


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _check_ns(name, x):
    if not _is_int(x) or x < 0 or x > INT_MAX:
        raise QueueError("%s must be an int in [0, 2^62], got %r" % (name, x), {"type": "reject", "reason": "invalid %s: %r" % (name, x)})


class Item:
    __slots__ = ("epoch", "seq", "recv_ns", "due_ns", "payload", "payload_hash")

    def __init__(self, epoch, seq, recv_ns, due_ns, payload, payload_hash):
        self.epoch, self.seq, self.recv_ns, self.due_ns, self.payload, self.payload_hash = epoch, seq, recv_ns, due_ns, payload, payload_hash

    def key(self):
        return (self.due_ns, self.seq)


class DelayQueue:
    def __init__(self, delay_ns, capacity=64, epoch=0):
        if not _is_int(delay_ns) or delay_ns < 0 or delay_ns > INT_MAX:
            raise QueueError("delay_ns must be a non-negative int, got %r" % (delay_ns,))
        if not _is_int(capacity) or capacity < 1:
            raise QueueError("capacity must be a positive int, got %r" % (capacity,))
        if not _is_int(epoch) or epoch < 0:
            raise QueueError("epoch must be a non-negative int, got %r" % (epoch,))
        self.delay_ns = delay_ns
        self.capacity = capacity
        self.epoch = epoch
        self._items = []
        self._last_seq = None
        self._last_now = None
        self.clock_backward_count = 0
        self.delivered = 0

    # ------------------------------------------------------------------ helpers
    def __len__(self):
        return len(self._items)

    def pending(self):
        return [(i.epoch, i.seq, i.due_ns) for i in self._items]

    def _ev(self, typ, item=None, reason=None, **kw):
        e = {"type": typ, "epoch": self.epoch, "queue_len": len(self._items), "delay_ns": self.delay_ns}
        if item is not None:
            e.update(seq=item.seq, t_in_ns=item.recv_ns, t_due_ns=item.due_ns, payload_hash=item.payload_hash)
        if reason is not None:
            e["reason"] = reason
        e.update(kw)
        return e

    def _clear(self, reason, now_ns):
        events = [self._ev("drop", it, reason=reason, t_now_ns=now_ns) for it in self._items]
        self._items = []
        for e in events:
            e["queue_len"] = 0
        return events

    def _backward(self, now_ns):
        """Clock went below the last time seen: pending entries are discarded and the epoch changes."""
        ev = self._clear("clock_backward", now_ns)
        old = self.epoch
        self.epoch += 1
        self._last_seq = None
        self.clock_backward_count += 1
        ev.append(self._ev("clock_backward", reason="now %d < last %d; epoch %d -> %d" % (now_ns, self._last_now, old, self.epoch), t_now_ns=now_ns, old_epoch=old))
        self._last_now = now_ns
        return ev

    # ------------------------------------------------------------------ API
    def enqueue(self, epoch, seq, recv_ns, payload, payload_hash=None):
        """Add one entry. Returns the list of events (an `enqueue` event, preceded by clock-backward events if the time went back).
        Raises QueueError (with `.event`) for an unknown epoch, a non-increasing / duplicate seq, invalid numbers or a full queue."""
        for name, v in (("epoch", epoch), ("seq", seq), ("recv_ns", recv_ns)):
            _check_ns(name, v)
        events = []
        if self._last_now is not None and recv_ns < self._last_now:
            events += self._backward(recv_ns)
        if epoch != self.epoch:
            raise QueueError("unknown epoch %d (queue epoch %d)" % (epoch, self.epoch),
                             self._ev("reject", reason="unknown epoch %d (queue epoch %d)" % (epoch, self.epoch), seq=seq, t_in_ns=recv_ns, rejected_events_before=events))
        if self._last_seq is not None and seq <= self._last_seq:
            raise QueueError("seq %d not above last seq %d" % (seq, self._last_seq),
                             self._ev("reject", reason="duplicate or non-increasing seq %d (last %d)" % (seq, self._last_seq), seq=seq, t_in_ns=recv_ns, rejected_events_before=events))
        if len(self._items) >= self.capacity:
            raise QueueError("queue full (%d)" % self.capacity,
                             self._ev("reject", reason="queue full (capacity %d)" % self.capacity, seq=seq, t_in_ns=recv_ns, rejected_events_before=events))
        it = Item(epoch, seq, recv_ns, recv_ns + self.delay_ns, payload, payload_hash)
        self._items.append(it)
        self._items.sort(key=Item.key)
        self._last_seq = seq
        self._last_now = recv_ns if self._last_now is None else max(self._last_now, recv_ns)
        events.append(self._ev("enqueue", it))
        return events

    def advance(self, now_ns):
        """Release every entry with due_ns <= now_ns, in (t_due, seq) order. Returns (items, events). A repeated or later call never
        re-delivers. A now_ns below the last one seen clears the queue (clock backward) and delivers nothing."""
        _check_ns("now_ns", now_ns)
        if self._last_now is not None and now_ns < self._last_now:
            return [], self._backward(now_ns)
        self._last_now = now_ns
        due = [it for it in self._items if it.due_ns <= now_ns]
        self._items = [it for it in self._items if it.due_ns > now_ns]
        self.delivered += len(due)
        events = [self._ev("due", it, t_now_ns=now_ns) for it in due]
        return due, events

    def reset(self, new_epoch, now_ns):
        """Explicit reset: discard every pending entry (each reported), switch to `new_epoch` (must be above the current one)."""
        _check_ns("now_ns", now_ns)
        _check_ns("new_epoch", new_epoch)
        if new_epoch <= self.epoch:
            raise QueueError("new epoch %d must exceed current epoch %d" % (new_epoch, self.epoch),
                             self._ev("reject", reason="reset to non-increasing epoch %d" % new_epoch))
        events = self._clear("reset", now_ns)
        old = self.epoch
        self.epoch = new_epoch
        self._last_seq = None
        self._last_now = now_ns
        events.append(self._ev("reset", reason="explicit reset", t_now_ns=now_ns, old_epoch=old))
        return events

    def discard(self, reason, now_ns=None):
        """Discard every pending entry (each reported with `reason`); the epoch is unchanged."""
        return self._clear(reason, now_ns)

    def shutdown(self, now_ns=None):
        """Discard everything without publishing (stop semantics: never drain on shutdown)."""
        events = self._clear("shutdown", now_ns)
        events.append(self._ev("shutdown", reason="queue closed", t_now_ns=now_ns))
        return events


# ---------------------------------------------------------------------------------------------------------------
# supported-message check (proxy first version): the frozen two-point header.stamp=0 trajectory only
def payload_hash(record):
    """sha256 of the canonical JSON of a task1-command/1 record. An integrity check only, never an identity."""
    return hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_command(record, joints, limits, max_speed_fraction, frame_id=""):
    """Return a list of problems (empty = the frozen supported message). `record` is a task1-command/1 dict
    (header.stamp [s, ns], frame_id, joint_names, points[{positions, velocities, accelerations, effort, time_from_start [s, ns]}]).
    limits: joint -> {lower, upper, velocity}. The record is never modified."""
    bad = []
    try:
        if record.get("header", {}).get("stamp") != [0, 0]:
            bad.append("header.stamp must be 0 (the controller starts the trajectory on receipt); got %s" % (record.get("header", {}).get("stamp"),))
        if record["header"]["frame_id"] != frame_id:
            bad.append("header.frame_id %r != frozen %r" % (record["header"]["frame_id"], frame_id))
        if list(record["joint_names"]) != list(joints):
            bad.append("joint_names %s != frozen %s" % (record["joint_names"], list(joints)))
        pts = record["points"]
        if len(pts) != 2:
            bad.append("expected exactly 2 points, got %d" % len(pts))
            return bad
        n = len(joints)
        for i, p in enumerate(pts):
            if len(p["positions"]) != n:
                bad.append("point %d: %d positions" % (i, len(p["positions"])))
            if len(p["velocities"]) != n or any(v != 0.0 for v in p["velocities"]):
                bad.append("point %d: velocities must be %d zeros" % (i, n))
            if p["accelerations"] or p["effort"]:
                bad.append("point %d: accelerations/effort must be empty" % i)
            for name in ("positions", "velocities"):
                if any(not math.isfinite(x) for x in p[name]):
                    bad.append("point %d: non-finite %s" % (i, name))
            for x in p["time_from_start"]:
                if not _is_int(x) or x < 0:
                    bad.append("point %d: bad time_from_start %s" % (i, p["time_from_start"]))
        if pts[0]["time_from_start"] != [0, 0]:
            bad.append("first point time_from_start must be 0, got %s" % (pts[0]["time_from_start"],))
        T = pts[1]["time_from_start"][0] + pts[1]["time_from_start"][1] * 1e-9
        if not T > 0:
            bad.append("duration T must be > 0, got %r" % T)
        if not bad:
            for j, a, b in zip(joints, pts[0]["positions"], pts[1]["positions"]):
                lim = limits[j]
                if not (lim["lower"] <= a <= lim["upper"] and lim["lower"] <= b <= lim["upper"]):
                    bad.append("%s outside URDF position limits" % j)
                if 1.5 * abs(b - a) / T > max_speed_fraction * lim["velocity"] + 1e-12:
                    bad.append("%s peak speed %.4f exceeds %.2f x URDF velocity limit" % (j, 1.5 * abs(b - a) / T, max_speed_fraction))
    except (KeyError, TypeError, AttributeError) as e:
        bad.append("malformed command record: %r" % (e,))
    return bad
