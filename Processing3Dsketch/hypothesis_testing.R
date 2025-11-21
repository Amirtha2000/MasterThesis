# ==== Setup ====
stopifnot(all(c("k_correct","n_trials","relation","condition","participant_id") %in% names(df)))

df <- within(df, {
  relation       <- relevel(factor(relation),  ref = "H")  # H as ref
  condition      <- relevel(factor(condition), ref = "Aligned")
  participant_id <- factor(participant_id)
})

library(lme4)
library(emmeans)

# ==== Primary GLMM (keep your preregistered structure) ====
m_full <- glmer(
  cbind(k_correct, n_trials - k_correct) ~ relation * condition + (1 | participant_id),
  family = binomial, data = df,
  control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))
)

# ==== Report "relation" averaged over condition ====
emm_rel <- emmeans(m_full, ~ relation, type = "response")   # averages over condition
rel_contrast <- pairs(emm_rel, type = "response")            # H vs V: OR, z, p

print(emm_rel)       # p(H), p(V) with 95% CI (probability scale)
print(rel_contrast)  # odds ratio H/V, SE, z, p

# Optional: export a tidy table
out <- cbind(as.data.frame(emm_rel),
             contrast = as.data.frame(rel_contrast))
# write.csv(out, "model_outputs/relation_only_k_overall.csv", row.names = FALSE)

# ==== Minimal publication plot (two points with 95% CI) ====
library(ggplot2)
pd <- as.data.frame(emm_rel)
pd$relation <- factor(pd$relation, levels = c("H","V"))

p_rel <- ggplot(pd, aes(x = relation, y = prob)) +
  geom_point(size = 3) +
  geom_errorbar(aes(ymin = asymp.LCL, ymax = asymp.UCL), width = 0.08) +
  scale_y_continuous(limits = c(0,1), breaks = seq(0,1,0.1)) +
  labs(x = "Relation", y = "Estimated P(Correct)",
       title = "Horizontal vs Vertical (EMMs averaged over condition)") +
  theme_minimal(base_size = 12) +
  theme(axis.title.x = element_text(face = "bold"),
        axis.title.y = element_text(face = "bold"))
# ggsave("model_outputs/relation_only_emm.png", p_rel, width = 5.5, height = 4.2, dpi = 300)
p_rel
