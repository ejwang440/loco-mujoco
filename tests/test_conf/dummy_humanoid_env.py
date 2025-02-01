from pathlib import Path
import mujoco
from mujoco import MjSpec
from mujoco import mjx

import jax
import jax.numpy as jnp
import numpy as np

from loco_mujoco.environments import LocoEnv
from loco_mujoco.core.observations import ObservationType
from loco_mujoco.core.utils import info_property

from loco_mujoco.trajectory import TrajectoryTransitions

from copy import deepcopy
from dataclasses import replace


class DummyHumamoidEnv(LocoEnv):

    def __init__(self, observation_spec=None, actuation_spec=None, spec=None, **kwargs):

        # load the model specification
        if spec is None:
            spec = self.get_default_xml_file_path()

        spec = mujoco.MjSpec.from_file(spec)

        # get the observation and action specification
        if observation_spec is None:
            # get default
            observation_spec = self._get_observation_specification(spec)
        else:
            # parse
            observation_spec = self.parse_observation_spec(observation_spec)
        if actuation_spec is None:
            actuation_spec = self._get_action_specification(spec)

        self._using_jax = kwargs["enable_mjx"]

        super(DummyHumamoidEnv, self).__init__(spec, actuation_spec, observation_spec, **kwargs)

    @staticmethod
    def _get_observation_specification(spec: MjSpec):
        """
        Returns the observation specification of the environment.

        Args:
            spec (MjSpec): Specification of the environment.

        Returns:
            A list of observation types.
        """
        observation_spec = [
            # ------------- JOINT POS -------------
            ObservationType.FreeJointPosNoXY("q_root", xml_name="root"),
            ObservationType.JointPos("q_abdomen_z", xml_name="abdomen_z"),

            # ------------- JOINT VEL -------------
            ObservationType.FreeJointVel("dq_root", xml_name="root"),
            ObservationType.JointVel("dq_abdomen_z", xml_name="abdomen_z"),

            # ------------- BODIES -------------
            ObservationType.BodyPos("left_thigh_obs_pos", xml_name="left_thigh"),
            ObservationType.BodyVel("left_thigh_obs_vel", xml_name="left_thigh"),

        ]

        return observation_spec

    @staticmethod
    def _get_action_specification(spec: MjSpec):
        action_spec = ["abdomen_y", "right_knee"]
        return action_spec

    @classmethod
    def get_default_xml_file_path(cls):
        return (Path(__file__).resolve().parent / "humanoid_test.xml").as_posix()

    @info_property
    def sites_for_mimic(self):
        return ["torso_site", "pelvis_site", "right_thigh_site", "right_foot_site", "left_thigh_site",
                "left_foot_site"]

    @info_property
    def root_body_name(self):
        return "torso"

    @info_property
    def goal_visualization_arrow_offset(self):
        return [0, 0, 0.6]

    @info_property
    def grf_size(self):
        return 6

    @info_property
    def upper_body_xml_name(self):
        return "torso_link"

    @info_property
    def root_free_joint_xml_name(self):
        return "root"

    @info_property
    def root_height_healthy_range(self):
        return (0.6, 1.5)

    def generate_trajectory_from_nominal(self, nominal_traj, horizon=None, rng_key=None):
        if self.th is None:
            raise ValueError("No trajectory was passed to the environment. "
                             "To create a dataset pass a trajectory first.")

        if self.th.traj.transitions is None:
            # create new trajectory and trajectory handler
            th = deepcopy(self.th)

            # set trajectory handler and store old one for later
            orig_th = self.th
            self.th = th

            # get a new model and data
            model = self.mjspec.compile()
            data = mujoco.MjData(model)
            mujoco.mj_resetData(model, data)

            # setup containers for the dataset
            all_observations, all_next_observations, all_rewards, all_absorbing, all_dones = [], [], [], [], []

            if rng_key is None:
                rng_key = jax.random.key(0)

            for i in range(self.th.n_trajectories):

                # set configuration to the first state of the current trajectory
                self.th.fixed_start_conf = (i, 0)

                # do a reset
                key, subkey = jax.random.split(rng_key)
                traj_data_single = nominal_traj.data.get(i, 0, np)  # get first sample
                carry = self._init_additional_carry(key, model, data, np)

                # set data from traj_data (qpos and qvel) and forward to calculate other kinematic entities.
                mujoco.mj_resetData(model, data)
                data = self.set_sim_state_from_traj_data(data, traj_data_single, carry)
                mujoco.mj_forward(model, data)

                data, carry = self._reset_init_data_and_model(model, data, carry)
                data, carry = (
                    self.obs_container.reset_state(self, model, data, carry, np))
                obs, carry = self._create_observation(model, data, carry)
                info = self._reset_info_dictionary(obs, data, subkey)

                # initiate episode containers
                observations = [obs]
                rewards = []
                absorbing_flags = []

                if horizon is None:
                    t_max = nominal_traj.data.len_trajectory(i)
                else:
                    t_max = horizon

                for j in range(1, t_max):
                    # get next sample and calculate forward dynamics
                    traj_data_single = nominal_traj.data.get(i, j, np)  # get next sample
                    data = self.set_sim_state_from_traj_data(data, traj_data_single, carry)
                    mujoco.mj_forward(model, data)

                    data, carry = self._simulation_post_step(model, data, carry)
                    obs, carry = self._create_observation(model, data, carry)
                    obs, data, info, carry = (
                        self._step_finalize(obs, model, data, info, carry))
                    observations.append(obs)

                    # check if the current state is an absorbing state
                    is_absorbing, carry = self._is_absorbing(obs, info, data, carry)
                    absorbing_flags.append(is_absorbing)

                    # compute reward
                    action = np.zeros(self.info.action_space.shape)
                    reward, carry = self._reward(obs, action, obs, is_absorbing, info, model, data, carry)
                    rewards.append(reward)

                observations = np.vstack(observations)
                all_observations.append(observations[:-1])
                all_next_observations.append(observations[1:])
                all_rewards.append(rewards)
                all_absorbing.append(absorbing_flags)
                dones = np.zeros(observations.shape[0]-1)
                dones[-1] = 1
                all_dones.append(dones)

            all_observations = np.concatenate(all_observations).astype(np.float32)
            all_next_observations = np.concatenate(all_next_observations).astype(np.float32)
            all_rewards = np.concatenate(all_rewards).astype(np.float32)
            all_dones = np.concatenate(all_dones).astype(np.float32)
            all_absorbing = np.concatenate(all_absorbing).astype(np.float32)

            transitions = TrajectoryTransitions(np.array(all_observations),
                                                np.array(all_next_observations),
                                                np.array(all_absorbing),
                                                np.array(all_dones),
                                                rewards=all_rewards
                                                )

            self.th = orig_th
            self.th.traj = replace(self.th.traj, transitions=transitions)

        return self.th.traj.transitions

    def mjx_generate_trajectory_from_nominal(self, nominal_traj, horizon=None, rng_key=None):

        def _mjx_step(data, info, carry, traj_ind, sub_traj_ind):

            # get next sample and calculate forward dynamics
            traj_data_single = nominal_traj.data.get(traj_ind, sub_traj_ind, jnp)  # get next sample
            data = self.mjx_set_sim_state_from_traj_data(data, traj_data_single, carry)
            data = mjx.forward(sys, data)

            data, carry = self._mjx_simulation_post_step(model, data, carry)
            obs, carry = self._mjx_create_observation(model, data, carry)
            obs, data, info, carry = (
                self._mjx_step_finalize(obs, model, data, info, carry))

            # check if the current state is an absorbing state
            absorbing, carry = self._is_absorbing(obs, info, data, carry)

            # compute reward
            action = jnp.zeros(self.info.action_space.shape)
            reward, carry = self._mjx_reward(obs, action, obs, absorbing, info, model, data, carry)

            return obs, reward, absorbing, action, data, info, carry

        if self.th is None:
            raise ValueError("No trajectory was passed to the environment. "
                             "To create a dataset pass a trajectory first.")

        if self.th.traj.transitions is None:
            # create new trajectory and trajectory handler
            th = deepcopy(self.th)

            # set trajectory handler and store old one for later
            orig_th = self.th
            self.th = th

            # get a new model and data
            model = self.mjspec.compile()
            data = mujoco.MjData(model)
            mujoco.mj_resetData(model, data)
            sys = mjx.put_model(model)
            data = mjx.put_data(model, data)
            first_data = mjx.forward(sys, data)

            # setup containers for the dataset
            all_observations, all_next_observations, all_rewards, all_absorbing, all_dones = [], [], [], [], []

            # compile mjx_step function
            mjx_step = jax.jit(_mjx_step)

            if rng_key is None:
                rng_key = jax.random.key(0)

            for i in range(self.th.n_trajectories):

                # set configuration to the first state of the current trajectory
                self.th.fixed_start_conf = (i, 0)

                # do a reset
                data = first_data

                key, subkey = jax.random.split(rng_key)
                traj_data_single = nominal_traj.data.get(i, 0, jnp)  # get first sample
                carry = self._init_additional_carry(key, model, data, jnp)

                # set data from traj_data (qpos and qvel) and forward to calculate other kinematic entities.
                data = self.mjx_set_sim_state_from_traj_data(data, traj_data_single, carry)
                data = mjx.forward(sys, data)

                data, carry = self._mjx_reset_init_data_and_model(model, data, carry)
                data, carry = (
                    self.obs_container.reset_state(self, model, data, carry, jnp))
                obs, carry = self._mjx_create_observation(model, data, carry)
                info = self._reset_info_dictionary(obs, data, subkey)

                # initiate episode containers
                observations = [obs]
                rewards = []
                absorbing_flags = []

                if horizon is None:
                    t_max = nominal_traj.data.len_trajectory(i)
                else:
                    t_max = horizon

                for j in range(1, t_max):

                    obs, reward, absorbing, action, data, info, carry = mjx_step(data, info, carry, i, j)
                    observations.append(obs)
                    rewards.append(reward)
                    absorbing_flags.append(absorbing)

                observations = jnp.vstack(observations)
                all_observations.append(observations[:-1])
                all_next_observations.append(observations[1:])
                all_rewards.append(jnp.hstack(rewards))
                all_absorbing.append(jnp.hstack(absorbing_flags))
                dones = jnp.zeros(observations.shape[0]-1)
                all_dones.append(dones)

            all_observations = jnp.concatenate(all_observations).astype(np.float32)
            all_next_observations = jnp.concatenate(all_next_observations).astype(np.float32)
            all_rewards = jnp.concatenate(all_rewards).astype(np.float32)
            all_dones = jnp.concatenate(all_dones).astype(np.float32)
            all_absorbing = jnp.concatenate(all_absorbing).astype(np.float32)

            transitions = TrajectoryTransitions(jnp.array(all_observations),
                                                jnp.array(all_next_observations),
                                                jnp.array(all_absorbing),
                                                jnp.array(all_dones),
                                                rewards=all_rewards
                                                )

            self.th = orig_th
            self.th.traj = replace(self.th.traj, transitions=transitions)

        return self.th.traj.transitions
