# Load required libraries
library(ggplot2)
library(readr)
library(dplyr)

# Load data
div_data <- read_csv("../bugwise_average_divergence.csv", show_col_types = FALSE)

# Compute total divergence and assign hunk group labels
div_data <- div_data %>%
  mutate(
    total_divergence = avg_divergence * pair_count,
    hunk_group = case_when(
      hunk_count == 2 ~ "2 Hunks",
      hunk_count == 3 ~ "3 Hunks",
      hunk_count >= 4 ~ "4+ Hunks"
    )
  )

div_data$hunk_group <- factor(div_data$hunk_group, levels = c("2 Hunks", "3 Hunks", "4+ Hunks"))

# Estimate density peak per group
get_density_peak <- function(x) {
  d <- density(x, na.rm = TRUE)
  d$x[which.max(d$y)]
}

modes <- div_data %>%
  group_by(hunk_group) %>%
  summarize(mode_peak = get_density_peak(total_divergence), .groups = "drop")

# ASE color palette
ase_colors <- c("2 Hunks" = "#1f77b4", "3 Hunks" = "#ff7f0e", "4+ Hunks" = "#2ca02c")

# Generate plot with log scale
p <- ggplot(div_data, aes(x = total_divergence, color = hunk_group, fill = hunk_group)) +
  geom_density(alpha = 0.3, size = 1.1, adjust = 1.5) +  # Smoother curves
  geom_vline(data = modes, aes(xintercept = mode_peak, color = hunk_group), linetype = "dashed", size = 0.8) +
  scale_x_log10() +
  labs(
    x = "Total Divergence (log scale)",
    y = "Density",
    color = "Hunk Count",
    fill = "Hunk Count"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    legend.position = "bottom",
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank()
  ) +
  scale_color_manual(values = ase_colors) +
  scale_fill_manual(values = ase_colors)

# Save plot
dir.create("pdfs", showWarnings = FALSE)
ggsave("pdfs/ASE_HunkDivergence_Density_Log.pdf", plot = p, width = 7, height = 5)

cat("Saved to pdfs/ASE_HunkDivergence_Density_Log.pdf\n")
