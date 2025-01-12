import pytest
import jax.numpy as jnp
import os
import numpy as np
import jax
import mujoco
from mujoco import MjModel, MjData, mj_id2name
from jax import lax
from loco_mujoco.trajectory.dataclasses import interpolate_trajectories


from loco_mujoco.trajectory import (
    Trajectory,
    TrajectoryInfo,
    TrajectoryData,
)

from conftest import *


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_save(
    backend,
    input_trajectory_info_data,
    input_trajectory_data,
    input_trajectory_transitions,
    tmp_path,
):
    # todo: combine load and save to a single function, and then iterate over all different attributes in the dataclasses
    path = tmp_path / "test.npz"
    info = input_trajectory_info_data(backend)
    data = input_trajectory_data(backend)
    transitions = input_trajectory_transitions(backend)
    object_test = Trajectory(info, data, transitions)
    object_test.save(path)

    assert path.exists(), "File was not created"

    loaded = np.load(path, allow_pickle=True)
    for key in ["qpos", "qvel"]:
        np.testing.assert_array_equal(loaded[key], getattr(data, key))


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_load(
    backend,
    input_trajectory_info_data,
    input_trajectory_data,
    input_trajectory_transitions,
    tmp_path,
):
    path = tmp_path / "test.npz"
    info = input_trajectory_info_data(backend)
    data = input_trajectory_data(backend)
    transitions = input_trajectory_transitions(backend)

    object_test = Trajectory(info, data, transitions)
    object_test.save(path)
    trajectory = Trajectory.load(path)

    assert trajectory.info.joint_names == info.joint_names
    assert trajectory.info.frequency == info.frequency
    assert trajectory.info.metadata == info.metadata
    assert trajectory.info.site_names == info.site_names
    assert trajectory.info.body_names == info.body_names

    np.testing.assert_allclose(trajectory.data.qpos, data.qpos, atol=1e-7)
    np.testing.assert_allclose(trajectory.data.qvel, data.qvel, atol=1e-7)
    np.testing.assert_allclose(
        trajectory.transitions.observations, transitions.observations, atol=1e-7
    )
    np.testing.assert_allclose(
        trajectory.transitions.next_observations,
        transitions.next_observations,
        atol=1e-7,
    )
    np.testing.assert_allclose(
        trajectory.transitions.absorbings, transitions.absorbings, atol=1e-7
    )
    np.testing.assert_allclose(
        trajectory.transitions.dones, transitions.dones, atol=1e-7
    )
    np.testing.assert_allclose(
        trajectory.transitions.actions, transitions.actions, atol=1e-7
    )
    np.testing.assert_allclose(
        trajectory.transitions.rewards, transitions.rewards, atol=1e-7
    )


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_info__post_init__(
    backend,
    input_trajectory_info_data,
    input_expected_joint_name2ind_qpos,
    input_body_name2ind,
    input_site_name2ind,
):
    trajectoryInfo: TrajectoryInfo = input_trajectory_info_data(backend)

    expected_joint_name2ind_qpos = input_expected_joint_name2ind_qpos(backend)
    expected_body_name2ind = input_body_name2ind(backend)
    expected_site_name2ind = input_site_name2ind(backend)

    # Validate joint name to index mapping
    for key, expected_value in expected_joint_name2ind_qpos.items():
        np.testing.assert_array_equal(
            expected_value,
            trajectoryInfo.joint_name2ind_qpos[key],
            err_msg=f"Mismatch for joint '{key}' in backend {backend}",
        )

    # Validate body name to index mapping
    for key, expected_value in expected_body_name2ind.items():
        np.testing.assert_array_equal(
            expected_value,
            trajectoryInfo.body_name2ind[key],
            err_msg=f"Mismatch for body '{key}' in backend {backend}",
        )

    # Validate site name to index mapping
    for key, expected_value in expected_site_name2ind.items():
        np.testing.assert_array_equal(
            expected_value,
            trajectoryInfo.site_name2ind[key],
            err_msg=f"Mismatch for site '{key}' in backend {backend}",
        )


