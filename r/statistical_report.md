## Cross-reference against the Python model

Compared against the Python logistic regression's standardized coefficients
(`../reports/figures/logreg_coefficients.png`). Exact magnitudes are not
expected to match — the Python model's features are scaled (StandardScaler)
and uses L2-regularized MLE, while this R model is fit on raw/unscaled
features with unregularized MLE. What matters per the TRD's success
criterion (section 14) is whether the sign and relative importance of each
coefficient agree.

**Directionally consistent on every statistically significant feature:**

| Feature | R sign / sig. | Python sign / magnitude | Agreement |
|---|---|---|---|
| reason_1 | + (p<0.001) | + (0.35) | Yes |
| reason_3 | + (p<0.001), strongest R driver | + (0.45), 3rd-largest | Yes |
| transportation_expense | + (p<0.001) | + (0.68), largest Python coef | Yes |
| children | + (p<0.001) | + (0.40) | Yes |
| pets | − (p<0.001) | − (0.33) | Yes |
| body_mass_index | + (p=0.011) | + (0.30) | Yes |
| age | − (p=0.024) | − (0.22) | Yes |
| day_of_week | − (n.s., p=0.078) | − (small) | Yes |
| distance_to_work | − (n.s.) | − (small) | Yes |
| education_binary | − (n.s.) | − (small) | Yes |
| daily_work_load_average | − (n.s.) | − (smallest) | Yes |
| month_value | + (n.s.) | + (small) | Yes |

**Discrepancy: `reason_2`.** R estimates a positive effect (+0.65) while
Python shows a small negative one (−0.08). Neither model treats this as a
reliable signal — R's p-value is 0.476 and Python's magnitude is among the
smallest in the model. Reason codes 15-17 (pregnancy/childbirth-related)
are rare in this 662-row sample, so neither model has enough cases to pin
down that coefficient's sign confidently. This is a sample-size limitation,
not a modeling disagreement, and is flagged rather than resolved.

**Structural difference: `reason_4`.** R drops this coefficient (`NA`) due
to perfect collinearity — the cleaned view's `WHERE` filter excludes
reason-code-0 rows, so `reason_1`..`reason_4` always sum to exactly 1 for
every remaining row, creating a dummy-variable trap that unregularized
`glm()` cannot resolve. Python's `sklearn` model returns a real coefficient
(−0.58, second-largest by magnitude) because L2 regularization keeps the
optimization well-defined under collinearity by distributing weight across
the four correlated reason dummies. Both results are correct for their
respective methodology; they are simply not directly comparable on this
one feature without further adjustment (e.g. dropping the GLM intercept or
one reason category to remove the collinearity).

**Conclusion:** every feature with a statistically significant effect in
either model agrees in direction between R and Python, satisfying the
TRD's cross-validation success criterion (section 14: "Python and R models
produce directionally consistent coefficients").