# Install packages
# install.packages("ggalluvial", repos = "https://cloud.r-project.org")

# Load necessary libraries
library(readr)
library(dplyr)
library(stringr)
library(ggplot2)
library(ggalluvial)

# Load your CSVs
llm_data <- read_csv("llm_bug_passed_mapping.csv")
prox_data <- read_csv("proximity_class.csv")

# Standardize bug IDs to match
llm_data <- llm_data %>%
  mutate(bug_id = str_replace_all(BUG_ID, "-", "_")) %>%
  select(LLM, bug_id)

# Merge the datasets on bug_id
merged <- llm_data %>%
  inner_join(prox_data, by = "bug_id")

# Count flows between Proximity Class and LLM
flow_counts <- merged %>%
  count(proximity_class, LLM, name = "value")

# Set custom order for Proximity Class
flow_counts$proximity_class <- factor(flow_counts$proximity_class,
  levels = c("Nucleus", "Cluster", "Orbit", "Sprawl", "Fragment"))

# Plot with wider strata boxes for readability
p <- ggplot(flow_counts,
            aes(axis1 = proximity_class, axis2 = LLM, y = value)) +
  geom_alluvium(aes(fill = proximity_class), width = 0.25, alpha = 0.85) +  # Wider flows
  geom_stratum(width = 0.25, fill = "grey90", color = "black") +            # Wider boxes
  geom_text(stat = "stratum", aes(label = after_stat(stratum)),
            size = 5.5, fontface = "bold", hjust = 0.5) +                    # Centered text
  scale_x_discrete(limits = c("Proximity Class", "LLM"),
                   expand = c(.05, .05)) +
  theme_minimal(base_size = 16) +
  theme_void() +
  theme(legend.position = "none")

# Save to PDF
ggsave("proximity_class_llm_sankey.pdf", plot = p,
       width = 11, height = 7, units = "in")


# Save to PDF
# ggsave("proximity_class_llm_sankey.pdf", plot = p, width = 10, height = 6)
