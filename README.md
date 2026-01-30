# Fuzzy Logic Control of Ball-and-Beam System

This project presents the design, implementation, and comparison of two different
fuzzy logic controllers for the control of a classic **Ball-and-Beam system**, which
is an inherently unstable nonlinear control problem.

The study was carried out within the scope of the **Fuzzy Logic Applications Course**
in the Department of Computer Engineering.

---

## Project Scope

Two fuzzy control approaches are implemented and analyzed:

1. **Intuitive (Rule-Based) Fuzzy Controller**
   - Control rules are manually designed based on human intuition and experience.

2. **Model-Based Automatic Fuzzy Controller (PD-Based)**
   - Control rules are generated algorithmically using a simplified PD control model.

The main objective of both controllers is to keep the ball balanced at the center
of the beam (position = 0).

---

## System Description

### Inputs
- **Ball Position (x)** ∈ [-1, 1]
- **Ball Velocity (v)** ∈ [-1, 1]

### Output
- **Beam Angle (θ)** ∈ [-1, 1]

All variables are normalized to ensure consistency and stable control behavior.

---

## Controller Designs

### Intuitive Fuzzy Controller

- Membership Functions: Triangular
- Linguistic Variables:
  - Position: Left – Center – Right
  - Velocity: Negative – Zero – Positive
  - Output Angle: Left – Straight – Right
- Rule Base: 9 manually defined fuzzy rules

This controller relies on human-like reasoning and provides smooth and stable control
near the equilibrium point.

---

### Model-Based (PD-Based) Fuzzy Controller

- Fuzzy rules are generated automatically
- Based on the following control effect:

  **effect = −position − 0.5 × velocity**

- Linguistic Labels: Poor – Average – Good

This approach eliminates manual tuning and focuses on fast error correction,
although it may introduce small oscillations around the equilibrium point.

---

## Performance Comparison

| Criterion            | Intuitive Controller | Model-Based Controller |
|----------------------|---------------------|------------------------|
| Stability            | High                | Medium                 |
| Response Speed       | Medium–Fast         | Fast                   |
| Oscillation          | Low                 | Small oscillations     |
| Noise Sensitivity    | Low–Medium          | Medium–High            |
| Design Method        | Manual              | Algorithmic            |

---

## Simulation Results

### Intuitive Fuzzy Controller Response
![Intuitive Response](figures/intuitive_response.png)

### Model-Based Fuzzy Controller Response
![Model-Based Response](figures/model_based_response.png)

### Control Signal and Ball Position Comparison
The figure below presents a combined comparison of control signals and ball position
responses for both intuitive and model-based fuzzy controllers.
![Control and Position Comparison](figures/control_and_position_comparison.png)

---

## Conclusion

The intuitive fuzzy controller provides smoother and more human-like responses,
while the model-based fuzzy controller achieves faster convergence through
analytical rule generation.

Both controllers demonstrate that fuzzy logic is an effective and robust control
strategy for unstable nonlinear systems such as the Ball-and-Beam system.

---

Department of Computer Engineering  
Fuzzy Logic Applications Course