def test_trajectory_info_get_attribute_names(input_trajectory_info_field_names):
    attribute_names = TrajectoryInfo.get_attribute_names()

    assert (
        attribute_names == input_trajectory_info_field_names
    ), f"Expected {input_trajectory_info_field_names}, but got {attribute_names}"


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_info_add_joint(backend, input_trajectory_info_data):
    trajectoryInfo: TrajectoryInfo = input_trajectory_info_data(backend)

    backend_type = jnp if backend == "jax" else np

    jnt_names = trajectoryInfo.joint_names
    jnt_type = trajectoryInfo.model.jnt_type

    trajectoryInfo = trajectoryInfo.add_joint("joint1", 3, backend_type)
    jnt_names.append("joint1")
    jnt_type = backend_type.append(jnt_type, 3)

    assert trajectoryInfo.joint_names == jnt_names

    np.testing.assert_array_equal(trajectoryInfo.model.jnt_type, jnt_type)

    trajectoryInfo = trajectoryInfo.add_joint("joint2", 0)
    jnt_names.append("joint2")
    jnt_type = backend_type.append(jnt_type, 0)

    assert trajectoryInfo.joint_names == jnt_names
    np.testing.assert_array_equal(trajectoryInfo.model.jnt_type, jnt_type)


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_info_add_body(backend, input_trajectory_info_data):
    trajectoryInfo: TrajectoryInfo = input_trajectory_info_data(backend)

    backend_type = jnp if backend == "jax" else np

    nbody = trajectoryInfo.model.nbody
    body_rootid = trajectoryInfo.model.body_rootid
    body_weldid = trajectoryInfo.model.body_weldid
    body_mocapid = trajectoryInfo.model.body_mocapid
    body_pos = trajectoryInfo.model.body_pos
    body_quat = trajectoryInfo.model.body_quat
    body_ipos = trajectoryInfo.model.body_ipos
    body_iquat = trajectoryInfo.model.body_iquat

    trajectoryInfo = trajectoryInfo.add_body(
        "head",
        15,
        16,
        17,
        backend_type.array([0.0, 0.0, 0.0]),
        backend_type.array([1.0, 0.0, 0.0, 0.0]),
        backend_type.array([0.0, 0.0, 0.0]),
        backend_type.array([1.0, 0.0, 0.0, 0.0]),
        backend_type,
    )

    body_rootid = backend_type.append(body_rootid, 15)
    body_weldid = backend_type.append(body_weldid, 16)
    body_mocapid = backend_type.append(body_mocapid, 17)
    new_row = backend_type.array([0.0, 0.0, 0.0])
    body_pos = backend_type.vstack([body_pos, new_row])
    new_row = backend_type.array([1.0, 0.0, 0.0, 0.0])
    body_quat = backend_type.vstack([body_quat, new_row])
    new_row = backend_type.array([0.0, 0.0, 0.0])
    body_ipos = backend_type.vstack([body_ipos, new_row])
    new_row = backend_type.array([1.0, 0.0, 0.0, 0.0])
    body_iquat = backend_type.vstack([body_iquat, new_row])

    assert trajectoryInfo.model.nbody == nbody + 1
    np.testing.assert_array_equal(trajectoryInfo.model.body_rootid, body_rootid)
    np.testing.assert_array_equal(trajectoryInfo.model.body_weldid, body_weldid)
    np.testing.assert_array_equal(trajectoryInfo.model.body_mocapid, body_mocapid)
    np.testing.assert_array_equal(trajectoryInfo.model.body_pos, body_pos)
    np.testing.assert_array_equal(trajectoryInfo.model.body_quat, body_quat)
    np.testing.assert_array_equal(trajectoryInfo.model.body_ipos, body_ipos)
    np.testing.assert_array_equal(trajectoryInfo.model.body_iquat, body_iquat)


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_info_add_site(backend, input_trajectory_info_data):
    trajectoryInfo: TrajectoryInfo = input_trajectory_info_data(backend)

    backend_type = jnp if backend == "jax" else np

    site_names = trajectoryInfo.site_names
    site_bodyid = trajectoryInfo.model.site_bodyid
    site_pos = trajectoryInfo.model.site_pos
    site_quat = trajectoryInfo.model.site_quat

    trajectoryInfo = trajectoryInfo.add_site(
        "new_site",
        backend_type.array([0.0, 0.0, 0.0]),
        backend_type.array([1.0, 0.0, 0.0, 0.0]),
        2,
        backend_type,
    )

    site_names.append("new_site")
    site_bodyid = backend_type.append(site_bodyid, 2)
    new_row = backend_type.array([0.0, 0.0, 0.0])
    site_pos = backend_type.vstack([site_pos, new_row])
    new_row = backend_type.array([1.0, 0.0, 0.0, 0.0])
    site_quat = backend_type.vstack([site_quat, new_row])

    assert trajectoryInfo.site_names == site_names
    np.testing.assert_array_equal(trajectoryInfo.model.site_bodyid, site_bodyid)
    np.testing.assert_array_equal(trajectoryInfo.model.site_pos, site_pos)
    np.testing.assert_array_equal(trajectoryInfo.model.site_quat, site_quat)


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_info_remove_joints(backend, input_trajectory_info_data):
    trajectoryInfo: TrajectoryInfo = input_trajectory_info_data(backend)

    backend_type = jnp if backend == "jax" else np

    last_joint = trajectoryInfo.joint_names[-1]
    joint_names = trajectoryInfo.joint_names[:-1]
    jnt_type = trajectoryInfo.model.jnt_type[:-1]
    njnt = trajectoryInfo.model.njnt

    trajectoryInfo = trajectoryInfo.remove_joints([last_joint], backend_type)

    assert trajectoryInfo.joint_names == joint_names
    assert trajectoryInfo.model.njnt == njnt - 1
    np.testing.assert_array_equal(trajectoryInfo.model.jnt_type, jnt_type)


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_info_remove_bodies(backend, input_trajectory_info_data):
    trajectoryInfo: TrajectoryInfo = input_trajectory_info_data(backend)

    backend_type = jnp if backend == "jax" else np
    last_body_name = trajectoryInfo.body_names[-1]
    body_names = trajectoryInfo.body_names[:-1]
    nbody = trajectoryInfo.model.nbody - 1
    body_rootid = trajectoryInfo.model.body_rootid[:-1]
    body_weldid = trajectoryInfo.model.body_weldid[:-1]
    body_mocapid = trajectoryInfo.model.body_mocapid[:-1]
    body_pos = trajectoryInfo.model.body_pos[:-1]
    body_quat = trajectoryInfo.model.body_quat[:-1]
    body_ipos = trajectoryInfo.model.body_ipos[:-1]
    body_iquat = trajectoryInfo.model.body_iquat[:-1]
    trajectoryInfo = trajectoryInfo.remove_bodies([last_body_name], backend_type)

    assert trajectoryInfo.body_names == body_names
    assert trajectoryInfo.model.nbody == nbody
    np.testing.assert_array_equal(trajectoryInfo.model.body_rootid, body_rootid)
    np.testing.assert_array_equal(trajectoryInfo.model.body_weldid, body_weldid)
    np.testing.assert_array_equal(trajectoryInfo.model.body_mocapid, body_mocapid)
    np.testing.assert_array_equal(trajectoryInfo.model.body_pos, body_pos)
    np.testing.assert_array_equal(trajectoryInfo.model.body_quat, body_quat)
    np.testing.assert_array_equal(trajectoryInfo.model.body_ipos, body_ipos)
    np.testing.assert_array_equal(trajectoryInfo.model.body_iquat, body_iquat)


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_info_remove_sites(backend, input_trajectory_info_data):
    trajectoryInfo: TrajectoryInfo = input_trajectory_info_data(backend)

    backend_type = jnp if backend == "jax" else np
    last_site_name = trajectoryInfo.site_names[-1]
    site_names = trajectoryInfo.site_names[:-1]
    nsite = trajectoryInfo.model.nsite - 1
    site_bodyid = trajectoryInfo.model.site_bodyid[:-1]
    site_pos = trajectoryInfo.model.site_pos[:-1]
    site_quat = trajectoryInfo.model.site_quat[:-1]
    trajectoryInfo = trajectoryInfo.remove_sites([last_site_name], backend_type)

    assert trajectoryInfo.site_names == site_names
    assert trajectoryInfo.model.nsite == nsite
    np.testing.assert_array_equal(trajectoryInfo.model.site_bodyid, site_bodyid)
    np.testing.assert_array_equal(trajectoryInfo.model.site_pos, site_pos)
    np.testing.assert_array_equal(trajectoryInfo.model.site_quat, site_quat)


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_info_reorder_joints(backend, input_trajectory_info_data):
    trajectoryInfo: TrajectoryInfo = input_trajectory_info_data(backend)

    backend_type = jnp if backend == "jax" else np

    trajectoryInfo = trajectoryInfo.reorder_joints(
        [1, 0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], backend_type
    )

    assert trajectoryInfo.joint_names == [
        "abdomen_z",
        "root",
        "abdomen_y",
        "abdomen_x",
        "right_hip_x",
        "right_hip_z",
        "right_hip_y",
        "right_knee",
        "left_hip_x",
        "left_hip_z",
        "left_hip_y",
        "left_knee",
    ]

    np.testing.assert_array_equal(
        trajectoryInfo.model.jnt_type,
        backend_type.array([3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
    )


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_info_reorder_bodies(backend, input_trajectory_info_data):
    trajectoryInfo: TrajectoryInfo = input_trajectory_info_data(backend)

    backend_type = jnp if backend == "jax" else np

    body_names = trajectoryInfo.body_names.copy()
    body_names[0], body_names[1] = body_names[1], body_names[0]

    trajectoryInfo = trajectoryInfo.reorder_bodies(
        [1, 0, 2, 3, 4, 5, 6, 7, 8, 9], backend_type
    )

    assert trajectoryInfo.body_names == body_names
    np.testing.assert_array_equal(
        trajectoryInfo.model.body_rootid,
        backend_type.array([1, 0, 1, 1, 1, 1, 1, 1, 1, 1]),
    )
    np.testing.assert_array_equal(
        trajectoryInfo.model.body_weldid,
        backend_type.array([1, 0, 2, 3, 4, 5, 5, 7, 8, 8]),
    )
    np.testing.assert_array_equal(
        trajectoryInfo.model.body_mocapid,
        backend_type.array([-1, -1, -1, -1, -1, -1, -1, -1, -1, -1]),
    )
    np.testing.assert_array_equal(
        trajectoryInfo.model.body_pos,
        backend_type.array(
            [
                [0.0, 0.0, 1.4],
                [0.0, 0.0, 0.0],
                [-0.01, 0.0, -0.26],
                [0.0, 0.0, -0.165],
                [0.0, -0.1, -0.04],
                [0.0, 0.01, -0.403],
                [0.0, 0.0, -0.45],
                [0.0, 0.1, -0.04],
                [0.0, -0.01, -0.403],
                [0.0, 0.0, -0.45],
            ]
        ),
    )
    np.testing.assert_array_almost_equal(
        trajectoryInfo.model.body_quat,
        backend_type.array(
            [
                [
                    1.0,
                    0.0,
                    0.0,
                    0.0,
                ],
                [1.0, 0.0, 0.0, 0.0],
                [0.999998, 0.0, -0.002, 0.0],
                [0.999998, 0.0, -0.002, 0.0],
                [1.0, 0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0],
            ]
        ),
    )
    np.testing.assert_array_almost_equal(
        trajectoryInfo.model.body_ipos,
        backend_type.array(
            [
                [-0.00253938, 0.0, 0.03466259],
                [0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0],
                [-0.02, 0.0, 0.0],
                [0.0, 0.005, -0.17],
                [0.0, 0.0, -0.15],
                [0.0, 0.0, 0.1],
                [0.0, -0.005, -0.17],
                [0.0, 0.0, -0.15],
                [0.0, 0.0, 0.1],
            ]
        ),
    )
    np.testing.assert_array_almost_equal(
        trajectoryInfo.model.body_iquat,
        backend_type.array(
            [
                [0.99991226, 0.0, 0.01324499, 0.0],
                [1.0, 0.0, 0.0, 0.0],
                [0.70710677, 0.70710677, 0.0, -0.0],
                [0.70710677, 0.70710677, 0.0, -0.0],
                [0.99989194, 0.01470111, 0.0, -0.0],
                [1.0, 0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0],
                [0.99989194, -0.01470111, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0],
            ]
        ),
    )


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_info_reorder_sites(backend, input_trajectory_info_data):
    trajectoryInfo: TrajectoryInfo = input_trajectory_info_data(backend)

    backend_type = jnp if backend == "jax" else np

    site_names = trajectoryInfo.site_names.copy()
    site_names[-1], site_names[-2] = site_names[-2], site_names[-1]

    trajectoryInfo = trajectoryInfo.reorder_sites([0, 1, 2, 3, 5, 4], backend_type)

    assert trajectoryInfo.site_names == site_names
    np.testing.assert_array_equal(
        trajectoryInfo.model.site_bodyid,
        backend_type.array([1, 3, 4, 6, 9, 7]),
    )
    np.testing.assert_array_equal(
        trajectoryInfo.model.site_pos,
        backend_type.array(
            [
                [0.0, 0.0, 0.1],
                [0.0, 0.0, -0.1],
                [0.0, 0.0, 0.1],
                [0.0, 0.0, 0.15],
                [0.0, 0.0, 0.15],
                [0.0, 0.0, 0.1],
            ]
        ),
    )
    # todo: add different quat values to make this test useful
    np.testing.assert_array_equal(
        trajectoryInfo.model.site_quat,
        backend_type.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0],
            ]
        ),
    )


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_model_get_attribute_names(backend, input_trajectory_info_data):
    trajectoryInfo: TrajectoryInfo = input_trajectory_info_data(backend)

    attribute_names = trajectoryInfo.model.get_attribute_names()

    assert attribute_names == [
        "njnt",
        "jnt_type",
        "nbody",
        "body_rootid",
        "body_weldid",
        "body_mocapid",
        "body_pos",
        "body_quat",
        "body_ipos",
        "body_iquat",
        "nsite",
        "site_bodyid",
        "site_pos",
        "site_quat",
    ]


