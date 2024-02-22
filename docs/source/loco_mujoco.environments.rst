.. _env-label:
Overview of Environments and Tasks
=================================

Here you can find an overview of all tasks. Each Task is represented by its own ID. For each task, you can choose between
different datasets. The real dataset contains real (noisy) motion capture datasets without actions. The perfect dataset
contains ground truth states and actions form an expert policy. The preference dataset
contains preferences of an ground truth expert with states and action (only available on an few tasks). The status of a
dataset can be seen down below. ✅ means it is already available, and 🔶 means pending.

.. note::
    The **perfect** and **preference** datasets are only available for the *default* settings of an environment.
    By default, arms are not included in the observation space. Hence, these datasets are only available
    for tasks without arms. In comparison, the real dataset also contains arm observations.

.. list-table::
   :widths: 25 30 15 30
   :header-rows: 1

   * - **Image**
     - **Task-IDs**
     - **Status of Datasets**
     - **Description**
   * - .. image:: https://github.com/robfiras/loco-mujoco/assets/69359729/cdcd4617-c18a-448d-b42a-ea01384016b0
     - | HumanoidMuscle.walk
       | HumanoidMuscle.run
       | HumanoidMuscle4Ages.walk.4
       | HumanoidMuscle.run
       | HumanoidMuscle4Ages.run.4
     - | real: ✅
       | perfect: ✅
       | preference: 🔶
     -  Task of an adult **Muscle** Humanoid
        Walking or Running Straight.
   * - .. image:: https://github.com/robfiras/loco-mujoco/assets/69359729/1bdebeb1-401c-439e-8f2e-7197fd34c5e5
     - | HumanoidMuscle4Ages.walk.3
       | HumanoidMuscle4Ages.run.3
     - | real: ✅
       | perfect: 🔶
       | preference: 🔶
     -  Task of a (~12 year old) **Muscle** Humanoid Walking or Running Straight.
   * - .. image:: https://github.com/robfiras/loco-mujoco/assets/69359729/2c7aeb58-65a6-427c-8b12-197c96410cd8
     - | HumanoidMuscle4Ages.walk.2
       | HumanoidMuscle4Ages.run.2
     - | real: ✅
       | perfect: 🔶
       | preference: 🔶
     -  Task of a (~5-6 year old) **Muscle** Humanoid Walking or Running Straight.
   * - .. image:: https://github.com/robfiras/loco-mujoco/assets/69359729/600a917f-c784-4b5e-ac99-9472711de843
     - | HumanoidMuscle4Ages.walk.1
       | HumanoidMuscle4Ages.run.1
     - | real: ✅
       | perfect: 🔶
       | preference: 🔶
     -  Task of a (~2 year old) **Muscle** Humanoid Walking or Running Straight.
   * - .. image:: https://github.com/robfiras/loco-mujoco/assets/69359729/cf32520f-5a2e-401a-9f2e-b8033ef7109c
     - | HumanoidMuscle.walk
       | HumanoidMuscle.run
       | HumanoidMuscle4Ages.walk.4
       | HumanoidMuscle.run
       | HumanoidMuscle4Ages.run.4
     - | real: ✅
       | perfect: ✅
       | preference: 🔶
     -  Task of an adult **Torque** Humanoid
        Walking or Running Straight.
   * - .. image:: https://github.com/robfiras/loco-mujoco/assets/69359729/352f3594-8903-4eaf-a223-f751b590f4ec
     - | HumanoidMuscle4Ages.walk.3
       | HumanoidMuscle4Ages.run.3
     - | real: ✅
       | perfect: 🔶
       | preference: 🔶
     -  Task of a (~12 year old) **Torque** Humanoid Walking or Running Straight.
   * - .. image:: https://github.com/robfiras/loco-mujoco/assets/69359729/06c83af9-3c45-43a1-8173-aa1d8771fe4c
     - | HumanoidMuscle4Ages.walk.2
       | HumanoidMuscle4Ages.run.2
     - | real: ✅
       | perfect: 🔶
       | preference: 🔶
     -  Task of a (~5-6 year old) **Torque** Humanoid Walking or Running Straight.
   * - .. image:: https://github.com/robfiras/loco-mujoco/assets/69359729/5ec93baa-bed8-4d9f-b983-3bc12264b9b6
     - | HumanoidMuscle4Ages.walk.1
       | HumanoidMuscle4Ages.run.1
     - | real: ✅
       | perfect: 🔶
       | preference: 🔶
     -  Task of a (~2 year old) **Torque** Humanoid Walking or Running Straight.
   * - .. image:: https://github.com/robfiras/loco-mujoco/assets/69359729/fed0315c-921e-4b2e-a9c2-54b85198ef65
     - | UnitreeH1.walk
     - | real: ✅
       | perfect: ✅
       | preference: 🔶
     -  UnitreeH1 Straight Walking Task.
   * - .. image:: https://github.com/robfiras/loco-mujoco/assets/69359729/ab0dec59-fc24-4763-8ff6-38d58ac3b3de
     - | UnitreeH1.run
     - | real: ✅
       | perfect: ✅
       | preference: 🔶
     -  UnitreeH1 Straight Running Task.
   * - .. image:: https://github.com/robfiras/loco-mujoco/assets/69359729/851ff3c0-d05f-4de1-a00b-7b3204056e2f
     - | UnitreeH1.carry
     - | real: ✅
       | perfect: 🔶
       | preference: 🔶
     -  UnitreeH1 Straight Carry Task.
   * - .. image:: https://github.com/robfiras/loco-mujoco/assets/69359729/22c7bb0c-ff92-4e99-a964-7654df6d22c4
     - | Talos.walk
     - | real: ✅
       | perfect: ✅
       | preference: 🔶
     -  Talos Straight Walking Task.
   * - .. image:: https://github.com/robfiras/loco-mujoco/assets/69359729/0ba1f0e7-1f3d-4088-a44f-0a53bec1cf3a
     - | Talos.carry
     - | real: ✅
       | perfect: 🔶
       | preference: 🔶
     -  Talos Straight Carry Task.
   * - .. image:: https://github.com/robfiras/loco-mujoco/assets/69359729/1ff09d98-e46b-429c-ac07-87de58853d28
     - | Atlas.walk
     - | real: ✅
       | perfect: ✅
       | preference: 🔶
     -  Atlas Straight Walking Task.
   * - .. image:: https://github.com/robfiras/loco-mujoco/assets/69359729/3c433333-3466-445b-b39f-2f990553d5ff
     - | Atlas.carry
     - | real: ✅
       | perfect: 🔶
       | preference: 🔶
     -  Atlas Straight Carry Task.
   * - .. image:: https://github.com/robfiras/loco-mujoco/assets/69359729/b722bb42-a26c-4692-b1a8-c6f71a78e37b
     - | UnitreeA1.simple
     - | real: ✅
       | perfect: ✅
       | preference: 🔶
     -  UnitreeA1 Straight Walking Task.
   * - .. image:: https://github.com/robfiras/loco-mujoco/assets/69359729/5a1f783e-8b52-4680-a22b-d96f89faf9b3
     - | UnitreeA1.hard
     - | real: ✅
       | perfect: ✅
       | preference: 🔶
     -  UnitreeA1 Walking in **8 Different Direction** Task.