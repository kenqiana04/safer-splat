# Next Actions: Navigation Stack and Real Robot

## Immediate Next Actions

1. Confirm nominal planner/controller in the current repo: current evidence supports a simple goal-directed nominal controller, not a full planner.
2. Confirm current dynamics: current evidence supports a 3D double-integrator point model.
3. Decide paper title wording: prefer planner-agnostic safety assurance wording.
4. Decide whether to include "four-wheel" in the title: recommendation is no, unless a four-wheel-specific adapter is implemented.
5. Confirm lab robot command interface: `cmd_vel`, Ackermann, or other.
6. Confirm pose/localization source and update rate.
7. Confirm GSplat-to-robot frame alignment method.
8. Plan the minimal real-world demo scenes: start-near-obstacle, narrow passage, close-pass near goal, DT-warning/recovery.
9. Start Method/System Overview draft after audit.
10. Add a limitations paragraph separating simulation benchmark claims from real-robot deployment claims.

## Do Not Do Next

1. Do not open a new Adaptive branch.
2. Do not restart MPC-style recovery as a main method.
3. Do not run full100 for frozen branches.
4. Do not claim full navigation planner contribution.
5. Do not claim localization contribution.
6. Do not claim four-wheel dynamics validation from the current double-integrator simulation.
7. Do not write h / min_safety_h as metric clearance in meters.
8. Do not write margin violation as collision.
9. Do not present FC-Aware as the main method without redesign.
10. Do not use real-robot demo language that implies global safety guarantee.

## Writing Priority

1. System Overview: baseline nominal command, GSplat CBF-QP, wrapper safety assurance layer.
2. Method: start feasibility, repair, H-step DT verification, triggered V4-C recovery.
3. Experiments: simulation evidence first; diagnostic branches clearly marked.
4. Real-Robot Deployment: interface plan and minimal demonstration scenes.
5. Limitations: no planner, no localization, no four-wheel dynamics in current simulation.

## Deployment Priority

1. Get robot command API.
2. Get pose source.
3. Calibrate GSplat frame to robot/world frame.
4. Implement command adapter and low-speed safety limits.
5. Add independent emergency stop.
6. Run static h checks before motion.
7. Run low-speed start-near-obstacle demo.
8. Run narrow passage and DT-warning demos only after logs look sane.