@pytest.mark.parametrize("backend", ["jax"])
def test_trajectory_model_to_numpy(backend, input_trajectory_info_data):
    trajectoryInfo: TrajectoryInfo = input_trajectory_info_data(backend)

    trajectoryModelNumpy = trajectoryInfo.model.to_numpy()

    assert isinstance(trajectoryModelNumpy.jnt_type, np.ndarray)
    assert isinstance(trajectoryModelNumpy.body_rootid, np.ndarray)
    assert isinstance(trajectoryModelNumpy.body_weldid, np.ndarray)
    assert isinstance(trajectoryModelNumpy.body_mocapid, np.ndarray)
    assert isinstance(trajectoryModelNumpy.body_pos, np.ndarray)
    assert isinstance(trajectoryModelNumpy.body_quat, np.ndarray)
    assert isinstance(trajectoryModelNumpy.body_ipos, np.ndarray)
    assert isinstance(trajectoryModelNumpy.body_iquat, np.ndarray)
    assert isinstance(trajectoryModelNumpy.site_bodyid, np.ndarray)
    assert isinstance(trajectoryModelNumpy.site_pos, np.ndarray)
    assert isinstance(trajectoryModelNumpy.site_quat, np.ndarray)


@pytest.mark.parametrize("backend", ["numpy"])
def test_trajectory_model_to_jax(backend, input_trajectory_info_data):
    trajectoryInfo: TrajectoryInfo = input_trajectory_info_data(backend)

    trajectoryModelJax = trajectoryInfo.model.to_jax()

    assert isinstance(trajectoryModelJax.jnt_type, jax.Array)
    assert isinstance(trajectoryModelJax.body_rootid, jax.Array)
    assert isinstance(trajectoryModelJax.body_weldid, jax.Array)
    assert isinstance(trajectoryModelJax.body_mocapid, jax.Array)
    assert isinstance(trajectoryModelJax.body_pos, jax.Array)
    assert isinstance(trajectoryModelJax.body_quat, jax.Array)
    assert isinstance(trajectoryModelJax.body_ipos, jax.Array)
    assert isinstance(trajectoryModelJax.body_iquat, jax.Array)
    assert isinstance(trajectoryModelJax.site_bodyid, jax.Array)
    assert isinstance(trajectoryModelJax.site_pos, jax.Array)
    assert isinstance(trajectoryModelJax.site_quat, jax.Array)


