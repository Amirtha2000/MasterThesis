# ----- model_binom.R (Primary GLMM + supporting tests; reproducible) -----
suppressPackageStartupMessages({
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(lme4)
  library(emmeans)
  library(broom.mixed)
  library(easystats)      # performance, parameters, report, insight, effectsize
  library(readr)
})

# ===== 0) I/O, environment, and version capture =====
out_dir <- "model_outputs"
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

# Capture versions for reproducibility (Methods/Appendix)
sink(file.path(out_dir, "session_versions.txt"))
cat("R version:\n"); print(R.version.string)
cat("\nPackage versions:\n")
pv <- data.frame(
  package = c("lme4","emmeans","easystats","ggplot2","dplyr","broom.mixed"),
  version = c(
    as.character(packageVersion("lme4")),
    as.character(packageVersion("emmeans")),
    as.character(packageVersion("easystats")),
    as.character(packageVersion("ggplot2")),
    as.character(packageVersion("dplyr")),
    as.character(packageVersion("broom.mixed"))
  )
)
print(pv, row.names = FALSE)
sink()

# ===== 1) Preconditions =====
if (!exists("raw_df") && !exists("df")) {
  stop("No data found. Provide 'raw_df' or 'df'.")
}
df <- if (exists("df")) df else raw_df

req <- c("k_correct","n_trials","relation","condition","participant_id")
missing <- setdiff(req, names(df))
if (length(missing)) stop("Data missing required columns: ", paste(missing, collapse = ", "))

# ===== 2) Minimal hygiene & baselines =====
# Allow either H/V or Horizontal/Vertical; same for condition
norm_rel <- function(x) {
  x <- as.character(x)
  x[x %in% c("H","Horizontal")] <- "H"
  x[x %in% c("V","Vertical")]   <- "V"
  factor(x, levels = c("H","V"))
}
norm_cond <- function(x) {
  x <- as.character(x)
  x[x %in% c("Aligned","aligned","A")] <- "Aligned"
  x[x %in% c("Rotated","rotated","R")] <- "Rotated"
  factor(x, levels = c("Aligned","Rotated"))
}

df <- df %>%
  mutate(
    relation       = norm_rel(relation),
    condition      = norm_cond(condition),
    participant_id = factor(participant_id),
    prop_correct   = k_correct / n_trials
  )

# Optional: rotation skill (for exploratory model only)
if (all(c("rotation_floor1","rotation_floor2") %in% names(df))) {
  df <- df %>%
    mutate(rot_acc_raw = rowMeans(pick(rotation_floor1, rotation_floor2), na.rm = TRUE),
           rot_acc_z   = as.numeric(scale(rot_acc_raw)))
}

# ===== 3) Descriptives (sanity) =====
cat("\n== Descriptives: mean proportion correct by cell ==\n")
print(df %>% group_by(relation, condition) %>% summarise(prop = mean(prop_correct), .groups = "drop"))

if (any(df$k_correct > df$n_trials, na.rm = TRUE)) stop("Found k_correct > n_trials.")
cell_chk <- count(df, participant_id, relation, condition)
if (any(cell_chk$n != 1)) message("Note: some participant × relation × condition cells have n != 1.")

# ===== 4) Primary model (k/n GLMM with interaction) =====
m_full_kn <- glmer(
  cbind(k_correct, n_trials - k_correct) ~ relation * condition + (1 | participant_id),
  family = binomial, data = df,
  control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))
)
cat("\n== GLMM (PRIMARY) summary ==\n"); print(summary(m_full_kn))

# Additive comparator and intercept-only for LRT ladder (for significance of interaction)
m_add_kn <- glmer(
  cbind(k_correct, n_trials - k_correct) ~ relation + condition + (1 | participant_id),
  family = binomial, data = df,
  control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))
)
m_int_kn <- glmer(
  cbind(k_correct, n_trials - k_correct) ~ 1 + (1 | participant_id),
  family = binomial, data = df,
  control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))
)

