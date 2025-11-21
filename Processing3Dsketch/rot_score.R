# 1. Load the necessary package
library(lme4)
library(car) # Recommended for Type II or III ANOVA (Anova function)

# --- Ensure your factor variables are correctly set ---
data$condition <- factor(data$condition)
data$relation <- factor(data$relation)
data$participant <- factor(data$participant)
# Treat rotation_score as numeric, even if it's 0/1/2
data$rotation_score <- as.numeric(data$rotation_score) 

# --- Ensure your reference levels are correct ---
# Set the baseline (reference) for Condition to the NON-ROTATED scenario
# This makes the interaction term specifically test the Rotated condition.
data$condition <- relevel(data$condition, ref = "NonRotated") 


# 2. Define and run the Binomial GLMM

# We include the three-way interaction: condition * relation * rotation_score
# to fully test the conditional effect.
model_hypothesis <- glmer(
  cbind(k_correct, n_trial - k_correct) ~ condition * relation + 
    condition * rotation_score + # Core interaction for hypothesis
    relation * rotation_score +
    condition:relation:rotation_score + # Three-way interaction
    (1 | participant),
  data = data,
  family = binomial
)

# 3. View the model results
summary(model_hypothesis)

# 4. Use Type II or III ANOVA to get omnibus P-values for interactions
# (This is often better than looking at individual coefficient P-values)
Anova(model_hypothesis, type = 3)