@pytest.mark.parametrize("backend", ["jax", "numpy"])
@pytest.mark.parametrize(
    "traj_index, sub_traj_index", [(0, 0), (0, 1)]
)  # todo: add more test cases
def test_trajectory_data_get(
    backend, traj_index, sub_traj_index, input_trajectory_data
):
    trajectory_data: TrajectoryData = input_trajectory_data(backend)

    backend_type = jnp if backend == "jax" else np

    data = trajectory_data.get(traj_index, sub_traj_index, backend_type)
    # todo: this test is wrong and will fail for N_trajs > 1. Checkout the get method to see how the actual index is calculated.
    expected_qpos = trajectory_data.qpos[traj_index + sub_traj_index]
    expected_qvel = trajectory_data.qvel[traj_index + sub_traj_index]
    expected_xpos = (
        trajectory_data.xpos[traj_index + sub_traj_index]
        if trajectory_data.xpos.size > 0
        else backend_type.empty(0)
    )
    expected_xquat = (
        trajectory_data.xquat[traj_index + sub_traj_index]
        if trajectory_data.xquat.size > 0
        else backend_type.empty(0)
    )
    expected_cvel = (
        trajectory_data.cvel[traj_index + sub_traj_index]
        if trajectory_data.cvel.size > 0
        else backend_type.empty(0)
    )
    expected_subtree_com = (
        trajectory_data.subtree_com[traj_index + sub_traj_index]
        if trajectory_data.subtree_com.size > 0
        else backend_type.empty(0)
    )
    expected_site_xpos = (
        trajectory_data.site_xpos[traj_index + sub_traj_index]
        if trajectory_data.site_xpos.size > 0
        else backend_type.empty(0)
    )
    expected_site_xmat = (
        trajectory_data.site_xmat[traj_index + sub_traj_index]
        if trajectory_data.site_xmat.size > 0
        else backend_type.empty(0)
    )
    expected_userdata = (
        trajectory_data.userdata[traj_index + sub_traj_index]
        if trajectory_data.userdata.size > 0
        else backend_type.empty(0)
    )

    assert np.allclose(data.qpos, expected_qpos)
    assert np.allclose(data.qvel, expected_qvel)
    assert np.allclose(data.xpos, expected_xpos)
    assert np.allclose(data.xquat, expected_xquat)
    assert np.allclose(data.cvel, expected_cvel)
    assert np.allclose(data.subtree_com, expected_subtree_com)
    assert np.allclose(data.site_xpos, expected_site_xpos)
    assert np.allclose(data.site_xmat, expected_site_xmat)
    assert np.allclose(data.userdata, expected_userdata)


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_dynamic_slice_in_dim(backend, input_trajectory_data):

    trajectory_data: TrajectoryData = input_trajectory_data(backend)

    backend_type = jnp if backend == "jax" else np
    traj_index = 0
    sub_traj_start_index = 0
    slice_length = 2

    sliced_data = TrajectoryData.dynamic_slice_in_dim(
        trajectory_data,
        traj_index,
        sub_traj_start_index,
        slice_length,
        backend_type,
    )

    expected_qpos = backend_type.squeeze(
        trajectory_data.qpos[sub_traj_start_index : sub_traj_start_index + slice_length]
    )
    assert np.allclose(sliced_data.qpos, expected_qpos)

    expected_qvel = backend_type.squeeze(
        trajectory_data.qvel[sub_traj_start_index : sub_traj_start_index + slice_length]
    )
    assert np.allclose(sliced_data.qvel, expected_qvel)

    if trajectory_data.xpos.size > 0:
        expected_xpos = backend_type.squeeze(
            trajectory_data.xpos[
                sub_traj_start_index : sub_traj_start_index + slice_length
            ]
        )
        assert np.allclose(sliced_data.xpos, expected_xpos)

    if trajectory_data.xquat.size > 0:
        expected_xquat = backend_type.squeeze(
            trajectory_data.xquat[
                sub_traj_start_index : sub_traj_start_index + slice_length
            ]
        )
        assert np.allclose(sliced_data.xquat, expected_xquat)

    if trajectory_data.cvel.size > 0:
        expected_cvel = backend_type.squeeze(
            trajectory_data.cvel[
                sub_traj_start_index : sub_traj_start_index + slice_length
            ]
        )
        assert np.allclose(sliced_data.cvel, expected_cvel)

    if trajectory_data.subtree_com.size > 0:
        expected_subtree_com = backend_type.squeeze(
            trajectory_data.subtree_com[
                sub_traj_start_index : sub_traj_start_index + slice_length
            ]
        )
        assert np.allclose(sliced_data.subtree_com, expected_subtree_com)

    if trajectory_data.site_xpos.size > 0:
        expected_site_xpos = backend_type.squeeze(
            trajectory_data.site_xpos[
                sub_traj_start_index : sub_traj_start_index + slice_length
            ]
        )
        assert np.allclose(sliced_data.site_xpos, expected_site_xpos)

    if trajectory_data.site_xmat.size > 0:
        expected_site_xmat = backend_type.squeeze(
            trajectory_data.site_xmat[
                sub_traj_start_index : sub_traj_start_index + slice_length
            ]
        )
        assert np.allclose(sliced_data.site_xmat, expected_site_xmat)


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_dynamic_slice_in_dim_compat(backend, input_trajectory_data):
    trajectory_data: TrajectoryData = input_trajectory_data(backend)

    backend_type = jnp if backend == "jax" else np

    start = 2
    length = 2

    sliced_data = TrajectoryData._dynamic_slice_in_dim_compat(
        trajectory_data.qpos, start, length, backend_type
    )

    if backend == "jax":
        expected_slice = lax.dynamic_slice_in_dim(trajectory_data.qpos, start, length)
    else:
        expected_slice = trajectory_data.qpos[start : start + length].copy()

    assert np.allclose(
        sliced_data, expected_slice
    ), f"Failed for backend {backend_type}. Sliced data: {sliced_data}, Expected: {expected_slice}"


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_get_single_attribute(backend, input_trajectory_data):
    trajectory_data: TrajectoryData = input_trajectory_data(backend)

    backend_type = jnp if backend == "jax" else np

    split_points = trajectory_data.split_points
    traj_index = 0
    sub_traj_index = 2

    attribute = trajectory_data.qpos
    result = TrajectoryData._get_single_attribute(
        attribute, split_points, traj_index, sub_traj_index, backend_type
    )

    start_idx = split_points[traj_index] + sub_traj_index
    expected_value = backend_type.squeeze(attribute[start_idx].copy())

    assert np.allclose(
        result, expected_value
    ), f"Expected {expected_value} but got {result}"


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_dynamic_slice_in_dim_single(backend, input_trajectory_data):
    trajectory_data: TrajectoryData = input_trajectory_data(backend)

    backend_type = jnp if backend == "jax" else np

    attribute = trajectory_data.site_xpos
    split_points = trajectory_data.split_points
    traj_index = 0
    sub_traj_index = 0
    slice_length = 5

    slice = trajectory_data._dynamic_slice_in_dim_single(
        attribute, split_points, traj_index, sub_traj_index, slice_length, backend_type
    )

    start_idx = split_points[traj_index]
    slice_start = start_idx + sub_traj_index
    if backend == "jax":
        expected_slice = lax.dynamic_slice_in_dim(
            trajectory_data.site_xpos, slice_start, slice_length
        )
    else:
        expected_slice = trajectory_data.site_xpos[
            slice_start : slice_start + slice_length
        ].copy()

    assert np.allclose(
        slice, expected_slice
    ), f"Failed for backend {backend_type}. Sliced data: {slice}, Expected: {expected_slice}"


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_data_add_joint(backend, input_trajectory_data):
    trajectory_data: TrajectoryData = input_trajectory_data(backend)

    backend_type = jnp if backend == "jax" else np

    original_qpos_shape = trajectory_data.qpos.shape
    original_qvel_shape = trajectory_data.qvel.shape

    new_qpos_value = 1.0
    new_qvel_value = 2.0
    updated_trajectory_data = trajectory_data.add_joint(
        new_qpos_value, new_qvel_value, backend_type
    )

    updated_qpos_shape = updated_trajectory_data.qpos.shape
    updated_qvel_shape = updated_trajectory_data.qvel.shape

    assert updated_qpos_shape == (original_qpos_shape[0], original_qpos_shape[1] + 1)
    assert updated_qvel_shape == (original_qvel_shape[0], original_qvel_shape[1] + 1)

    # Check that the last column contains the new values
    assert np.allclose(
        updated_trajectory_data.qpos[:, -1],
        backend_type.full((original_qpos_shape[0],), new_qpos_value),
    )
    assert np.allclose(
        updated_trajectory_data.qvel[:, -1],
        backend_type.full((original_qvel_shape[0],), new_qvel_value),
    )


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_data_add_body(backend, input_trajectory_data):
    trajectory_data: TrajectoryData = input_trajectory_data(backend)

    backend_type = jnp if backend == "jax" else np

    original_xpos_shape = trajectory_data.xpos.shape
    original_xquat_shape = trajectory_data.xquat.shape
    original_cvel_shape = trajectory_data.cvel.shape
    original_subtree_com_shape = trajectory_data.subtree_com.shape

    new_xpos_value = 1.0
    new_cvel_value = 2.0
    new_subtree_com_value = 3.0

    updated_trajectory_data: TrajectoryData = trajectory_data.add_body(
        new_xpos_value, new_cvel_value, new_subtree_com_value, backend_type
    )

    updated_xpos_shape = updated_trajectory_data.xpos.shape
    updated_xquat_shape = updated_trajectory_data.xquat.shape
    updated_cvel_shape = updated_trajectory_data.cvel.shape
    updated_subtree_com_shape = updated_trajectory_data.subtree_com.shape

    assert updated_xpos_shape == (
        original_xpos_shape[0],
        original_xpos_shape[1] + 1,
        original_xpos_shape[2],
    )
    assert updated_xquat_shape == (
        original_xquat_shape[0],
        original_xquat_shape[1] + 1,
        original_xquat_shape[2],
    )
    assert updated_cvel_shape == (
        original_cvel_shape[0],
        original_cvel_shape[1] + 1,
        original_cvel_shape[2],
    )
    assert updated_subtree_com_shape == (
        original_subtree_com_shape[0],
        original_subtree_com_shape[1] + 1,
        original_subtree_com_shape[2],
    )

    assert np.allclose(
        updated_trajectory_data.xpos[:, -1, :],
        backend_type.full((original_xpos_shape[0], 1, 3), new_xpos_value),
    )

    assert np.allclose(
        updated_trajectory_data.cvel[:, -1, :],
        backend_type.full((original_cvel_shape[0], 1, 6), new_cvel_value),
    )

    assert np.allclose(
        updated_trajectory_data.subtree_com[:, -1, :],
        backend_type.full((original_subtree_com_shape[0], 1, 3), new_subtree_com_value),
    )


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_data_add_site(backend, input_trajectory_data):
    trajectory_data: TrajectoryData = input_trajectory_data(backend)

    backend_type = jnp if backend == "jax" else np

    original_site_xpos_shape = trajectory_data.site_xpos.shape
    original_site_xmat_shape = trajectory_data.site_xmat.shape

    new_site_xpos_value = 1.0
    updated_trajectory_data: TrajectoryData = trajectory_data.add_site(
        new_site_xpos_value, backend_type
    )

    updated_site_xpos_shape = updated_trajectory_data.site_xpos.shape
    updated_site_xmat_shape = updated_trajectory_data.site_xmat.shape

    assert updated_site_xpos_shape == (
        original_site_xpos_shape[0],
        original_site_xpos_shape[1] + 1,
        original_site_xpos_shape[2],
    )

    assert updated_site_xmat_shape == (
        original_site_xmat_shape[0],
        original_site_xmat_shape[1] + 1,
        original_site_xmat_shape[2],
    )

    assert np.allclose(
        updated_trajectory_data.site_xpos[:, -1, :],
        backend_type.full((original_site_xpos_shape[0], 1, 3), new_site_xpos_value),
    )


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_data_remove_joint(backend, input_trajectory_data):
    trajectory_data: TrajectoryData = input_trajectory_data(backend)

    backend_type = jnp if backend == "jax" else np

    original_qpos_shape = trajectory_data.qpos.shape
    original_qvel_shape = trajectory_data.qvel.shape

    if original_qpos_shape[1] < 1 or original_qvel_shape[1] < 1:
        pytest.skip("Not enough joints to remove")

    joint_qpos_ids = backend_type.array([original_qpos_shape[1] - 1])
    joint_qvel_ids = backend_type.array([original_qvel_shape[1] - 1])

    updated_trajectory_data = trajectory_data.remove_joints(
        joint_qpos_ids, joint_qvel_ids, backend_type
    )

    updated_qpos_shape = updated_trajectory_data.qpos.shape
    updated_qvel_shape = updated_trajectory_data.qvel.shape

    assert updated_qpos_shape == (original_qpos_shape[0], original_qpos_shape[1] - 1)
    assert updated_qvel_shape == (original_qvel_shape[0], original_qvel_shape[1] - 1)

    if original_qpos_shape[1] < 2 or original_qvel_shape[1] < 2:
        pytest.skip("Not enough joints to remove")
    # Case 2: Remove two joints (e.g., the last two joints)
    joint_qpos_ids = backend_type.array(
        [original_qpos_shape[1] - 2, original_qpos_shape[1] - 1]
    )
    joint_qvel_ids = backend_type.array(
        [original_qvel_shape[1] - 2, original_qvel_shape[1] - 1]
    )

    updated_trajectory_data = trajectory_data.remove_joints(
        joint_qpos_ids, joint_qvel_ids, backend_type
    )

    updated_qpos_shape = updated_trajectory_data.qpos.shape
    updated_qvel_shape = updated_trajectory_data.qvel.shape

    assert updated_qpos_shape == (original_qpos_shape[0], original_qpos_shape[1] - 2)
    assert updated_qvel_shape == (original_qvel_shape[0], original_qvel_shape[1] - 2)


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_data_remove_body(backend, input_trajectory_data):
    trajectory_data: TrajectoryData = input_trajectory_data(backend)

    backend_type = jnp if backend == "jax" else np

    original_xpos_shape = trajectory_data.xpos.shape
    original_xquat_shape = trajectory_data.xquat.shape
    original_cvel_shape = trajectory_data.cvel.shape
    original_subtree_com_shape = trajectory_data.subtree_com.shape

    # todo: this statement is not needed, we should not skip.
    if (
        original_xpos_shape[1] < 1
        or original_xquat_shape[1] < 1
        or original_cvel_shape[1] < 1
        or original_subtree_com_shape[1] < 1
    ):
        pytest.skip("Not enough bodies to remove")

    body_ids = backend_type.array([original_xpos_shape[1] - 1])

    updated_trajectory_data = trajectory_data.remove_bodies(body_ids, backend_type)

    updated_xpos_shape = updated_trajectory_data.xpos.shape
    updated_xquat_shape = updated_trajectory_data.xquat.shape
    updated_cvel_shape = updated_trajectory_data.cvel.shape
    updated_subtree_com_shape = updated_trajectory_data.subtree_com.shape

    assert updated_xpos_shape == (
        original_xpos_shape[0],
        original_xpos_shape[1] - 1,
        original_xpos_shape[2],
    )
    assert updated_xquat_shape == (
        original_xquat_shape[0],
        original_xquat_shape[1] - 1,
        original_xquat_shape[2],
    )
    assert updated_cvel_shape == (
        original_cvel_shape[0],
        original_cvel_shape[1] - 1,
        original_cvel_shape[2],
    )
    assert updated_subtree_com_shape == (
        original_subtree_com_shape[0],
        original_subtree_com_shape[1] - 1,
        original_subtree_com_shape[2],
    )

    # Case 2: Remove two bodies (e.g., the last two bodies)
    if (
        original_xpos_shape[1] < 2
        or original_xquat_shape[1] < 2
        or original_cvel_shape[1] < 2
        or original_subtree_com_shape[1] < 2
    ):
        pytest.skip("Not enough bodies to remove")

    body_ids = backend_type.array(
        [original_xpos_shape[1] - 2, original_xpos_shape[1] - 1]
    )

    updated_trajectory_data = trajectory_data.remove_bodies(body_ids, backend_type)

    updated_xpos_shape = updated_trajectory_data.xpos.shape
    updated_xquat_shape = updated_trajectory_data.xquat.shape
    updated_cvel_shape = updated_trajectory_data.cvel.shape
    updated_subtree_com_shape = updated_trajectory_data.subtree_com.shape

    assert updated_xpos_shape == (
        original_xpos_shape[0],
        original_xpos_shape[1] - 2,
        original_xpos_shape[2],
    )
    assert updated_xquat_shape == (
        original_xquat_shape[0],
        original_xquat_shape[1] - 2,
        original_xquat_shape[2],
    )
    assert updated_cvel_shape == (
        original_cvel_shape[0],
        original_cvel_shape[1] - 2,
        original_cvel_shape[2],
    )
    assert updated_subtree_com_shape == (
        original_subtree_com_shape[0],
        original_subtree_com_shape[1] - 2,
        original_subtree_com_shape[2],
    )


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_data_remove_site(backend, input_trajectory_data):
    trajectory_data: TrajectoryData = input_trajectory_data(backend)

    backend_type = jnp if backend == "jax" else np

    original_site_xpos_shape = trajectory_data.site_xpos.shape
    original_site_xmat_shape = trajectory_data.site_xmat.shape

    if original_site_xpos_shape[1] < 1 or original_site_xmat_shape[1] < 1:
        pytest.skip("Not enough sites to remove")

    # Case 1: Remove the last site
    site_ids = backend_type.array([original_site_xpos_shape[1] - 1])

    updated_trajectory_data = trajectory_data.remove_sites(site_ids, backend_type)

    updated_site_xpos_shape = updated_trajectory_data.site_xpos.shape
    updated_site_xmat_shape = updated_trajectory_data.site_xmat.shape

    assert updated_site_xpos_shape == (
        original_site_xpos_shape[0],
        original_site_xpos_shape[1] - 1,
        original_site_xpos_shape[2],
    )
    assert updated_site_xmat_shape == (
        original_site_xmat_shape[0],
        original_site_xmat_shape[1] - 1,
        original_site_xmat_shape[2],
    )

    # Case 2: Remove two sites
    if original_site_xpos_shape[1] < 2 or original_site_xmat_shape[1] < 2:
        pytest.skip("Not enough sites to remove")

    site_ids = backend_type.array(
        [original_site_xpos_shape[1] - 2, original_site_xpos_shape[1] - 1]
    )

    updated_trajectory_data = trajectory_data.remove_sites(site_ids, backend_type)

    updated_site_xpos_shape = updated_trajectory_data.site_xpos.shape
    updated_site_xmat_shape = updated_trajectory_data.site_xmat.shape

    assert updated_site_xpos_shape == (
        original_site_xpos_shape[0],
        original_site_xpos_shape[1] - 2,
        original_site_xpos_shape[2],
    )
    assert updated_site_xmat_shape == (
        original_site_xmat_shape[0],
        original_site_xmat_shape[1] - 2,
        original_site_xmat_shape[2],
    )


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_data_reorder_joints(backend, input_trajectory_data):
    trajectory_data: TrajectoryData = input_trajectory_data(backend)

    backend_type = jnp if backend == "jax" else np

    original_qpos_shape = trajectory_data.qpos.shape
    original_qvel_shape = trajectory_data.qvel.shape

    new_order_qpos = backend_type.array(list(reversed(range(original_qpos_shape[1]))))
    new_order_qvel = backend_type.array(list(reversed(range(original_qvel_shape[1]))))

    updated_trajectory_data = trajectory_data.reorder_joints(
        new_order_qpos, new_order_qvel
    )

    qpos_ind = np.arange(original_qpos_shape[1])
    qvel_ind = np.arange(original_qvel_shape[1])
    assert np.array_equal(
        updated_trajectory_data.qpos[:, qpos_ind], trajectory_data.qpos[:, new_order_qpos[qpos_ind]]
    )
    assert np.array_equal(
        updated_trajectory_data.qpos[:, qvel_ind], trajectory_data.qpos[:, new_order_qpos[qvel_ind]]
    )


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_data_reorder_bodies(backend, input_trajectory_data):
    trajectory_data: TrajectoryData = input_trajectory_data(backend)
    backend_type = jnp if backend == "jax" else np

    original_xpos_shape = trajectory_data.xpos.shape

    new_order = backend_type.array(list(reversed(range(original_xpos_shape[1]))))
    updated_trajectory_data = trajectory_data.reorder_bodies(new_order)

    body_ind = np.arange(original_xpos_shape[1])
    assert np.array_equal(
        updated_trajectory_data.xpos[:, body_ind], trajectory_data.xpos[:, new_order[body_ind]]
    )
    assert np.array_equal(
        updated_trajectory_data.xquat[:, body_ind], trajectory_data.xquat[:, new_order[body_ind]]
    )
    assert np.array_equal(
        updated_trajectory_data.cvel[:, body_ind], trajectory_data.cvel[:, new_order[body_ind]]
    )
    assert np.array_equal(
        updated_trajectory_data.subtree_com[:, body_ind],
        trajectory_data.subtree_com[:, new_order[body_ind]],
    )


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_data_reorder_sites(backend, input_trajectory_data):
    trajectory_data: TrajectoryData = input_trajectory_data(backend)

    backend_type = jnp if backend == "jax" else np

    original_site_xpos_shape = trajectory_data.site_xpos.shape

    new_order = backend_type.array(list(reversed(range(original_site_xpos_shape[1]))))

    updated_trajectory_data = trajectory_data.reorder_sites(new_order)

    # todo: do the same update as done for body and joint
    assert np.array_equal(
        updated_trajectory_data.site_xpos[:, 0],
        trajectory_data.site_xpos[:, new_order[0]],
    )
    assert np.array_equal(
        updated_trajectory_data.site_xpos[:, 1],
        trajectory_data.site_xpos[:, new_order[1]],
    )
    assert np.array_equal(
        updated_trajectory_data.site_xpos[:, -1],
        trajectory_data.site_xpos[:, new_order[-1]],
    )

    assert np.array_equal(
        updated_trajectory_data.site_xmat[:, 0],
        trajectory_data.site_xmat[:, new_order[0]],
    )
    assert np.array_equal(
        updated_trajectory_data.site_xmat[:, 1],
        trajectory_data.site_xmat[:, new_order[1]],
    )
    assert np.array_equal(
        updated_trajectory_data.site_xmat[:, -1],
        trajectory_data.site_xmat[:, new_order[-1]],
    )


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_data_concatenate(
    backend, input_trajectory_data, input_trajectory_info_data
):
    trajectory_data_factory = input_trajectory_data(backend)
    trajectory_info_factory = input_trajectory_info_data(backend)

    backend_type = jnp if backend == "jax" else np

    traj_data1 = trajectory_data_factory
    traj_data2 = trajectory_data_factory
    traj_info1 = trajectory_info_factory
    traj_info2 = trajectory_info_factory

    concatenated_traj_data, concatenated_traj_info = TrajectoryData.concatenate(
        [traj_data1, traj_data2], [traj_info1, traj_info2], backend_type
    )

    assert concatenated_traj_data.qpos.shape == (
        traj_data1.qpos.shape[0] + traj_data2.qpos.shape[0],
        traj_data1.qpos.shape[1],
    )
    assert concatenated_traj_data.qvel.shape == (
        traj_data1.qvel.shape[0] + traj_data2.qvel.shape[0],
        traj_data1.qvel.shape[1],
    )
    assert concatenated_traj_data.xpos.shape == (
        traj_data1.xpos.shape[0] + traj_data2.xpos.shape[0],
        traj_data1.xpos.shape[1],
        traj_data1.xpos.shape[2],
    )
    assert concatenated_traj_data.xquat.shape == (
        traj_data1.xquat.shape[0] + traj_data2.xquat.shape[0],
        traj_data1.xquat.shape[1],
        traj_data1.xquat.shape[2],
    )
    assert concatenated_traj_data.cvel.shape == (
        traj_data1.cvel.shape[0] + traj_data2.cvel.shape[0],
        traj_data1.cvel.shape[1],
        traj_data1.cvel.shape[2],
    )
    assert concatenated_traj_data.subtree_com.shape == (
        traj_data1.subtree_com.shape[0] + traj_data2.subtree_com.shape[0],
        traj_data1.subtree_com.shape[1],
        traj_data1.subtree_com.shape[2],
    )
    assert concatenated_traj_data.site_xpos.shape == (
        traj_data1.site_xpos.shape[0] + traj_data2.site_xpos.shape[0],
        traj_data1.site_xpos.shape[1],
        traj_data1.site_xpos.shape[2],
    )
    assert concatenated_traj_data.site_xmat.shape == (
        traj_data1.site_xmat.shape[0] + traj_data2.site_xmat.shape[0],
        traj_data1.site_xmat.shape[1],
        traj_data1.site_xmat.shape[2],
    )

    expected_split_points = backend_type.array(
        [
            0,
            traj_data1.qpos.shape[0],
            traj_data1.qpos.shape[0] + traj_data2.qpos.shape[0],
        ]
    )

    assert backend_type.allclose(
        concatenated_traj_data.split_points, expected_split_points
    )


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_data_len_trajectory(backend, input_trajectory_data):
    trajectory_data: TrajectoryData = input_trajectory_data(backend)

    # todo: this and the next test should be done by also adapting the data in traj data. There will be a checking for
    # split points implemented soon, and this will throw and error.

    backend_type = jnp if backend == "jax" else np

    split_points = backend_type.array([0, 100, 300, 600])
    trajectory_data = trajectory_data.replace(split_points=split_points)

    traj_len_0 = trajectory_data.len_trajectory(0)
    assert traj_len_0 == 100, f"Expected 100, got {traj_len_0}"

    traj_len_1 = trajectory_data.len_trajectory(1)
    assert traj_len_1 == 200, f"Expected 200, got {traj_len_1}"

    traj_len_2 = trajectory_data.len_trajectory(2)
    assert traj_len_2 == 300, f"Expected 300, got {traj_len_2}"


