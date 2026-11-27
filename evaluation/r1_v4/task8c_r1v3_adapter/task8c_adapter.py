"""Source-bound Task 8C HDF5 to frozen R1 v3 frame-facts adapter.

This module extracts measurements only. It never imports or invokes the R1
decision functions. `prepare_case` refuses an unverified runner binding unless
the caller explicitly requests diagnostic-only extraction; such facts are
never eligible for a checker execution.
"""
from __future__ import annotations

import hashlib
import itertools
import math
from pathlib import Path

import h5py
import numpy as np

ADAPTER_VERSION = "task8c-r1v3-source-adapter-1.0.0"
EXPECTED_XML_SHA256 = "a6177b7383b3b273ed1f41ad1ca342c921aea86584348a6d05a4bdff703e4542"
EXPECTED_BODY_COUNT = 29
EXPECTED_GEOM_COUNT = 161
EXPECTED_FRAMES = 258
EXPECTED_NATIVE_SAMPLES = 6426
NATIVE_PER_FRAME = 25
FOCUS_OBJECT = "cream_cheese_1"
CONTACT_FIELDS = (
    "sample_index", "geom1", "geom2", "body1", "body2", "dist", "pos",
    "frame", "force_contact_frame", "geom1_name", "geom2_name",
    "body1_name", "body2_name",
)


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate_manifest_case(manifest_row, binding, manifest_sha256):
    """Bind a case to exact authoritative IDs, hashes, and source path."""
    if manifest_sha256 != "f30f4b9e907fa0cdda75c3ca31de08e50de9a916f2f27bf69ece776c37966617":
        raise ValueError("Frozen Task 8C manifest hash mismatch")
    pairs = (("blinded_case_id", "case_id"), ("new_execution_id", "source_execution_id"),
             ("coordinator_group_id", "source_group_id"), ("raw_hdf5_sha256", "recording_sha256"),
             ("xml_sha256", "xml_sha256"))
    for source_key, binding_key in pairs:
        if manifest_row.get(source_key) != binding.get(binding_key):
            raise ValueError("Authoritative case/source binding mismatch: " + source_key)
    if "recording_path" in binding:
        if Path(manifest_row["raw_hdf5_path"]).resolve() != Path(binding["recording_path"]).resolve():
            raise ValueError("Recording path does not match authoritative source binding")