cat("\n== Model selection (AIC/logLik/Δ) ==\n")
sel_tbl <- tibble(
  model  = c("Interaction (relation*condition)", "Additive (relation+condition)", "Intercept-only"),
  AIC    = c(AIC(m_full_kn), AIC(m_add_kn), AIC(m_int_kn)),
  logLik = c(as.numeric(logLik(m_full_kn)), as.numeric(logLik(m_add_kn)), as.numeric(logLik(m_int_kn)))
) |>
  mutate(DeltaAIC = AIC - min(AIC))
print(sel_tbl)

cat("\n== Likelihood-ratio tests (nested ladder) ==\n")
print(anova(m_int_kn, m_add_kn, m_full_kn, test = "Chisq"))

# ===== 5) EMMs & pairwise tests (reportable, probability scale) =====
emm_cells <- emmeans(m_full_kn, ~ relation * condition, type = "response") |> as.data.frame()
names(emm_cells) <- sub("^asymp\\.", "", names(emm_cells))  # normalize CI names (older/newer emmeans)

cat("\n== EMMs (probability) ==\n"); print(emm_cells)

cat("\n== Simple effects: H vs V within each condition (ORs) ==\n")
print(pairs(emmeans(m_full_kn, ~ relation * condition), by = "condition", type = "response", adjust = "none"))

cat("\n== Simple effects: Aligned vs Rotated within each relation (ORs) ==\n")
print(pairs(emmeans(m_full_kn, ~ relation * condition), by = "relation", type = "response", adjust = "none"))

# ===== 6) Assumptions via easystats =====
# Overdispersion, R2, ICC, convergence, collinearity
perf_full <- performance::model_performance(m_full_kn)
r2_full   <- performance::r2(m_full_kn)
icc_full  <- performance::icc(m_full_kn)
disp_full <- performance::check_overdispersion(m_full_kn)
coll_full <- performance::check_collinearity(m_full_kn)
conv_full <- performance::check_convergence(m_full_kn)

# Persist compact performance table (LaTeX)
perf_tbl <- tibble::tibble(
  Metric = c("AIC","BIC","R$^2$ (marginal)","R$^2$ (conditional)","ICC","Overdispersion $\\phi$"),
  Value  = c(
    sprintf("%.2f", perf_full$AIC),
    sprintf("%.2f", perf_full$BIC),
    sprintf("%.3f", r2_full$R2_marginal),
    sprintf("%.3f", r2_full$R2_conditional),
    sprintf("%.3f", icc_full$ICC_adjusted),
    sprintf("%.3f", disp_full$dispersion_ratio)
  )
)

latex_perf <- knitr::kable(
  perf_tbl, format = "latex", booktabs = TRUE,
  caption = "Primary GLMM performance indices (easystats).",
  col.names = c("Metric", "Value")
)
writeLines(latex_perf, file.path(out_dir, "performance_primary_glmm.tex"))

# Persist parameters (logit + OR)
par_logit <- parameters::model_parameters(m_full_kn, effects = "fixed", ci = 0.95, exponentiate = FALSE)
par_or    <- parameters::model_parameters(m_full_kn, effects = "fixed", ci = 0.95, exponentiate = TRUE)

# Odds-ratio LaTeX table
or_tbl <- par_or |>
  transmute(
    Effect = gsub(":", " × ", Parameter),
    `Odds Ratio` = sprintf("%.2f", Coefficient),
    `95\\%% CI`   = paste0("[", sprintf("%.2f", CI_low), ", ", sprintf("%.2f", CI_high), "]"),
    `p` = insight::format_p(p)
  )
latex_or <- knitr::kable(
  or_tbl, format = "latex", booktabs = TRUE,
  caption = "Fixed effects (odds ratios) for the primary GLMM.",
  col.names = c("Effect","Odds Ratio","95\\% CI","$p$")
)
writeLines(latex_or, file.path(out_dir, "parameters_or_primary_glmm.tex"))