@pytest.mark.parametrize("backend", ["jax", "numpy"])
def test_trajectory_data_n_samples(backend, input_trajectory_data):
    trajectory_data: TrajectoryData = input_trajectory_data(backend)

    backend_type = jnp if backend == "jax" else np

    split_points = backend_type.array([0, 100, 300, 600])
    trajectory_data = trajectory_data.replace(split_points=split_points)

    n_samples = trajectory_data.n_samples
    assert n_samples == 600, f"Expected 600, got {n_samples}"


def test_trajectory_data_get_attribute_names():
    attribute_names = TrajectoryData.get_attribute_names()

    expected_attributes = [
        "qpos",
        "qvel",
        "xpos",
        "xquat",
        "cvel",
        "subtree_com",
        "site_xpos",
        "site_xmat",
        "userdata",
        "split_points",
    ]

    assert set(attribute_names) == set(
        expected_attributes
    ), f"Attributes mismatch. Got {attribute_names}"


@pytest.mark.parametrize("backend", ["jax"])
def test_trajectory_data_to_numpy(backend, input_trajectory_data):
    trajectory_data: TrajectoryData = input_trajectory_data(backend)

    numpy_trajectory_data = trajectory_data.to_numpy()

    # Verify all fields are numpy arrays
    for field_name in TrajectoryData.get_attribute_names():
        value = getattr(numpy_trajectory_data, field_name)
        assert isinstance(value, np.ndarray), f"{field_name} is not a numpy array"


