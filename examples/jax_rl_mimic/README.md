## DeepMimic Imitation Learning Example

This example demonstrates training a PPO agent with a DeepMimic reward on the Unitree H1 robot to mimic a dataset of 
human walking in different directions.

This example will use the `GoalTrajMimic` as a goal vector including positions, orientations, and velocities of the 
site positions and joint positions and velocities to match from the expert dataset. The defined reward function in 
the configuration is`MimicReward`, which corresponds to a DeepMimic style reward. The trained agent 
can walk in various directions and rotate around its z-axis at the end of training.

---

### 🚀 Training

To train the agent, run:

```bash
python experiment.py
```

This command will:

- Train the PPO agent on the Unitree H1 robot for 300 million steps (approximately 36 minutes on an RTX 3080 Ti).
- Save the trained agent (as `GAILJax_saved.pkl` in the `outputs` folder).
- Perform a final rendering of the trained policy.
- Save a video of the rendering to the `LocoMuJoCo_recordings/` directory.
- Upload the video to Weights & Biases (WandB) for further analysis (check the command line logs for details).


#### Validation Loop During Training

Throughout training, the agent will be evaluated using various trajectory-based metrics, including 
Euclidean distance, Dynamic Time Warping (DTW), and discrete Fréchet distance. These metrics will be 
computed on different entities such as joint positions, joint velocities, and site positions and orientations. 
All results will be logged to Weights & Biases (WandB).

---

### 📈 Evaluation

To evaluate the trained agent, run:

```bash
python eval.py --path path/to/agent_file
```

If you'd like to evaluate the agent using MuJoCo (instead of Mjx), run:

```bash
python eval.py --path path/to/agent_file --use_mujoco
```

> ⚠️ **Note:** Evaluating with MuJoCo may not yield results as robust as with Mjx due to simulator differences. For reliable policy transfer between the two, consider applying domain randomization techniques.
nks to the dataset, or more details about the environment or architecture!