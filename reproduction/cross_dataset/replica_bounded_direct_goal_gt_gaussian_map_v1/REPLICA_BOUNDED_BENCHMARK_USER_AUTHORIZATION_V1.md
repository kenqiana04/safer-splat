# Replica Bounded Benchmark User Authorization V1

`AUTHORITY_TYPE: EXPLICIT_USER_AUTHORIZED_BENCHMARK_DESIGN`

This is `NEW_VERSIONED_REPLICA_BENCHMARK_DESIGN_CHOICE`. It is not a recovered official SAFER robot parameter and is not a parameterization of any physical robot platform.

The benchmark state is `[px, py, pz, vx, vy, vz]`; the control is `[ax, ay, az]`; coordinates are metric free-3D. The robot is a spherical benchmark primitive with `r_robot=0.10 m` and `epsilon_base=0.01 m`. With `dt=0.05 s`, forward Euler is `p_next=p+dt*v`, `v_next=v+dt*u`. Each velocity and acceleration component is bounded in `[-0.10, 0.10]` in SI units. Initial and goal velocities are zero.

The direct-goal nominal controller is `vel_des=clip(5*(p_goal-p), -0.10, 0.10)` and `u_des=clip(vel_des-v, -0.10, 0.10)`. The actual control is never formed by clipping `u_des`: it is produced only by the bounded QP. A non-solved QP returns no control and does not advance the plant.

The maximum simulation horizon reserved for the future benchmark is 500 steps / 25.0 s. Success is position norm <=0.03 m and velocity norm <=0.03 m/s. This task performs no multi-step benchmark.