@pytest.mark.parametrize("backend", ["numpy"])
def test_trajectory_data_to_jax(backend, input_trajectory_data):
    trajectory_data: TrajectoryData = input_trajectory_data(backend)

    jax_trajectory_data = trajectory_data.to_jax()

    for field_name in TrajectoryData.get_attribute_names():
        value = getattr(jax_trajectory_data, field_name)
        assert isinstance(value, jax.Array), f"{field_name} is not a JAX array"


@pytest.mark.parametrize("backend", ["numpy", "jax"])
def test_interpolate_trajectories_basic(
    input_trajectory_data, input_trajectory_info_data, backend
):
    traj_data: TrajectoryData = input_trajectory_data(backend)
    traj_info: TrajectoryInfo = input_trajectory_info_data(backend)

    new_frequency = traj_info.frequency * 2

    new_traj_data, new_traj_info = interpolate_trajectories(
        traj_data, traj_info, new_frequency
    )

    assert new_traj_info.frequency == new_frequency

    scaling_factor = new_frequency / traj_info.frequency
    expected_n_samples = round(traj_data.n_samples * scaling_factor)
    assert new_traj_data.n_samples == expected_n_samples

    assert new_traj_data.qpos.shape[0] == expected_n_samples
    assert new_traj_data.qvel.shape[0] == expected_n_samples
    assert new_traj_data.xquat.shape[0] == expected_n_samples


