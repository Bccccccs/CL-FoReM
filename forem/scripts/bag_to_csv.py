#!/usr/bin/env python3
"""Convert a hf.bag recorded by run_task0_smoke.sh --bag into CSVs (runs in forem-dev).

Writes hf_joint_states.csv, hf_controller_state.csv, hf_clock.csv next to the bag, using the
same column layout as check_feedback.py (t = message header stamp / clock, simulated seconds).
No filtering, resampling or dropping: every recorded message becomes a row.
"""
import argparse
import csv
import os

import rosbag

JOINTS = ["ur5_shoulder_pan_joint", "ur5_shoulder_lift_joint", "ur5_elbow_joint",
          "ur5_wrist_1_joint", "ur5_wrist_2_joint", "ur5_wrist_3_joint"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bag", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    js, st, ck = [], [], []
    with rosbag.Bag(a.bag) as bag:
        for topic, m, _ in bag.read_messages():
            if topic == "/joint_states":
                idx = {n: i for i, n in enumerate(m.name)}
                if all(j in idx for j in JOINTS):
                    js.append([m.header.stamp.to_sec()] + [m.position[idx[j]] for j in JOINTS] +
                              [m.velocity[idx[j]] for j in JOINTS] + [m.effort[idx[j]] for j in JOINTS])
            elif topic == "/eff_joint_traj_controller/state":
                st.append([m.header.stamp.to_sec()] + list(m.desired.positions) + list(m.actual.positions) +
                          list(m.error.positions) + list(m.desired.velocities) + list(m.actual.velocities))
            elif topic == "/clock":
                ck.append([m.clock.to_sec()])

    def write(name, header, rows):
        with open(os.path.join(a.out, name), "w", newline="") as f:
            w = csv.writer(f); w.writerow(header); w.writerows(rows)

    write("hf_joint_states.csv", ["t"] + ["pos_" + j for j in JOINTS] + ["vel_" + j for j in JOINTS] + ["eff_" + j for j in JOINTS], js)
    write("hf_controller_state.csv", ["t"] + ["des_" + j for j in JOINTS] + ["act_" + j for j in JOINTS] +
          ["err_" + j for j in JOINTS] + ["desvel_" + j for j in JOINTS] + ["actvel_" + j for j in JOINTS], st)
    write("hf_clock.csv", ["t"], ck)
    print("bag_to_csv: joint_states=%d controller_state=%d clock=%d" % (len(js), len(st), len(ck)))


if __name__ == "__main__":
    main()