# Save diagnostics summaries
capture.output(perf_full,  file = file.path(out_dir, "model_performance_primary.txt"))
capture.output(r2_full,    file = file.path(out_dir, "r2_primary.txt"))
capture.output(icc_full,   file = file.path(out_dir, "icc_primary.txt"))
capture.output(disp_full,  file = file.path(out_dir, "overdispersion_primary.txt"))
capture.output(conv_full,  file = file.path(out_dir, "convergence_primary.txt"))
capture.output(coll_full,  file = file.path(out_dir, "collinearity_primary.txt"))

# ===== 7) Figures: EMMs & interaction =====
emm_df <- emm_cells
if (!all(c("lower.CL","upper.CL") %in% names(emm_df))) {
  # fallback from SE (rare)
  if (all(c("prob","SE") %in% names(emm_df))) {
    emm_df <- emm_df %>% mutate(
      lower.CL = pmax(0, prob - 1.96 * SE),
      upper.CL = pmin(1, prob + 1.96 * SE)
    )
  } else stop("CI columns not found for plotting.")
}

p_cells <- ggplot(emm_df, aes(x = relation, y = prob, color = condition, group = condition)) +
  geom_point(position = position_dodge(width = 0.35), size = 3) +
  geom_errorbar(aes(ymin = lower.CL, ymax = upper.CL),
                position = position_dodge(width = 0.35), width = 0.2) +
  geom_line(position = position_dodge(width = 0.35), alpha = 0.6) +
  scale_y_continuous(limits = c(0,1), breaks = seq(0,1,0.1)) +
  labs(title = "Estimated cell probabilities (EMMs)", y = "Probability of correct", x = "Relation") +
  theme_minimal(base_size = 12)
ggsave(file.path(out_dir, "emm_cell_probabilities.png"), p_cells, width = 7.5, height = 5, dpi = 300)

p_lines <- ggplot(emm_df, aes(x = relation, y = prob, group = condition, linetype = condition)) +
  geom_line(position = position_dodge(width = 0.35), linewidth = 0.8) +
  geom_point(position = position_dodge(width = 0.35), size = 3) +
  geom_errorbar(aes(ymin = lower.CL, ymax = upper.CL),
                position = position_dodge(width = 0.35), width = 0.2) +
  scale_y_continuous(limits = c(0,1), breaks = seq(0,1,0.1)) +
  labs(title = "Interaction plot (population-level)", y = "Probability", x = "Relation") +
  theme_minimal(base_size = 12)
ggsave(file.path(out_dir, "interaction_plot.png"), p_lines, width = 7.5, height = 5, dpi = 300)

# ===== 8) Supporting models (documented but not primary) =====
# (a) participant × build-order cell random intercept (sensitivity; improves AIC but sparse)
if ("building_order_id" %in% names(df)) {
  m_cell <- tryCatch(
    glmer(
      cbind(k_correct, n_trials - k_correct) ~ relation * condition +
        (1 | participant_id) + (1 | participant_id:building_order_id),
      family = binomial, data = df,
      control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))
    ),
    error = function(e) e
  )
  if (inherits(m_cell, "merMod")) {
    cat("\n== Supporting: participant:building_order_id random intercept ==\n")
    print(summary(m_cell))
    capture.output(summary(m_cell), file = file.path(out_dir, "supporting_cell_RI.txt"))
  } else {
    message("Cell RI model failed: ", m_cell$message)
  }
}