@pytest.mark.parametrize("backend", ["numpy", "jax"])
def test_interpolate_trajectories_quaternions(
    input_trajectory_data, input_trajectory_info_data, backend
):
    traj_data: TrajectoryData = input_trajectory_data(backend)
    traj_info: TrajectoryInfo = input_trajectory_info_data(backend)

    backend_type = jnp if backend == "jax" else np

    new_frequency = traj_info.frequency * 2

    new_traj_data, _ = interpolate_trajectories(
        traj_data, traj_info, new_frequency, backend_type
    )

    norms = backend_type.linalg.norm(new_traj_data.xquat, axis=-1)
    assert np.allclose(
        norms, 1.0, atol=1e-6
    ), "Interpolated quaternions are not normalized"


@pytest.mark.parametrize("backend", ["numpy"])
def test_trajectory_transitions_to_jnp(backend, input_trajectory_transitions):
    trajectory_transitions: TrajectoryTransitions = input_trajectory_transitions(
        backend
    )

    jnp_transitions = trajectory_transitions.to_jnp()

    assert isinstance(jnp_transitions.observations, jax.Array)
    assert isinstance(jnp_transitions.next_observations, jax.Array)
    assert isinstance(jnp_transitions.absorbings, jax.Array)
    assert isinstance(jnp_transitions.dones, jax.Array)
    assert isinstance(jnp_transitions.actions, jax.Array)
    assert isinstance(jnp_transitions.rewards, jax.Array)


@pytest.mark.parametrize("backend", ["jax"])
def test_trajectory_transitions_to_np(backend, input_trajectory_transitions):
    trajectory_transitions: TrajectoryTransitions = input_trajectory_transitions(
        backend
    )

    np_transitions = trajectory_transitions.to_np()

    assert isinstance(np_transitions.observations, np.ndarray)
    assert isinstance(np_transitions.next_observations, np.ndarray)
    assert isinstance(np_transitions.absorbings, np.ndarray)
    assert isinstance(np_transitions.dones, np.ndarray)
    assert isinstance(np_transitions.actions, np.ndarray)
    assert isinstance(np_transitions.rewards, np.ndarray)


def test_trajectory_transitions_get_attribute_names():
    attribute_names = TrajectoryTransitions.get_attribute_names()
    expected_names = [
        "observations",
        "next_observations",
        "absorbings",
        "dones",
        "actions",
        "rewards",
    ]
    assert attribute_names == expected_names
