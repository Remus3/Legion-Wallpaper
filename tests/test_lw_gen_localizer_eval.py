"""Torch-free tests for tools/lw_gen_localizer_eval.py PURE adapter.

The localizer eval harness is detector-agnostic. Its only pure logic is
cocowb_to_kp_map: a COCO-WholeBody-133 detection (what SDPose-Wholebody and the
DWPose onnx stack emit, in PIXEL coords) -> the name-keyed kp_map + per-side
hand lists that tools.lw_gen_weaponfix.weapon_roi_from_keypoints already
consumes (slices 1-2, reused unchanged). Neck is absent in COCO-WholeBody, so
it is DERIVED as the shoulder midpoint. Confidence below a floor -> the joint
is dropped (None for a body joint, omitted for a hand point).

This is NOT slice 2's body_to_kp_map (that adapts OpenPose-18); COCO-WholeBody
has different indices and no neck slot, hence a distinct adapter. The module
must import under base python with numpy only (no torch / cv2 / controlnet_aux).
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools import lw_gen_localizer_eval as lle  # noqa: E402
from tools import lw_gen_weaponfix as lgw  # noqa: E402

from _import_probe import assert_import_free  # noqa: E402

IMG_WH = (1000, 500)  # round dims so pixel/normalized math is exact


def make_cwb(overrides):
    """Build a 133-slot COCO-WholeBody list; overrides maps idx -> (x, y, conf).

    Every unset slot is a zero-confidence origin point (the detector's stand-in
    for an unlocalized keypoint), so a test only states the joints it cares
    about and everything else reads as missing under the conf floor.
    """
    kps = [(0.0, 0.0, 0.0)] * 133
    for idx, triple in overrides.items():
        kps[idx] = triple
    return kps


# A well-formed upper body: nose + both shoulders/elbows/wrists, high conf.
GOOD_BODY = {
    0: (500.0, 50.0, 0.9),   # nose        -> (0.50, 0.10)
    5: (400.0, 150.0, 0.9),  # L shoulder  -> (0.40, 0.30)
    6: (600.0, 150.0, 0.9),  # R shoulder  -> (0.60, 0.30)  neck mid (0.50,0.30)
    7: (350.0, 250.0, 0.9),  # L elbow     -> (0.35, 0.50)
    8: (650.0, 250.0, 0.9),  # R elbow     -> (0.65, 0.50)
    9: (300.0, 350.0, 0.9),  # L wrist     -> (0.30, 0.70)
    10: (700.0, 350.0, 0.9),  # R wrist    -> (0.70, 0.70)
}


def test_import_is_torch_free():
    assert_import_free("tools.lw_gen_localizer_eval",
                       ("torch", "cv2", "controlnet_aux"))
    assert callable(lle.cocowb_to_kp_map)


def test_maps_body_joints_and_normalizes():
    kp_map, _lh, _rh = lle.cocowb_to_kp_map(make_cwb(GOOD_BODY), IMG_WH)
    assert kp_map["nose"] == (0.50, 0.10)
    assert kp_map["RElbow"] == (0.65, 0.50)
    assert kp_map["RWrist"] == (0.70, 0.70)
    assert kp_map["LElbow"] == (0.35, 0.50)
    assert kp_map["LWrist"] == (0.30, 0.70)


def test_neck_is_shoulder_midpoint():
    kp_map, _lh, _rh = lle.cocowb_to_kp_map(make_cwb(GOOD_BODY), IMG_WH)
    # midpoint of L(0.40,0.30) and R(0.60,0.30) shoulders
    assert kp_map["neck"] == (0.50, 0.30)


def test_low_conf_joint_becomes_none():
    body = dict(GOOD_BODY)
    body[10] = (700.0, 350.0, 0.05)  # R wrist below floor
    kp_map, _lh, _rh = lle.cocowb_to_kp_map(make_cwb(body), IMG_WH, min_conf=0.3)
    assert kp_map["RWrist"] is None
    assert kp_map["RElbow"] == (0.65, 0.50)  # neighbour unaffected


def test_missing_shoulder_makes_neck_none():
    body = dict(GOOD_BODY)
    body[6] = (600.0, 150.0, 0.05)  # R shoulder below floor -> no midpoint
    kp_map, _lh, _rh = lle.cocowb_to_kp_map(make_cwb(body), IMG_WH, min_conf=0.3)
    assert kp_map["neck"] is None


def test_hand_slices_normalized_and_conf_filtered():
    body = dict(GOOD_BODY)
    # right hand occupies indices 112..132; give two good points + one weak.
    body[112] = (720.0, 360.0, 0.9)  # -> (0.72, 0.72)
    body[113] = (740.0, 380.0, 0.8)  # -> (0.74, 0.76)
    body[114] = (760.0, 400.0, 0.05)  # weak -> dropped
    # left hand occupies 91..111; one good point.
    body[91] = (300.0, 360.0, 0.9)   # -> (0.30, 0.72)
    _kp, lh, rh = lle.cocowb_to_kp_map(make_cwb(body), IMG_WH, min_conf=0.3)
    assert (0.72, 0.72) in rh and (0.74, 0.76) in rh
    assert all(abs(p[0] - 0.76) > 1e-9 for p in rh)  # weak point excluded
    assert lh == [(0.30, 0.72)]


def test_end_to_end_into_weapon_roi():
    kp_map, _lh, rh = lle.cocowb_to_kp_map(make_cwb(GOOD_BODY), IMG_WH)
    res = lgw.weapon_roi_from_keypoints(kp_map, wrist="right", img_wh=IMG_WH, hand=rh)
    assert res.ok is True
    assert res.fallback is None
    assert res.mask_binary is not None


# ---- execution provider selection ------------------------------------------
#
# The sessions were pinned to CPU with a hardcoded list, so the 5070 sat idle
# while yolox_l and dw-ll ran on the 7700X. onnxruntime-gpu alone does not fix
# that: the provider list is what binds a session, and a CPU-only list keeps
# running on CPU no matter which package is installed.
#
# Availability is INJECTED rather than read from the machine, so this asserts
# the policy on a CI runner with no GPU exactly as it does on Legion.


def test_cuda_is_preferred_when_available():
    provs = lle._dwpose_providers(available=["CUDAExecutionProvider",
                                                  "CPUExecutionProvider"])
    assert provs[0] == "CUDAExecutionProvider", "CUDA must be tried first"
    assert provs[-1] == "CPUExecutionProvider", "CPU must stay as the fallback"


def test_cpu_only_machine_gets_cpu_and_does_not_ask_for_cuda():
    """A CUDA entry ORT cannot honour makes InferenceSession raise, so a
    machine without the GPU build must not be handed one."""
    provs = lle._dwpose_providers(available=["CPUExecutionProvider"])
    assert provs == ["CPUExecutionProvider"]


def test_provider_can_be_forced_to_cpu_for_reproducibility(monkeypatch):
    """CUDA and CPU kernels are not bit-identical. Any measurement that has to
    reproduce an earlier CPU number needs a way back without a reinstall."""
    monkeypatch.setenv("LW_ORT_PROVIDER", "cpu")
    provs = lle._dwpose_providers(available=["CUDAExecutionProvider",
                                                  "CPUExecutionProvider"])
    assert provs == ["CPUExecutionProvider"]


# ---- CUDA DLL discovery ----------------------------------------------------
#
# Having onnxruntime-gpu installed is not enough on Windows. The CUDA EP needs
# cudnn64_9.dll and the CUDA 12 runtime on the DLL search path, and pip drops
# those inside site-packages, which Python does not search. When they are not
# found ORT does NOT raise - it silently falls back to CPU, which is exactly
# how the sessions ran on the CPU while reporting a healthy provider list.
#
# Layout is built under tmp_path so this asserts the search rule itself rather
# than whatever happens to be installed on the machine running it.


def _fake_site_packages(tmp_path):
    for rel in ("nvidia/cudnn/bin", "nvidia/cublas/bin", "torch/lib"):
        (tmp_path / rel).mkdir(parents=True)
    return tmp_path


def test_cuda_dll_dirs_finds_pip_nvidia_and_torch_libs(tmp_path):
    dirs = [str(d) for d in lle._cuda_dll_dirs(_fake_site_packages(tmp_path))]
    assert any(d.endswith("cudnn") or d.endswith("bin") for d in dirs)
    assert sum("nvidia" in d for d in dirs) == 2, "both nvidia packages wanted"
    assert any(d.replace(chr(92), "/").endswith("torch/lib") for d in dirs), (
        "torch/lib carries a bundled CUDA runtime and cuDNN and is the reason "
        "importing torch first made the CUDA EP bind")


def test_cuda_dll_dirs_is_empty_when_nothing_is_installed(tmp_path):
    assert lle._cuda_dll_dirs(tmp_path) == []


def test_cuda_dll_dirs_skips_a_missing_nvidia_tree(tmp_path):
    (tmp_path / "torch" / "lib").mkdir(parents=True)
    dirs = [str(d) for d in lle._cuda_dll_dirs(tmp_path)]
    assert len(dirs) == 1 and dirs[0].endswith("lib")


def test_register_cuda_dlls_puts_them_on_path(monkeypatch, tmp_path):
    """PATH is the mechanism that actually binds the CUDA EP - see the
    docstring. Asserted here so a future tidy-up cannot quietly drop back to
    add_dll_directory alone, which fails silently onto CPU."""
    sp = _fake_site_packages(tmp_path)
    # no drive letter: os.pathsep is ":" on a POSIX runner, which would split a
    # Windows-style entry in half and fail for a reason that is not the policy
    monkeypatch.setenv("PATH", "PRE_EXISTING_ENTRY")
    lle._register_cuda_dlls(site_packages=sp, windows=True)
    parts = os.environ["PATH"].split(os.pathsep)
    assert str(sp / "torch" / "lib") in parts
    assert str(sp / "nvidia" / "cudnn" / "bin") in parts
    assert "PRE_EXISTING_ENTRY" in parts, "must not clobber PATH"
