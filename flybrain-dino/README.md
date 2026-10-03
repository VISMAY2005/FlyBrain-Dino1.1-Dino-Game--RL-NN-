# Fly Brain Dino 1.1

A hybrid AI experiment combining real Drosophila connectome data from Janelia neuPrint with a trainable neural network and PPO-based Reinforcement Learning.

Fly Brain Dino 1.1 uses a real connectome subnetwork as a fixed computational substrate. A lightweight rate-based neural activity model propagates activity through the biological connectivity, and a trainable neural network learns to map the resulting activity to actions in a custom Dino-style environment.

The project is designed as an interactive experiment for exploring how biological neural connectivity can be combined with modern reinforcement learning.

> This is not a simulation of the complete fly brain and is not intended to be electrophysiologically accurate.

## Project Overview

The agent operates inside a custom Dino-style environment.

It observes the environment, converts relevant game information into neural stimulation, propagates activity through a connectome-derived network, reads activity from selected neurons, and passes the resulting representation into a trainable policy.

The policy then selects an action.

The environment returns a reward, and PPO uses the collected experience to update the trainable model.

The overall pipeline is:

```text
Custom Dino Environment
        ↓
Game State Features
        ↓
Neural Stimulation
        ↓
Real Connectome Subnetwork
        ↓
Rate-Based Neural Activity
        ↓
64-Neuron Readout
        ↓
32-Unit Trainable Neural Network
        ↓
Policy + Value Output
        ↓
Action
        ↓
Environment
        ↓
Reward
        ↓
PPO Update
        ↓
Repeat
```

## What Makes This Project Different?

A conventional RL implementation could solve the same type of environment using:

```text
Game State → MLP → PPO → Action
```

This project experiments with an additional biological connectivity layer:

```text
Game State
    ↓
Connectome
    ↓
Neural Activity
    ↓
Trainable NN
    ↓
PPO
```

The goal is not to claim that the fly brain is directly controlling the game.

Instead, the project explores whether real biological connectivity can serve as a useful computational structure inside an artificial learning system.

## The Three Neural Components

### 1. Connectome

The connectome provides the underlying neural wiring.

The project queries Janelia's neuPrint service and retrieves real neuron information, including:

* Neuron body IDs
* Neuron types
* Neuron instances
* Soma coordinates
* Connectivity information
* Synaptic weights

The selected neurons form a subnetwork rather than the complete fly brain.

Available presets are:

| Preset   | Target neurons |
| -------- | -------------: |
| Compact  |           ~750 |
| Balanced |         ~1,500 |
| Large    |         ~2,200 |

The actual number of neurons in the final graph depends on the available connectivity and filtering process. Isolated neurons are removed.

### 2. Rate-Based Neural Activity

The project does not attempt to reproduce biological membrane potentials or detailed electrophysiology.

Instead, it uses a lightweight rate-based activity model.

Activity is propagated through the connectome for a configurable number of steps.

Important parameters include:

* Propagation steps
* Leak
* Gain
* Stimulation scale
* Activity clipping

The current default configuration uses:

```text
Propagation steps: 4
Leak:              0.5
Gain:              0.9
Stim scale:        1.5
Activity clip:     1.0
```

### 3. Trainable Neural Network

The connectome itself is treated as a fixed computational structure.

A trainable neural network sits after the connectome readout.

The current model uses:

```text
64 inputs
   ↓
32 hidden units
   ↓
2 policy outputs

and

32 hidden units
   ↓
1 value output
```

The two policy outputs correspond to the two available action choices.

The model learns how to interpret the connectome-derived activity rather than assuming a biologically verified mapping between specific fly neurons and game actions.

The project deliberately uses a computational action mapping rather than claiming that specific fly neurons biologically represent "Jump" or "Duck."

## Reinforcement Learning

The trainable policy is optimized using Proximal Policy Optimization, or PPO.

The agent learns through repeated interaction with the environment.

The basic process is:

```text
Observe
   ↓
Process neural activity
   ↓
Select action
   ↓
Advance environment
   ↓
Receive reward
   ↓
Store experience
   ↓
Calculate advantage / return
   ↓
PPO update
   ↓
Repeat
```

The implementation includes:

* Policy network
* Value network
* Generalized Advantage Estimation
* PPO clipping
* Entropy regularization
* Value loss
* Gradient clipping
* Adam optimizer
* Exploration schedule
* Observation normalization

