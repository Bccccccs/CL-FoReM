"""task3.1 tests of the static source/contract audit (scripts/audit_task3_core.py) on synthetic trees plus the real tree."""
import json
import os
import shutil
import sys
import tempfile
import unittest

try:
    import yaml
except ImportError as e:  # pragma: no cover
    raise unittest.SkipTest("PyYAML not available: %s" % e)

HERE = os.path.dirname(os.path.abspath(__file__))
FOREM = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(FOREM, "scripts"))
import audit_task3_core as A  # noqa: E402


def write(path, text=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class Tree:
    """temp/<repo>/forem/{src,config,scripts} and temp/<repo>/husky/src -- the layout the audit expects."""

    def __enter__(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = os.path.join(self.tmp, "repo")
        self.root = os.path.join(self.repo, "forem")
        os.makedirs(self.root)
        return self

    def __exit__(self, *a):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def w(self, rel, text=""):
        write(os.path.join(self.root, rel), text)


class ShadowTest(unittest.TestCase):
    def test_clean_tree_ok(self):
        with Tree() as t:
            t.w("src/modulation_rl/scripts/modulation/__init__.py")
            t.w("src/modulation_rl/scripts/sac.py")
            ok, det = A.check_shadow(t.root)
            self.assertTrue(ok, det)

    def test_shadow_import_rejected(self):
        # a look-alike modified package, a second importable `modulation`, a second top-level sac.py, a binary in src
        with Tree() as t:
            t.w("src/modulation_rl/scripts/modulation/__init__.py")
            t.w("src/modulation_rl/scripts/modulation（修改后）/__init__.py")
            ok, det = A.check_shadow(t.root)
            self.assertFalse(ok)
            self.assertTrue(any(p[0] == "lookalike_dir" for p in det["problems"]), det)
        with Tree() as t:
            t.w("src/modulation_rl/scripts/modulation/__init__.py")
            t.w("src/other/scripts/modulation/__init__.py")
            self.assertFalse(A.check_shadow(t.root)[0])
        with Tree() as t:
            t.w("src/modulation_rl/scripts/modulation/__init__.py")
            t.w("src/modulation_rl/scripts/sac.py")
            t.w("src/forem_husky/scripts/sac.py")
            ok, det = A.check_shadow(t.root)
            self.assertFalse(ok)
            self.assertTrue(any(p[0] == "duplicate_module_file" for p in det["problems"]), det)
        with Tree() as t:
            t.w("src/modulation_rl/scripts/modulation/__init__.py")
            t.w("src/modulation_rl/scripts/pybindings.cpython-310-x86_64-linux-gnu.so")
            self.assertFalse(A.check_shadow(t.root)[0])

    def test_package_dir_same_basename_is_not_a_shadow(self):
        with Tree() as t:
            t.w("src/modulation_rl/scripts/modulation/__init__.py")
            t.w("src/modulation_rl/scripts/utils.py")
            t.w("src/modulation_rl/scripts/modulation/utils.py")      # modulation.utils != utils
            self.assertTrue(A.check_shadow(t.root)[0])


class PriorTest(unittest.TestCase):
    def sac_yaml(self, **kw):
        a = dict(update_function="update_parameters", prior_agent="none", checkpoint_required=False)
        a.update(kw)
        return yaml.safe_dump(dict(schema=1, algorithm=a))

    def test_clean_entry_ok(self):
        with Tree() as t:
            t.w("scripts/task3_sac_entry.py", "agent.update_parameters(memory, 16, 0)\n")
            t.w("config/task3/sac.yaml", self.sac_yaml())
            self.assertTrue(A.check_prior(t.root)[0])

    def test_prior_required_entry_rejected(self):
        for marker in ("agent.update_parameters_modified(m, 1, 0, prior)", "prior.load_and_freeze_checkpoint(p)",
                       "p='/home/cbl/mm_husky_ws/x'", "ckpt='checkpoints_pnp_plus/sac_checkpoint_husky_ur5_4000'"):
            with Tree() as t:
                t.w("scripts/task3_sac_entry.py", marker + "\n")
                t.w("config/task3/sac.yaml", self.sac_yaml())
                ok, det = A.check_prior(t.root)
                self.assertFalse(ok, marker)
        with Tree() as t:
            t.w("config/task3/sac.yaml", self.sac_yaml(update_function="update_parameters_modified"))
            self.assertFalse(A.check_prior(t.root)[0])
        with Tree() as t:
            t.w("config/task3/sac.yaml", self.sac_yaml(prior_agent="checkpoints/x", checkpoint_required=True))
            self.assertFalse(A.check_prior(t.root)[0])
        with Tree() as t:                                   # missing sac.yaml is a failure, not a pass
            self.assertFalse(A.check_prior(t.root)[0])


class AssetTest(unittest.TestCase):
    def base(self, t):
        t.w("src/forem_husky/package.xml", "<package><name>forem_husky</name></package>")
        t.w("src/husky_ur5/package.xml", "<package><name>husky_ur5</name></package>")
        t.w("src/husky_ur5/meshes/a.dae", "x")

    def test_resolved_references_ok(self):
        with Tree() as t:
            self.base(t)
            t.w("src/forem_husky/launch/x.launch", '<launch><include file="$(find husky_ur5)/a.launch"/><x f="$(find xacro)"/></launch>')
            t.w("src/husky_ur5/urdf/r.xacro", '<m filename="package://husky_ur5/meshes/a.dae"/>')
            ok, det = A.check_assets(t.root)
            self.assertTrue(ok, det)

    def test_missing_asset_rejected(self):
        with Tree() as t:
            self.base(t)
            t.w("src/forem_husky/launch/x.launch", '<launch><include file="$(find not_imported_pkg)/a.launch"/></launch>')
            ok, det = A.check_assets(t.root)
            self.assertFalse(ok)
            self.assertTrue(any(p[0] == "unresolved_package" for p in det["problems"]), det)
        with Tree() as t:
            self.base(t)
            t.w("src/husky_ur5/urdf/r.xacro", '<m filename="package://husky_ur5/meshes/missing.dae"/>')
            ok, det = A.check_assets(t.root)
            self.assertFalse(ok)
            self.assertTrue(any(p[0] == "missing_asset_file" for p in det["problems"]), det)

    def test_commented_and_templated_references_ignored(self):
        with Tree() as t:
            self.base(t)
            t.w("src/forem_husky/launch/x.launch", '<launch><!-- <include file="$(find gone_pkg)/a.launch"/> --></launch>')
            t.w("src/husky_ur5/urdf/r.xacro", '<m filename="package://husky_ur5/meshes/${size}.dae"/>')
            self.assertTrue(A.check_assets(t.root)[0])

    def test_unreached_reference_needs_reason_and_evidence(self):
        with Tree() as t:
            self.base(t)
            t.w("src/husky_ur5/urdf/r.xacro", '<x f="$(find realsense2_description)/u.xacro"/>')
            self.assertFalse(A.check_assets(t.root)[0])
            t.w("config/task3/core_contract.yaml", yaml.safe_dump(dict(schema=1, unreached_package_references=[dict(package="realsense2_description", reason="r")])))
            self.assertFalse(A.check_assets(t.root)[0])        # no evidence
            t.w("config/task3/core_contract.yaml", yaml.safe_dump(dict(schema=1, unreached_package_references=[dict(package="realsense2_description", reason="r", evidence="e")])))
            self.assertTrue(A.check_assets(t.root)[0])


class SemanticTest(unittest.TestCase):
    def manifest(self, t, status, impact=None):
        files = []
        for rel in A.SEMANTIC_FILES:
            e = dict(destination=f"forem/src/modulation_rl/{rel}", status="verbatim")
            files.append(e)
        files[0]["status"] = status
        if impact:
            files[0]["semantic_impact"] = impact
        t.w("config/task3/source_manifest.json", json.dumps(dict(files=files)))
        return files[0]["destination"]

    def test_verbatim_ok(self):
        with Tree() as t:
            self.manifest(t, "verbatim")
            self.assertTrue(A.check_semantic(t.root)[0])

    def test_semantic_diff_required(self):
        with Tree() as t:                                    # silent patch of a reward/IK/task file
            self.manifest(t, "patched")
            ok, det = A.check_semantic(t.root)
            self.assertFalse(ok)
            self.assertEqual(det["problems"][0][0], "semantic_patch_without_declaration")
        with Tree() as t:
            self.manifest(t, "patched", "declared")
            self.assertTrue(A.check_semantic(t.root)[0])
        with Tree() as t:                                    # a semantic file missing from the manifest is also a failure
            t.w("config/task3/source_manifest.json", json.dumps(dict(files=[])))
            self.assertFalse(A.check_semantic(t.root)[0])


class ManifestTest(unittest.TestCase):
    def build(self, t):
        t.w("src/modulation_rl/a.py", "x = 1\n")
        write(os.path.join(t.repo, "husky/src/modulation_rl/a.py"), "x = 1\n")
        h = A.sha256(os.path.join(t.root, "src/modulation_rl/a.py"))
        m = dict(files=[dict(destination="forem/src/modulation_rl/a.py", source="husky/src/modulation_rl/a.py", source_sha256=h,
                             destination_sha256=h, status="verbatim")])
        t.w("config/task3/source_manifest.json", json.dumps(m))
        return m

    def problems(self, t):
        return [p[0] for p in A.check_manifest(t.root)[1]["problems"] if p[0] != "missing_package"]

    def test_consistent(self):
        with Tree() as t:
            self.build(t)
            self.assertEqual(self.problems(t), [])

    def test_modified_destination_and_reference_detected(self):
        with Tree() as t:
            self.build(t)
            t.w("src/modulation_rl/a.py", "x = 2\n")
            self.assertIn("destination_changed_since_manifest", self.problems(t))
        with Tree() as t:
            self.build(t)
            write(os.path.join(t.repo, "husky/src/modulation_rl/a.py"), "x = 3\n")
            self.assertIn("reference_changed", self.problems(t))

    def test_unlisted_file_and_unreasoned_patch_detected(self):
        with Tree() as t:
            self.build(t)
            t.w("src/modulation_rl/extra.py", "y = 1\n")
            self.assertIn("unlisted_files", self.problems(t))
        with Tree() as t:
            m = self.build(t)
            m["files"][0].update(status="patched")
            t.w("config/task3/source_manifest.json", json.dumps(m))
            probs = self.problems(t)
            self.assertIn("patched_without_reason", probs)
            self.assertIn("patched_without_diff", probs)
            self.assertIn("patched_without_semantic_impact", probs)


class RealTreeTest(unittest.TestCase):
    @unittest.skipUnless(os.path.isdir(os.path.join(FOREM, "..", "husky", "src", "modulation_rl")), "reference tree not present")
    def test_real_tree_passes_every_static_audit(self):
        res = A.run_all(FOREM)
        failed = {k: v for k, v in res.items() if isinstance(v, dict) and not v["ok"]}
        self.assertEqual(failed, {}, json.dumps(failed, ensure_ascii=False, default=str)[:800])

    def test_contract_covers_create_env_keys(self):
        hard, soft = A._create_env_keys(os.path.join(FOREM, "src/modulation_rl/scripts/modulation/utils.py"))
        cfg = yaml.safe_load(open(os.path.join(FOREM, "config/task3/task_contract.yaml")))["env_config"]
        self.assertFalse(hard - set(cfg))
        self.assertFalse(soft - set(cfg) - A.OPTIONAL_SOFT_KEYS)


if __name__ == "__main__":
    unittest.main()
