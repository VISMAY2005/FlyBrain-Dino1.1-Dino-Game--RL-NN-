# ALL editable parameters live here. The frontend reads them from /api/config at load.
CFG = dict(
 neuprint=dict(server="https://neuprint.janelia.org", dataset="male-cns:v1.0"),
 connectome=dict(
  default="balanced", presets={"compact": 750, "balanced": 1500, "large": 2200},  # targets, never padded
  readout_size=64, propagation_steps=4, leak=0.5, gain=0.9, stim_scale=1.5, act_clip=1.0,
  # (group, neuprint field, regex, share of target). UNVERIFIED against male-cns:v1.0 -- check in the neuPrint explorer.
  groups=[("sensory","superclass","(?i).*(sensory|visual_projection).*",0.20),
          ("kc","type","^KC.*",0.28), ("mbon","type","^MBON.*",0.03),
          ("dan","type","^(PPL1|PAM|PPL2|PPM3).*",0.02),
          ("descending","superclass","(?i).*descending.*",0.12),
          ("motor","superclass","(?i).*motor.*",0.05),
          ("central","superclass","(?i).*(central|intrinsic).*",0.30)],
  readout_groups=["mbon","descending","motor"],
  # Full-brain backdrop: REAL somas of neurons that are NOT simulated, drawn as dim dust so the brain shape reads.
  # mod=3 keeps ~1/3 of all neurons (bodyId % mod == 0). where = optional extra Cypher filter, e.g. "n.superclass =~ '(?i).*(optic|central).*'"
  context=dict(mod=3, limit=70000, where="")),
 rl=dict(hidden=32, gamma=0.99, lam=0.95, clip=0.20, entropy=0.01, value_coef=0.5, grad_clip=0.5,
  epochs=8, minibatch=32, min_batch=32, lr=0.001, episodes_per_update=16, train_steps_per_frame=16, test_steps_per_frame=1,
  explore_start=1.0, explore_min=0.05, explore_decay=0.995, temp_gain=2.0, model_version=2),
 training_presets=dict(
  FAST=dict(train_steps_per_frame=24, episodes_per_update=8, lr=0.002, entropy=0.015),
  BALANCED=dict(train_steps_per_frame=16, episodes_per_update=16, lr=0.001, entropy=0.01),
  STABLE=dict(train_steps_per_frame=10, episodes_per_update=32, lr=0.0005, entropy=0.005)),
 reward_presets=dict(STANDARD=dict(survive=0.01, clear=1.0, collide=-1.0),
  SURVIVAL=dict(survive=0.02, clear=0.75, collide=-1.25), RISKY=dict(survive=0.005, clear=1.25, collide=-1.0)),
 game=dict(gravity=0.6, jump_v=10.5, duck_steps=34, start_speed=5, max_speed=9, accel=0.0006, bird_chance=0.35,
  spawn_gap_min=260, spawn_gap_rand=200, decision_dist=100,
  bird_w=28, bird_by=24, bird_h=100),  # high obstacle: a jump cannot clear it, only a duck passes underneath
 visual=dict(palette=[['optic','#6f8cff'],['visual','#ffb347'],['central','#ff6f91'],['sensory','#4fe3b0'],['descending','#7dff7d'],['motor','#ff9a52'],['ascending','#8fd0ff'],['endocrine','#e0a0ff'],['','#9a7bff']],
  backdrop_gain=1.0, auto_rotate=0.003, activity_decay=0.85, particle_size=1.0, contrast=3.0, seed=7),
 paths=dict(cache="cache", models="models"),
 server=dict(host="127.0.0.1", port=8000),
)