# (b) building_shape as random vs fixed (both 2 levels → expect singular / no lift)
if ("building_shape" %in% names(df)) {
  m_shape_rand <- tryCatch(
    glmer(
      cbind(k_correct, n_trials - k_correct) ~ relation * condition + (1 | participant_id) + (1 | building_shape),
      family = binomial, data = df,
      control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))
    ), error = function(e) e
  )
  if (inherits(m_shape_rand, "merMod")) {
    cat("\n== Supporting: + (1|building_shape) ==\n")
    print(summary(m_shape_rand))
    capture.output(summary(m_shape_rand), file = file.path(out_dir, "supporting_shape_random.txt"))
  }
  m_shape_fix <- tryCatch(
    glmer(
      cbind(k_correct, n_trials - k_correct) ~ relation * condition + building_shape + (1 | participant_id),
      family = binomial, data = df,
      control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))
    ), error = function(e) e
  )
  if (inherits(m_shape_fix, "merMod")) {
    cat("\n== Supporting: + building_shape (fixed) ==\n")
    print(summary(m_shape_fix))
    capture.output(summary(m_shape_fix), file = file.path(out_dir, "supporting_shape_fixed.txt"))
  }
}

# (c) building_order_id as fixed nuisance
if ("building_order_id" %in% names(df)) {
  m_order_fix <- glmer(
    cbind(k_correct, n_trials - k_correct) ~ relation * condition + building_order_id + (1 | participant_id),
    family = binomial, data = df,
    control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))
  )
  cat("\n== Supporting: + building_order_id (fixed) ==\n"); print(summary(m_order_fix))
  capture.output(summary(m_order_fix), file = file.path(out_dir, "supporting_order_fixed.txt"))
}

# (d) VR experience as fixed (between-subjects)
if ("vr_experience" %in% names(df)) {
  m_vr <- glmer(
    cbind(k_correct, n_trials - k_correct) ~ relation * condition + vr_experience + (1 | participant_id),
    family = binomial, data = df,
    control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))
  )
  cat("\n== Supporting: + vr_experience (fixed) ==\n"); print(summary(m_vr))
  capture.output(summary(m_vr), file = file.path(out_dir, "supporting_vr_fixed.txt"))
}

# (e) Post-treatment rotation accuracy (exploratory/mediator; not causal control)
if ("rot_acc_z" %in% names(df)) {
  m_rot <- glmer(
    cbind(k_correct, n_trials - k_correct) ~ relation * condition + rot_acc_z + (1 | participant_id),
    family = binomial, data = df,
    control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))
  )
  cat("\n== Exploratory: + rot_acc_z (mediator; interpret with caution) ==\n"); print(summary(m_rot))
  capture.output(summary(m_rot), file = file.path(out_dir, "exploratory_rot_acc.txt"))
}

# ===== 9) Export a paste-ready one-liner for the Results text =====
# Pull the interaction row on both scales
par_logit <- parameters::model_parameters(m_full_kn, effects = "fixed", ci = 0.95, exponentiate = FALSE)
par_or    <- parameters::model_parameters(m_full_kn, effects = "fixed", ci = 0.95, exponentiate = TRUE)
int_logit <- par_logit %>% filter(grepl("relation.*condition", Parameter))
int_or    <- par_or    %>% filter(grepl("relation.*condition", Parameter))

fmt <- function(x, k=3) format(round(x, k), nsmall = k, trim = TRUE)
txt <- glue::glue(
  "Model performance: R^2_marg = {fmt(r2_full$R2_marginal)}, R^2_cond = {fmt(r2_full$R2_conditional)}, ",
  "ICC = {fmt(icc_full$ICC_adjusted)}, overdispersion phi = {sprintf('%.3f', disp_full$dispersion_ratio)}. ",
  "Interaction (relation × condition): beta = {fmt(int_logit$Coefficient)}, SE = {fmt(int_logit$SE)}, ",
  "p {insight::format_p(int_logit$p)}; OR = {sprintf('%.2f', int_or$Coefficient)}, ",
  "95% CI [{sprintf('%.2f', int_or$CI_low)}, {sprintf('%.2f', int_or$CI_high)}]."
)
writeLines(txt, file.path(out_dir, "thesis_primary_oneliner.txt"))

# Hand-off
assign("winner", m_full_kn, envir = .GlobalEnv)
assign("df", df, envir = .GlobalEnv)
cat("\n=== DONE (primary GLMM + exports to model_outputs/) ===\n")
