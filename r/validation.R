# ==============================================================================
# Statistical Validation — Absenteeism Risk Model (R)
# ==============================================================================
# TRD section 10.3: independent glm(family="binomial") logistic regression,
# fit on the same `absenteeism_cleaned` BigQuery view used by the Python
# model, reporting coefficient estimates, standard errors, p-values, odds
# ratios, and a Hosmer-Lemeshow goodness-of-fit test. Output is exported as
# both a markdown report and a CSV, for cross-referencing against the
# Python model's coefficients (see ../reports/figures/logreg_coefficients.png)
# as an independent sanity check.

library(bigrquery)
library(dplyr)
library(broom)
library(ResourceSelection)
library(knitr)

# ---- 1. Pull cleaned data from BigQuery ------------------------------------

PROJECT_ID <- "absenteeism-risk-platform"
DATASET    <- "absenteeism_analytics"
VIEW       <- "absenteeism_cleaned"

bq_auth()

sql <- sprintf("SELECT * FROM `%s.%s.%s`", PROJECT_ID, DATASET, VIEW)
tb  <- bq_project_query(PROJECT_ID, sql)
df  <- bq_table_download(tb)

cat("Pulled", nrow(df), "rows,", ncol(df), "columns from", VIEW, "\n")

# ---- 2. Fit the model --------------------------------------------------------

feature_cols <- c(
  "reason_1", "reason_2", "reason_3", "reason_4",
  "month_value", "day_of_week", "transportation_expense",
  "distance_to_work", "age", "daily_work_load_average",
  "body_mass_index", "education_binary", "children", "pets"
)

missing_cols <- setdiff(c(feature_cols, "excessive_absenteeism"), names(df))
if (length(missing_cols) > 0) {
  stop("Cleaned view is missing expected columns: ", paste(missing_cols, collapse = ", "))
}

model_df <- df %>%
  select(all_of(c(feature_cols, "excessive_absenteeism"))) %>%
  mutate(across(everything(), as.numeric))

glm_model <- glm(
  excessive_absenteeism ~ .,
  data = model_df,
  family = binomial(link = "logit")
)

cat("\n=== Model Summary ===\n")
print(summary(glm_model))

# ---- 3. Coefficients, p-values, odds ratios ---------------------------------

coef_table <- tidy(glm_model, conf.int = TRUE) %>%
  mutate(
    odds_ratio = exp(estimate),
    or_conf_low = exp(conf.low),
    or_conf_high = exp(conf.high),
    significant_05 = p.value < 0.05
  ) %>%
  arrange(p.value)

cat("\n=== Coefficients, Standard Errors, p-values, Odds Ratios ===\n")
print(kable(coef_table %>%
  select(term, estimate, std.error, p.value, odds_ratio, significant_05),
  digits = 4))

# ---- 4. Goodness-of-fit: Hosmer-Lemeshow -------------------------------------

hl_test <- hoslem.test(
  x = glm_model$y,
  y = fitted(glm_model),
  g = 10
)

cat("\n=== Hosmer-Lemeshow Goodness-of-Fit Test ===\n")
print(hl_test)
hl_verdict <- if (hl_test$p.value > 0.05) {
  "Fails to reject H0 (p > 0.05) -> no evidence of poor fit; model is well-calibrated."
} else {
  "Rejects H0 (p <= 0.05) -> evidence of poor fit; investigate calibration before trusting probabilities."
}
cat(hl_verdict, "\n")

# ---- 5. McFadden's pseudo-R^2 -------------------------------------

null_model <- glm(excessive_absenteeism ~ 1, data = model_df, family = binomial)
mcfadden_r2 <- 1 - (logLik(glm_model) / logLik(null_model))
cat("\nMcFadden's pseudo-R^2:", round(as.numeric(mcfadden_r2), 4), "\n")

# ---- 6. Export results -------------------------------------------------------

dir.create("../reports", showWarnings = FALSE)

write.csv(coef_table, "r_coefficients.csv", row.names = FALSE)

report_lines <- c(
  "# Statistical Validation Report — R (glm logistic regression)",
  "",
  sprintf("Fit on `%s.%s.%s` (%d rows, %d features).", PROJECT_ID, DATASET, VIEW, nrow(model_df), length(feature_cols)),
  "",
  "## Coefficients, p-values, odds ratios",
  "",
  kable(coef_table %>% select(term, estimate, std.error, p.value, odds_ratio, significant_05), digits = 4, format = "markdown"),
  "",
  "## Goodness-of-fit",
  "",
  sprintf("- Hosmer-Lemeshow chi-sq = %.4f, df = %d, p-value = %.4f", hl_test$statistic, hl_test$parameter, hl_test$p.value),
  sprintf("- Verdict: %s", hl_verdict),
  sprintf("- McFadden's pseudo-R^2: %.4f", as.numeric(mcfadden_r2)),
  "",
  "## Cross-reference against the Python model",
  "",
  "Compare the sign and relative magnitude of each coefficient above against",
  "`../reports/figures/logreg_coefficients.png` (Python logistic regression,",
  "standardized coefficients). Directionally consistent coefficients between",
  "R and Python (same sign on the dominant features) is the TRD's success",
  "criterion for this validation step — exact magnitudes will differ since",
  "the Python model's features are scaled (StandardScaler) and this R model",
  "is fit on raw/unscaled features."
)

writeLines(report_lines, "statistical_report.md")

cat("\nWrote r/r_coefficients.csv and r/statistical_report.md\n")