def _text(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", "strict")
    if isinstance(value, np.bytes_):
        return bytes(value).decode("utf-8", "strict")
    return str(value)


def _quat_matrix_wxyz(q):
    """MuJoCo w,x,y,z quaternion to rotation; same scaled arithmetic as v2."""
    q = np.asarray(q, dtype=np.float64)
    if q.shape != (4,) or not np.isfinite(q).all() or float(q @ q) == 0.0:
        raise ValueError("Invalid wxyz body quaternion")
    w, x, y, z = q
    s = 2.0 / float(q @ q)
    return np.array([
        [1-s*(y*y+z*z), s*(x*y-z*w), s*(x*z+y*w)],
        [s*(x*y+z*w), 1-s*(x*x+z*z), s*(y*z-x*w)],
        [s*(x*z-y*w), s*(y*z+x*w), 1-s*(x*x+y*y)],
    ], dtype=np.float64)


def _geometry_world(index, body_xpos, body_xquat):
    """Derive per-geom xPos/xMat from recorded body poses and XML local poses."""
    bp = np.asarray(body_xpos, dtype=np.float64)
    bq = np.asarray(body_xquat, dtype=np.float64)
    if bp.shape != (EXPECTED_BODY_COUNT, 3) or bq.shape != (EXPECTED_BODY_COUNT, 4):
        raise ValueError("Body-state dimensions do not match frozen geometry mapping")
    if not np.isfinite(bp).all() or not np.isfinite(bq).all():
        raise ValueError("Nonfinite body pose")
    rotations = np.stack([_quat_matrix_wxyz(q) for q in bq])
    geoms = index["geometries"]
    ids = np.asarray([g["owner_body_id"] for g in geoms], dtype=np.int64)
    local_p = np.asarray([g["local_position_xml"] for g in geoms], dtype=np.float64)
    local_r = np.asarray([g["local_rotation_xml"] for g in geoms], dtype=np.float64)
    if local_p.shape != (EXPECTED_GEOM_COUNT, 3) or local_r.shape != (EXPECTED_GEOM_COUNT, 3, 3):
        raise ValueError("Native XML geometry transform dimensions mismatch")
    gp = bp[ids] + np.einsum("gij,gj->gi", rotations[ids], local_p)
    gr = rotations[ids] @ local_r
    if not np.isfinite(gp).all() or not np.isfinite(gr).all():
        raise ValueError("Nonfinite reconstructed geometry transform")
    return gp, gr


def _corners(index, geom_id, gp, gr):
    geom = index["geometries"][geom_id]
    if geom["type"] != "mjGEOM_BOX":
        raise ValueError("Frozen R1 v3 collision-vertex rule requires BOX geometry")
    local = np.asarray(list(itertools.product([-1.0, 1.0], repeat=3)), dtype=np.float64)
    local *= np.asarray(geom["size"], dtype=np.float64)
    return local @ gr[geom_id].T + gp[geom_id]


def _entity_and_contact_maps(index, checker_config, physical_config, entity_inventory):
    geoms = index["geometries"]
    body_names = index["body_names"]
    if len(body_names) != EXPECTED_BODY_COUNT or len(geoms) != EXPECTED_GEOM_COUNT:
        raise ValueError("Frozen native geometry mapping dimensions changed")
    for g in geoms:
        owner_id = int(g["owner_body_id"])
        if (owner_id < 0 or owner_id >= len(body_names) or
            g["owner_body"] != body_names[owner_id] or
            g["owner_body"] not in g["body_ancestry"]):
            raise ValueError("Geometry owner identity disagrees with frozen body mapping")
    if entity_inventory.get("schema_version") != "corrected-entity-inventory-v2":
        raise ValueError("Require the frozen corrected entity inventory")
    records = entity_inventory.get("records", [])
    matching = [r for r in records if r.get("source_xml_sha256") == index.get("source_xml_sha256")]
    if not matching:
        raise ValueError("Entity inventory is not bound to the source XML")
    entities = matching[0].get("entities", [])
    if len(entities) != len({e["name"] for e in entities}):
        raise ValueError("Duplicate entity names in frozen entity inventory")
    ids = {}
    id_owner = {}
    entity_names = set()
    for entity in entities:
        name, body, body_id = entity["name"], entity["root_body_name"], int(entity["body_id"])
        if body not in body_names or body_names.index(body) != body_id:
            raise ValueError("Entity body identity disagrees with native XML map: " + name)
        listed = sorted(int(x) for x in entity["native_geom_ids"])
        derived = sorted(g["native_geom_id"] for g in geoms
                         if g["owner_body_id"] == body_id or body in g["body_ancestry"])
        if listed != derived:
            raise ValueError("Entity native geometry IDs disagree with the frozen geometry map: " + name)
        geom_ids = [i for i in listed if geoms[i]["collision_capable"]]
        if not geom_ids:
            raise ValueError("Entity has no collision geometry: " + name)
        if any(geoms[i]["type"] != "mjGEOM_BOX" for i in geom_ids):
            raise ValueError("Frozen R1 collision-vertex extractor requires BOX entity geometry")
        ids[name] = geom_ids
        entity_names.add(name)
        for geom_id in geom_ids:
            if geom_id in id_owner:
                raise ValueError("Conflicting canonical geometry ownership")
            id_owner[geom_id] = name
    if not set(checker_config["objects"]).issubset(entity_names):
        raise ValueError("Evaluation target is missing from the frozen entity inventory")
    table_ids = [int(x) for x in physical_config["table_geom_ids"]]
    floor_ids = [int(x) for x in physical_config["floor_geom_ids"]]
    left_ids = [int(x) for x in physical_config["gripper_left_ids"]]
    right_ids = [int(x) for x in physical_config["gripper_right_ids"]]
    for g in geoms:
        geom_id = int(g["native_geom_id"])
        ancestry = list(g["body_ancestry"]) + [g["owner_body"]]
        if "living_room_table" in ancestry:
            id_owner[geom_id] = "living_room_table"
        elif geom_id in floor_ids:
            id_owner[geom_id] = "floor"
        elif any(str(s).startswith(("robot0_", "gripper0_")) for s in ancestry):
            id_owner[geom_id] = "robot"
    for geom_id in table_ids + floor_ids + left_ids + right_ids:
        if not 0 <= geom_id < len(geoms):
            raise ValueError("Physical configuration contains out-of-range geom ID")
    if any(geoms[g]["type"] != "mjGEOM_BOX" for g in table_ids):
        raise ValueError("Frozen R1 table collision geometry is not all BOX")
    if any(not geoms[g]["collision_capable"] for g in table_ids + floor_ids + left_ids + right_ids):
        raise ValueError("Physical geometry mapping includes non-collision geometry")
    # Only the Task 8C protected cheese and frozen table boxes enter this
    # evaluation unit's vertex/support rule. Require their XML/runtime
    # serialization discrepancy to remain below the checker's own arithmetic
    # allowance; unrelated scene-object transforms are not substituted.
    relevant = ids[FOCUS_OBJECT] + table_ids
    for geom_id in relevant:
        bound = geoms[geom_id].get("box_corner_displacement_bound_due_to_rotation_serialization_m")
        arithmetic_allowance = (checker_config["arithmetic_eps_multiplier"] * np.finfo(float).eps *
                                max(1.0, *map(abs, geoms[geom_id]["size"])))
        if bound is None or float(bound) > arithmetic_allowance:
            raise ValueError("XML/runtime transform difference exceeds frozen arithmetic bound for relevant geometry")
    return ids, id_owner, table_ids, floor_ids, left_ids, right_ids


def _sample_action_index(sample):
    if sample == 0:
        return -1
    return (sample - 1) // NATIVE_PER_FRAME - 10


def _check_contact_bundle(h, index, id_owner):
    physics = h["physics"]
    contacts = h["contacts"]
    n = len(physics["ncon"])
    arrays = {name: contacts[name][()] for name in CONTACT_FIELDS}
    row_count = len(arrays["sample_index"])
    for name in CONTACT_FIELDS:
        if len(arrays[name]) != row_count:
            raise ValueError("Contact parallel-array length mismatch: " + name)
    shapes = {"pos": (row_count, 3), "frame": (row_count, 9),
              "force_contact_frame": (row_count, 6)}
    for name, shape in shapes.items():
        if np.asarray(arrays[name]).shape != shape:
            raise ValueError("Contact dataset shape mismatch: " + name)
    sample = np.asarray(arrays["sample_index"], dtype=np.int64)
    if row_count and (sample.min() < 0 or sample.max() >= n or np.any(sample[1:] < sample[:-1])):
        raise ValueError("Contact sample indices invalid or out of order")
    counts = np.bincount(sample, minlength=n)
    ncon = np.asarray(physics["ncon"][()], dtype=np.int64)
    if len(ncon) != n or not np.array_equal(counts, ncon):
        raise ValueError("Incomplete contact rows: per-sample count differs from ncon")
    for field in ("dist", "pos", "frame", "force_contact_frame"):
        if not np.isfinite(np.asarray(arrays[field], dtype=np.float64)).all():
            raise ValueError("Nonfinite contact measurement: " + field)
    g1 = np.asarray(arrays["geom1"], dtype=np.int64)
    g2 = np.asarray(arrays["geom2"], dtype=np.int64)
    b1 = np.asarray(arrays["body1"], dtype=np.int64)
    b2 = np.asarray(arrays["body2"], dtype=np.int64)
    geom_owner_ids = np.asarray([g["owner_body_id"] for g in index["geometries"]], dtype=np.int64)
    collision = np.asarray([bool(g["collision_capable"]) for g in index["geometries"]])
    if row_count and (g1.min() < 0 or g2.min() < 0 or g1.max() >= len(geom_owner_ids) or g2.max() >= len(geom_owner_ids)):
        raise ValueError("Contact references an unknown geometry ID")
    if row_count and (not collision[g1].all() or not collision[g2].all()):
        raise ValueError("Contact references a non-collision geometry")
    if not np.array_equal(b1, geom_owner_ids[g1]) or not np.array_equal(b2, geom_owner_ids[g2]):
        raise ValueError("Contact body IDs disagree with native geometry owners")
    if any(int(x) not in id_owner for x in np.concatenate((g1, g2))):
        raise ValueError("Contact geometry lacks frozen canonical entity mapping")
    geom_names = [g["name"] or "" for g in index["geometries"]]
    body_names = index["body_names"]
    for slot, geom_ids in (("geom1_name", g1), ("geom2_name", g2)):
        observed = [_text(x) for x in arrays[slot]]
        expected = [geom_names[int(i)] for i in geom_ids]
        if observed != expected:
            raise ValueError("Contact geometry names disagree with native mapping")
    for slot, body_ids in (("body1_name", b1), ("body2_name", b2)):
        observed = [_text(x) for x in arrays[slot]]
        expected = [body_names[int(i)] for i in body_ids]
        if observed != expected:
            raise ValueError("Contact body names disagree with native mapping")
    return arrays, counts


def _frame_facts(frame, sample_idx, time_s, body_xpos, body_xquat, contact_rows,
                 index, ids, id_owner, table_ids, floor_ids, left_ids, right_ids,
                 checker_config, evaluation_names):
    gp, gr = _geometry_world(index, body_xpos, body_xquat)
    boxes = {}
    entity_collision_ids = {i for name in evaluation_names for i in ids[name]}
    for geom_id in entity_collision_ids | set(table_ids):
        boxes[geom_id] = _corners(index, geom_id, gp, gr)
    bounds = {i: (v.min(0), v.max(0)) for i, v in boxes.items()}
    table_vertices = np.concatenate([boxes[i] for i in table_ids])
    table_lo, table_hi = table_vertices.min(0), table_vertices.max(0)
    objects = {}
    for name in evaluation_names:
        geom_ids = ids[name]
        vertices = np.concatenate([boxes[i] for i in geom_ids])
        lo, hi = vertices.min(0), vertices.max(0)
        tol = checker_config["arithmetic_eps_multiplier"] * np.finfo(float).eps * max(
            1.0, *(abs(float(v)) for v in list(lo) + list(hi) + list(table_lo) + list(table_hi)))
        separated = all(any(hi[k] < bounds[i][0][k] - tol or lo[k] > bounds[i][1][k] + tol
                            for k in range(3)) for i in table_ids)
        objects[name] = dict(valid=True, vertices=vertices.tolist(),
            bounds=[lo.tolist(), hi.tolist()],
            pose=np.concatenate([np.concatenate([gp[i].ravel(), gr[i].ravel()]) for i in geom_ids]).tolist(),
            contact_native_ids=[], contact_entities=[], support_parents=[], supported_children=[],
            support_contacts=[], table_contact=False, table_separated=bool(separated),
            bilateral_gripper=False,
            finger_z={"left": float(np.mean(gp[left_ids, 2])), "right": float(np.mean(gp[right_ids, 2]))}
                if left_ids and right_ids else {"left": float("nan"), "right": float("nan")})
    for ct in contact_rows:
        a, b = int(ct["geom1"]), int(ct["geom2"])
        # Both geometries have already been checked against the native map.
        for child, lower in ((a, b), (b, a)):
            name = id_owner.get(child)
            if name not in objects or id_owner.get(lower) == name:
                continue
            parent = id_owner.get(lower)
            if parent is None:
                raise ValueError("Contact owner is not canonically mapped")
            if parent not in ("living_room_table", "floor", "robot"):
                raise ValueError("Protected object has an object-to-object contact; exact support-chain geometry is not established")
            o = objects[name]
            o["contact_native_ids"].append(lower)
            o["contact_entities"].append(parent)
            o["table_contact"] |= parent == "living_room_table"
            if lower not in boxes or parent in ("robot", "floor"):
                continue
            plo, phi = bounds[lower]
            clo, chi = o["bounds"]
            olow = o["bounds"][0][2]
            p = np.asarray(ct["pos"], dtype=np.float64)
            d = float(ct["dist"])
            tol = checker_config["arithmetic_eps_multiplier"] * np.finfo(float).eps * max(
                1.0, *(abs(float(v)) for v in list(plo) + list(phi) + list(clo) + list(chi) + list(p) + [d]))
            horizontal = abs(max(abs(float(x)) for x in gr[lower][2]) - 1.0) <= tol
            overlap = all(max(plo[k], clo[k]) - tol <= p[k] <= min(phi[k], chi[k]) + tol for k in (0, 1))
            if (horizontal and overlap and d <= tol and
                abs((clo[2] - phi[2]) - d) <= tol and
                abs(2*p[2] - clo[2] - phi[2]) <= tol and abs(olow - clo[2]) <= tol):
                o["support_parents"].append(parent)
                if parent in objects:
                    objects[parent]["supported_children"].append(name)
                o["support_contacts"].append(dict(child_native_geom=child, parent_native_geom=lower,
                    parent_entity=parent, position=p.tolist(), recorded_signed_distance=d,
                    face_consistency_arithmetic_allowance=tol))
    for o in objects.values():
        for key in ("contact_native_ids", "contact_entities", "support_parents", "supported_children"):
            o[key] = sorted(set(o[key]))
        touched = set(o["contact_native_ids"])
        o["bilateral_gripper"] = bool(touched & set(left_ids)) and bool(touched & set(right_ids))
    table_pose = np.concatenate([np.concatenate([gp[i].ravel(), gr[i].ravel()]) for i in table_ids]).tolist()
    return dict(frame=frame, time=float(time_s), valid=True, contacts_complete=True,
        mapping_valid=True, sample_index=int(sample_idx), table_pose=table_pose, objects=objects)


def prepare_case(recording_path, source_xml_path, case_binding, geometry_index,
                 physical_config, checker_config, entity_inventory, *, diagnostic_unverified=False):
    """Validate one source and return exact saved-frame checker facts, no verdict.

    The facts are returned only after complete cohort, geometry, contact and
    temporal checks. A runner-unverified case can be extracted for diagnostics
    only; its `checker_eligible` flag remains false and a caller must not score it.
    """
    path = Path(recording_path)
    if case_binding.get("source_provenance_status") != "VERIFIED":
        if not diagnostic_unverified:
            raise ValueError("Runner provenance unverified; frozen checker execution forbidden")
    else:
        runner_path = case_binding.get("runner_source_path")
        if (not runner_path or not Path(runner_path).is_file() or
            sha256_file(runner_path) != case_binding.get("runner_sha256")):
            raise ValueError("Runner source SHA-256 mismatch")
    if sha256_file(path) != case_binding["recording_sha256"]:
        raise ValueError("Recording SHA-256 mismatch")
    if sha256_file(source_xml_path) != case_binding["xml_sha256"]:
        raise ValueError("Simulator XML SHA-256 mismatch")
    if case_binding["xml_sha256"] != EXPECTED_XML_SHA256:
        raise ValueError("Simulator XML is not the frozen geometry-map source")
    if geometry_index.get("source_xml_sha256") != EXPECTED_XML_SHA256:
        raise ValueError("Geometry index XML binding mismatch")
    if geometry_index.get("native_geom_count") != EXPECTED_GEOM_COUNT:
        raise ValueError("Geometry index count mismatch")
    ids, id_owner, table_ids, floor_ids, left_ids, right_ids = _entity_and_contact_maps(
        geometry_index, checker_config, physical_config, entity_inventory)
    if FOCUS_OBJECT not in ids:
        raise ValueError("The Task 8C protected object is absent from the frozen entity inventory")
    evaluation_names = [FOCUS_OBJECT]
    frames = []
    with h5py.File(path, "r") as h:
        attrs = h.attrs
        if _text(attrs["execution_kind"]) != "fresh_deterministic_reset":
            raise ValueError("Unsupported recording execution type")
        if _text(attrs["target_object"]) != "cream_cheese_1" or int(attrs["target_body_id"]) != 22 or _text(attrs["target_body_name"]) != "cream_cheese_1_main":
            raise ValueError("Protected object/body identity mismatch")
        if int(attrs["r1_boundary_frame"]) != 10 or int(attrs["terminal_frame"]) != 257:
            raise ValueError("Frozen monitoring boundary or terminal frame mismatch")
        if not math.isclose(float(attrs["native_timestep_s"]), 0.002, rel_tol=0, abs_tol=1e-12):
            raise ValueError("Native physics timestep mismatch")
        if not math.isclose(float(attrs["control_timestep_s"]), 0.05, rel_tol=0, abs_tol=1e-12):
            raise ValueError("Observation/control period mismatch")
        for name in ("actions/settling_actions", "actions/stationary_hold_actions"):
            if name not in h or h[name].ndim != 2 or h[name].shape[1] != 7:
                raise ValueError("Action dataset missing or malformed: " + name)
        if h["actions/settling_actions"].shape[0] != 10 or h["actions/stationary_hold_actions"].shape[0] != 247:
            raise ValueError("Action boundaries do not match frozen monitoring interval")
        obs = h["observations"]
        if len(obs["source_frame"]) != EXPECTED_FRAMES or len(obs["time"]) != EXPECTED_FRAMES:
            raise ValueError("Observation frame coverage mismatch")
        source_frames = np.asarray(obs["source_frame"][()], dtype=np.int64)
        if not np.array_equal(source_frames, np.arange(EXPECTED_FRAMES)):
            raise ValueError("Missing, duplicated, or out-of-order observation frames")
        physics = h["physics"]
        if len(physics["time_after"]) != EXPECTED_NATIVE_SAMPLES:
            raise ValueError("Native physics sample coverage mismatch")
        for field, expected_tail in (("body_xpos", (EXPECTED_BODY_COUNT, 3)),
                                     ("body_xquat", (EXPECTED_BODY_COUNT, 4))):
            if physics[field].shape != (EXPECTED_NATIVE_SAMPLES,) + expected_tail:
                raise ValueError("Native body-state shape mismatch: " + field)
        if physics["action_index"].shape != (EXPECTED_NATIVE_SAMPLES,):
            raise ValueError("Native action-index shape mismatch")
        before = np.asarray(physics["time_before"][()], dtype=np.float64)
        after = np.asarray(physics["time_after"][()], dtype=np.float64)
        if not np.isfinite(before).all() or not np.isfinite(after).all():
            raise ValueError("Nonfinite native timestamp")
        allowance = checker_config["time_arithmetic_allowance_s"]
        dt = np.diff(after)
        if not np.all(np.abs(dt - 0.002) <= allowance):
            raise ValueError("Native physics time sequence is incomplete or misaligned")
        if not np.all(np.abs(after[1:] - before[1:] - 0.002) <= allowance):
            raise ValueError("Native pre/post step timestamps are misaligned")
        native_action = np.asarray(physics["action_index"][()], dtype=np.int64)
        expected_action = np.asarray([_sample_action_index(i) for i in range(EXPECTED_NATIVE_SAMPLES)])
        if not np.array_equal(native_action, expected_action):
            raise ValueError("Action-to-native-sample boundaries do not match frozen frame projection")
        arrays, counts = _check_contact_bundle(h, geometry_index, id_owner)
        obs_time = np.asarray(obs["time"][()], dtype=np.float64)
        physics_sample = np.arange(EXPECTED_FRAMES, dtype=np.int64) * NATIVE_PER_FRAME
        if not np.all(np.abs(obs_time - after[physics_sample]) <= allowance):
            raise ValueError("Observation timestamps do not align to native endpoint samples")
        if not np.all(np.abs(obs_time - np.arange(EXPECTED_FRAMES)*0.05) <= allowance):
            raise ValueError("Observation timeline violates frozen 50ms cadence")
        # Only the frozen 20 Hz frame endpoints are projected into checker facts.
        # Intermediate 2 ms samples validate completeness but are never substituted
        # for a missing 50 ms checker frame.
        contact_sample = np.asarray(arrays["sample_index"], dtype=np.int64)
        for frame, sample_idx in enumerate(physics_sample):
            lo = int(np.searchsorted(contact_sample, sample_idx, side="left"))
            hi = int(np.searchsorted(contact_sample, sample_idx, side="right"))
            rows = []
            for r in range(lo, hi):
                rows.append({"geom1": int(arrays["geom1"][r]), "geom2": int(arrays["geom2"][r]),
                             "body1": int(arrays["body1"][r]), "body2": int(arrays["body2"][r]),
                             "pos": np.asarray(arrays["pos"][r], dtype=np.float64).tolist(),
                             "dist": float(arrays["dist"][r])})
            fact = _frame_facts(frame, sample_idx, obs_time[frame],
                physics["body_xpos"][sample_idx], physics["body_xquat"][sample_idx], rows,
                geometry_index, ids, id_owner, table_ids, floor_ids, left_ids, right_ids,
                checker_config, evaluation_names)
            frames.append(fact)
    return {"adapter_version": ADAPTER_VERSION, "case_id": case_binding["case_id"],
        "source_execution_id": case_binding["source_execution_id"],
        "source_group_id": case_binding["source_group_id"],
        "recording_sha256": case_binding["recording_sha256"],
        "runner_sha256": case_binding["runner_sha256"],
        "source_provenance_status": case_binding["source_provenance_status"],
        "checker_eligible": case_binding["source_provenance_status"] == "VERIFIED",
        "frame_count": len(frames), "native_sample_count": EXPECTED_NATIVE_SAMPLES,
        "contact_row_count": len(arrays["sample_index"]),
        "contact_rows_complete_all_native_samples": True,
        "frame_to_sample_stride": NATIVE_PER_FRAME,
        "monitoring_start_frame": 10, "terminal_frame": 257,
        "intermediate_native_samples_used_as_checker_frames": False,
        "frames": frames}
