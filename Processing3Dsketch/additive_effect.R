suppressPackageStartupMessages({
  library(lme4)
  library(emmeans)
  library(dplyr)
})

# --- k/n model (primary) ---
# Same random effects in both models
m_full_kn <- glmer(
  cbind(k_correct, n_trials - k_correct) ~ relation * condition + (1 | participant_id),
  family = binomial, data = df_kn,
  control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))
)

m_add_kn <- glmer(
  cbind(k_correct, n_trials - k_correct) ~ relation + condition + (1 | participant_id),
  family = binomial, data = df_kn,
  control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))
)

# Likelihood-ratio test for the interaction
lrt_kn <- anova(m_add_kn, m_full_kn, test = "Chisq")
print(lrt_kn)  # p-value tests relation:condition

# Optional: compare against intercept-only (global baseline)
m_int_kn <- glmer(
  cbind(k_correct, n_trials - k_correct) ~ 1 + (1 | participant_id),
  family = binomial, data = df_kn,
  control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))
)
anova(m_int_kn, m_add_kn, m_full_kn, test = "Chisq")  # nested ladder

# --- Trial-level diagnostic (binary) ---
m_full_tr <- glmer(
  accuracy ~ relation * condition + (1 | participant_id),
  family = binomial, data = td,
  control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))
)

m_add_tr <- glmer(
  accuracy ~ relation + condition + (1 | participant_id),
  family = binomial, data = td,
  control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))
)

anova(m_add_tr, m_full_tr, test = "Chisq")  # interaction test on trials

# --- Post-hoc: simple effects on probability scale (reportable) ---
emm_cells <- emmeans(m_full_kn, ~ relation * condition, type = "response")
pairs(emm_cells, by = "condition", type = "response")  # H vs V within each condition
pairs(emm_cells, by = "relation",  type = "response")  # Aligned vs Rotated within each relation