## PPO Configuration

Default parameters:

```text
Hidden units:          32
Gamma:                 0.99
Lambda:                0.95
PPO clip:              0.20
Entropy coefficient:   0.01
Value coefficient:     0.5
Gradient clipping:     0.5
PPO epochs:            8
Minibatch size:        32
Minimum batch:         32
Learning rate:         0.001
Episodes per update:   16
Train steps/frame:     16
Test steps/frame:      1
Exploration start:     1.0
Exploration minimum:   0.05
Exploration decay:     0.995
Temperature gain:      2.0
```

## Dino Environment

The project uses a custom Dino-style environment rather than the original Chrome Dino game.

The environment was designed specifically for testing the RL architecture.

The agent has two active decisions:

```text
Action 0 → Jump
Action 1 → Duck
```

The agent also effectively has a no-action behaviour through the environment's timing and decision logic.

The environment includes:

* Ground obstacles
* High obstacles
* Increasing game speed
* Jump physics
* Ducking
* Gravity
* Obstacle spawning
* Variable obstacle gaps
* Decision distance
* Survival rewards
* Obstacle-clear rewards
* Collision penalties

## Environment State

The game state is converted into a feature representation before being used to stimulate the neural system.

The representation includes information related to:

* Distance to the next obstacle
* Obstacle type
* Game speed
* Current player state
* Jumping state
* Ducking state

The distance representation uses multiple spatial bins to provide a more continuous representation of where the next obstacle is located.

## Reward System

Three reward components are used:

```text
Survival reward
Obstacle-clear reward
Collision penalty
```

Default reward preset:

```text
Survive:    +0.01
Clear:      +1.00
Collision:  -1.00
```

Additional presets are available.

### STANDARD

```text
Survive:    0.01
Clear:      1.00
Collision: -1.00
```

### SURVIVAL

```text
Survive:    0.02
Clear:      0.75
Collision: -1.25
```

### RISKY

```text
Survive:    0.005
Clear:      1.25
Collision: -1.00
```

## Training Presets

Three training presets are provided.

### FAST

Designed for faster training iterations.

```text
Train steps/frame: 24
Episodes/update:   8
Learning rate:     0.002
Entropy:           0.015
```

### BALANCED

Default training configuration.

```text
Train steps/frame: 16
Episodes/update:   16
Learning rate:     0.001
Entropy:           0.01
```

### STABLE

Designed for slower and more conservative updates.

```text
Train steps/frame: 10
Episodes/update:   32
Learning rate:     0.0005
Entropy:           0.005
```

## Connectome Construction

When a connectome is rebuilt, the backend connects to Janelia neuPrint and selects neurons using configurable groups.

Current groups include:

```text
Sensory
Kenyon Cells (KC)
MBON
DAN
Descending
Motor
Central / Intrinsic
```

The groups are selected using configurable neuPrint fields and regular expressions.

The system then:

1. Queries neuPrint.
2. Selects neurons from the configured groups.
3. Retrieves soma coordinates.
4. Retrieves connections between selected neurons.
5. Combines duplicate connections.
6. Removes isolated neurons.
7. Normalizes incoming connection weights.
8. Selects readout neurons.
9. Generates a connectome hash.
10. Saves the resulting graph locally.

## Readout Layer

The project currently selects up to 64 readout neurons from:

```text
MBON
Descending
Motor
```

The readout neurons provide the input to the trainable neural network.

The project does not claim that these neurons have a biologically validated Jump/Duck mapping.

Instead:

```text
Connectome activity
        ↓
Readout neurons
        ↓
Trainable MLP
        ↓
Action policy
```

The MLP learns the action mapping through reinforcement learning.

## neuPrint Integration

The project uses Janelia's neuPrint service.

Default configuration:

```text
Server:
https://neuprint.janelia.org

Dataset:
male-cns:v1.0
```

The neuPrint token is kept on the backend.

It is loaded from:

```text
.env
```

Example:

```env
NEUPRINT_TOKEN=your_token_here
```

The token is not stored inside `config.py` and is not sent to the frontend.

## Offline Training After Connectome Build

The neuPrint connection is required when building or rebuilding a connectome.

Once a connectome has been cached:

```text
neuPrint
   ↓
connectome.json.gz
   ↓
Local browser/backend
   ↓
Training
```

Training itself does not require repeated neuPrint queries.

Cached connectomes are stored under:

```text
cache/
```

Each preset has its own cached graph.

## Connectome Hashing

Each generated connectome receives a short SHA-256 based hash.

The hash is generated from the neuron IDs and connectivity information.

This allows model checkpoints to verify that the loaded model belongs to the same connectome configuration.

Changing the connectome invalidates checkpoints associated with the previous graph.

## Visualization

The frontend provides an interactive visualization of the connectome.

The visualization includes:

* Neuron positions
* Neural activity
* Connectivity
* Group information
* Activity propagation
* Real-time training information

The brain visualization is interactive.

You can drag to rotate the network and hover over neurons to inspect information.

## Training Dashboard

The interface displays:

* Current episode
* Current score
* Best score
* Clearance rate
* Average reward
* Jump/Duck count
* Exploration value
* Prediction-error visualization
* Connectome size
* Edge count
* Readout size
* Current training status

## Dopamine-Like Prediction Error

The interface includes a visual prediction-error indicator.

The value is based on:

```text
Reward + gamma × V(next) - V(current)
```

This is used as a visualization of a reward-prediction-error-like signal.

It does not modify the model weights directly.

It is intended as an interpretive visualization of the RL signal rather than a biological simulation of dopamine neurons.

## Model Checkpoints

Models are saved as JSON checkpoints under:

```text
models/
```

A checkpoint contains information such as:

* Model version
* Experiment ID
* Dataset
* Connectome hash
* Connectome preset
* Readout neuron IDs
* Model weights
* Adam optimizer state
* PPO state
* Observation normalization
* Training parameters
* Reward preset
* Training preset
* Episode count
* Environment steps
* PPO updates
* Optimizer step
* Exploration state
* Training metrics
* Random seed

This allows a training session to be resumed while preserving the relevant experiment configuration.

## Model Compatibility

A checkpoint is checked against the current connectome before loading.

The system verifies information including:

* Dataset
* Connectome hash
* Readout neuron IDs

This prevents accidentally loading a model trained against a different connectome configuration.

## Project Structure

```text
flybrain-dino/
│
├── backend/
│   ├── config.py
│   ├── server.py
│   └── __pycache__/
│
├── frontend/
│   └── index.html
│
├── cache/
│   └── <connectome presets>
│
├── models/
│   └── <saved checkpoints>
│
├── .env.example
├── requirements.txt
├── start.bat
└── README.md
```

## Backend

The backend is built with Flask.

Main responsibilities:

```text
Flask API
    ↓
neuPrint connection
    ↓
Connectome construction
    ↓
Connectome caching
    ↓
Model checkpoint management
```

Main API endpoints include:

```text
GET  /
GET  /api/health
GET  /api/config
GET  /api/connectome/status
GET  /api/connectome
GET  /api/connectome/meta
POST /api/connectome/build
GET  /api/models
POST /api/models/save
POST /api/models/load
```

## Frontend

The frontend is implemented as a self-contained HTML application using:

* HTML
* CSS
* JavaScript
* Canvas-based visualization

The frontend handles:

* Dino environment
* RL loop
* PPO updates
* Neural activity visualization
* Connectome visualization
* Training controls
* Testing controls
* Metrics
* Model save/load interface

## Requirements

Python 3.x

Python packages:

```text
Flask
neuprint-python
python-dotenv
```

Install manually with:

```bash
pip install -r requirements.txt
```

