#!/usr/bin/env python3
"""Convert a Task1 rosbag to raw CSVs (runs in forem-dev; needs rosbag).

Every message becomes a row; nothing is filtered, resampled or de-duplicated. Joints are mapped by NAME;
messages that do not contain all six joints are NOT written and are counted in bag_summary.json
(`incomplete_*`), which the analysis turns into a failure. t_header is the message header stamp (sim time),
t_bag the bag receive time (sim time at the recorder).
Writes (next to the bag, in RUN/raw/): joint_states.csv, controller_state.csv, link_truth.csv, clock.csv,
bag_commands.json, bag_summary.json; with --hf also hf_*.csv in the task0 layout for evaluate_hf_windows.py.
"""
import argparse
import csv
import json
import math
import os
import sys

import rosbag

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import task1_lib as L  # noqa: E402

J = L.JOINTS
CTRL = "/eff_joint_traj_controller"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bag", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--link-topic", default="/task1/link_states_250")
    ap.add_argument("--base-link", default="forem_ur5::ur5_base_link")
    ap.add_argument("--tip-link", default="forem_ur5::ur5_wrist_3_link")
    ap.add_argument("--hf", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    js, st, ck, lk, cmds = [], [], [], [], []
    summary = {"counts": {}, "incomplete_joint_states": 0, "incomplete_controller_state": 0, "name_order_differs_joint_states": 0,
               "name_order_differs_controller_state": 0, "missing_link_messages": 0, "non_finite_rows": 0}
    cnt = summary["counts"]
    with rosbag.Bag(a.bag) as bag:
        for topic, m, t in bag.read_messages():
            cnt[topic] = cnt.get(topic, 0) + 1
            tb = t.to_sec()
            if topic == "/joint_states":
                try:
                    q = L.map_by_name(m.name, list(m.position)); v = L.map_by_name(m.name, list(m.velocity)); e = L.map_by_name(m.name, list(m.effort))
                except L.InvalidInput:
                    summary["incomplete_joint_states"] += 1
                    continue
                if list(m.name) != J:
                    summary["name_order_differs_joint_states"] += 1
                row = [m.header.stamp.to_sec(), tb, m.header.seq] + q + v + e
                summary["non_finite_rows"] += int(not all(math.isfinite(x) for x in row))
                js.append(row)
            elif topic == CTRL + "/state":
                try:
                    g = lambda x: L.map_by_name(m.joint_names, list(x))
                    row = [m.header.stamp.to_sec(), tb, m.header.seq] + g(m.desired.positions) + g(m.actual.positions) + g(m.error.positions) + \
                          g(m.desired.velocities) + g(m.actual.velocities) + g(m.error.velocities)
                except L.InvalidInput:
                    summary["incomplete_controller_state"] += 1
                    continue
                if list(m.joint_names) != J:
                    summary["name_order_differs_controller_state"] += 1
                summary["non_finite_rows"] += int(not all(math.isfinite(x) for x in row))
                st.append(row)
            elif topic == "/clock":
                ck.append([m.clock.to_sec(), tb])
            elif topic == a.link_topic:
                names = list(m.name)
                if a.base_link in names and a.tip_link in names:
                    ib, it = names.index(a.base_link), names.index(a.tip_link)
                    pb, pt = m.pose[ib], m.pose[it]
                    lk.append([tb, pb.position.x, pb.position.y, pb.position.z, pb.orientation.x, pb.orientation.y, pb.orientation.z, pb.orientation.w,
                               pt.position.x, pt.position.y, pt.position.z, pt.orientation.x, pt.orientation.y, pt.orientation.z, pt.orientation.w])
                else:
                    summary["missing_link_messages"] += 1
            elif topic == CTRL + "/command":
                cmds.append({"t_bag": tb, "seq": int(m.header.seq), "message": L.command_record(m)})

    def write(name, header, rows):
        with open(os.path.join(a.out, name), "w", newline="") as f:
            w = csv.writer(f); w.writerow(header); w.writerows(rows)
        return len(rows)

    hdr_js = ["t_header", "t_bag", "seq"] + ["pos_" + j for j in J] + ["vel_" + j for j in J] + ["eff_" + j for j in J]
    hdr_st = ["t_header", "t_bag", "seq"] + ["des_" + j for j in J] + ["act_" + j for j in J] + ["err_" + j for j in J] + \
             ["desvel_" + j for j in J] + ["actvel_" + j for j in J] + ["errvel_" + j for j in J]
    hdr_lk = ["t_bag"] + ["b_" + c for c in ("x", "y", "z", "qx", "qy", "qz", "qw")] + ["t_" + c for c in ("x", "y", "z", "qx", "qy", "qz", "qw")]
    summary["rows"] = {"joint_states": write("joint_states.csv", hdr_js, js), "controller_state": write("controller_state.csv", hdr_st, st),
                       "link_truth": write("link_truth.csv", hdr_lk, lk), "clock": write("clock.csv", ["t", "t_bag"], ck)}
    json.dump(cmds, open(os.path.join(a.out, "bag_commands.json"), "w"), indent=1)
    if a.hf:  # task0 layout for evaluate_hf_windows.py (t = header stamp)
        d = os.path.dirname(a.out.rstrip("/"))
        write_abs = lambda name, header, rows: csv.writer(open(os.path.join(d, name), "w", newline="")).writerows([header] + rows)
        write_abs("hf_joint_states.csv", ["t"] + hdr_js[3:], [[r[0]] + r[3:] for r in js])
    json.dump(summary, open(os.path.join(a.out, "bag_summary.json"), "w"), indent=2)
    print("task1_bag_to_csv:", json.dumps(summary["rows"]), "incomplete:", summary["incomplete_joint_states"], summary["incomplete_controller_state"])
    bad = summary["incomplete_joint_states"] + summary["incomplete_controller_state"] + summary["non_finite_rows"]
    sys.exit(0 if (js and st and not bad) else 1)


if __name__ == "__main__":
    main()