## Installation

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd flybrain-dino
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
```

Activate it:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure neuPrint

Create a `.env` file:

```env
NEUPRINT_TOKEN=your_neuprint_token
```

The token is used only by the backend when constructing a connectome.

## Windows Quick Start

The repository includes:

```text
start.bat
```

Double-clicking it will:

1. Create a virtual environment if one does not exist.
2. Activate the environment.
3. Install the required packages.
4. Create `.env` from `.env.example` if needed.
5. Open the local application.
6. Start the Flask server.

The application runs by default at:

```text
http://127.0.0.1:8000
```

## First Run

After starting the application:

1. Add your neuPrint token to `.env`.
2. Open the application.
3. Select a connectome preset.
4. Press Rebuild.
5. Wait for neuPrint to return the graph.
6. The graph is cached locally.
7. Select a training preset.
8. Select a reward preset.
9. Press Train.
10. Monitor the agent and neural activity.
11. Use Save to create a checkpoint.
12. Use Test to evaluate the current policy.

## Configuration

Most project parameters are stored in:

```text
backend/config.py
```

The main configuration sections are:

```text
neuprint
connectome
rl
training_presets
reward_presets
game
visual
paths
server
```

This allows the environment and learning system to be modified without changing the core server.

## Important Configuration Parameters

### Connectome

```python
presets={
    "compact": 750,
    "balanced": 1500,
    "large": 2200
}
```

### Readout

```python
readout_size=64
```

### Neural propagation

```python
propagation_steps=4
leak=0.5
gain=0.9
stim_scale=1.5
act_clip=1.0
```

### PPO

```python
hidden=32
gamma=0.99
lam=0.95
clip=0.20
entropy=0.01
value_coef=0.5
grad_clip=0.5
lr=0.001
```

### Environment

```python
gravity=0.6
jump_v=10.5
duck_steps=34
start_speed=5
max_speed=9
accel=0.0006
bird_chance=0.35
```

### Visualization

```python
auto_rotate=0.003
activity_decay=0.85
particle_size=1.0
vis_gain=2.5
seed=7
```

## Experimental Presets

The project provides three connectome configurations.

### Compact

Approximately 750 target neurons.

Useful for faster experimentation and testing.

### Balanced

Approximately 1,500 target neurons.

This is the default configuration.

### Large

Approximately 2,200 target neurons.

Provides a larger connectivity structure for experimentation.

## Changing the Connectome

Changing the connectome preset changes the computational graph.

When switching to another graph:

1. The new graph must be cached.
2. Existing checkpoints from another graph should not be reused.
3. Start a new experiment.
4. Rebuild the graph if it has not already been cached.

## Research / Experiment Direction

The project is intended to support experiments around the question:

```text
Can real biological connectivity serve as a useful computational substrate
for an artificial reinforcement-learning agent?
```

A meaningful next step is to compare the architecture against conventional RL baselines.

For example:

```text
Baseline:
Game State → MLP → PPO

Hybrid:
Game State → Connectome → Readout → MLP → PPO
```

Potential evaluation metrics include:

* Episode reward
* Survival time
* Obstacle clearance
* Learning speed
* Sample efficiency
* Training stability
* Generalization
* Parameter count
* Computational cost

These comparisons would help determine whether the connectome contributes useful computational properties rather than evaluating the system only on whether it learns the environment.

## Scientific Scope

This project uses real connectome data, but it does not attempt to reproduce the full biological behaviour of a fly brain.

The neural activity model is simplified.

It does not reproduce:

* Detailed membrane dynamics
* Ion-channel behaviour
* Spiking neuron dynamics
* Neurotransmitter dynamics
* Full biological synaptic dynamics
* Complete fly-brain connectivity
* Biologically validated action representations

The connectome is used as a computational structure.

The trainable neural network and PPO algorithm are responsible for learning the task-specific behaviour.

## Important Distinction

The project should not be interpreted as:

```text
Real Fly Brain → Controls Dino
```

The actual computational architecture is closer to:

```text
Real Fly Connectome
        ↓
Simplified Neural Activity
        ↓
Readout
        ↓
Trainable Neural Network
        ↓
PPO Policy
        ↓
Dino Action
```

This distinction is important when interpreting the results.

## Technology Stack

### Backend

```text
Python
Flask
neuprint-python
python-dotenv
```

### Frontend

```text
HTML
CSS
JavaScript
Canvas API
```

### AI / ML

```text
Reinforcement Learning
PPO
Neural Networks
Rate-Based Neural Activity
Generalized Advantage Estimation
Adam Optimization
Observation Normalization
```

### Neuroscience / Connectomics

```text
Janelia neuPrint
Drosophila connectome
Neuron connectivity
Synaptic weights
Neuron metadata
```

## Credits

Connectome data is obtained from Janelia's neuPrint platform.

Project:

Fly Brain Dino 1.1

Built as an experimental exploration of:

```text
Connectomics
+
Neural Networks
+
Reinforcement Learning
```

## Disclaimer

This project is an experimental computational model.

It should not be interpreted as a complete biological simulation of the Drosophila brain or as evidence that the selected biological neurons correspond directly to the actions used by the Dino environment.

The connectome provides real biological connectivity data, while the neural activity model, trainable neural network, environment, and reinforcement-learning system provide the computational framework for the experiment.

## License

Add your preferred license here.

For example:

```text
MIT License
```

or replace this section with the license used by the repository.
