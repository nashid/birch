# Load required libraries
library(ggplot2)
library(readr)
library(dplyr)

# Load your data
div_data <- read_csv("../bugwise_average_divergence.csv", show_col_types = FALSE)

# Define scaling factor
scaling_factor <- 100

# Preprocess: compute total divergence and hunk groups
div_data <- div_data %>%
  mutate(
    total_divergence = avg_divergence * pair_count,
    scaled_divergence = total_divergence * scaling_factor,
    hunk_group = case_when(
      hunk_count == 2 ~ "2 Hunks",
      hunk_count == 3 ~ "3 Hunks",
      hunk_count >= 4 ~ "4+ Hunks"
    )
  )

div_data$hunk_group <- factor(div_data$hunk_group, levels = c("2 Hunks", "3 Hunks", "4+ Hunks"))

# Compute median for vertical lines
get_density_peak <- function(x) {
  d <- density(x, na.rm = TRUE)
  d$x[which.max(d$y)]
}

modes <- div_data %>%
  group_by(hunk_group) %>%
  summarize(mode_peak = get_density_peak(scaled_divergence), .groups = "drop")

# Define ASE-level color palette
ase_colors <- c("2 Hunks" = "#1f77b4",  # Dark Blue
                "3 Hunks" = "#ff7f0e",  # Orange
                "4+ Hunks" = "#2ca02c") # Green

# Generate density plot
p <- ggplot(div_data, aes(x = scaled_divergence, color = hunk_group, fill = hunk_group)) +
  geom_density(alpha = 0.25, size = 1.2) +
  geom_vline(data = modes, aes(xintercept = mode_peak, color = hunk_group), linetype = "dashed", size = 1) +
  scale_x_log10() +
  labs(
    title = "",
    x = paste0("Total Divergence ×", scaling_factor, " (log scale)"),
    y = "Density",
    color = "Hunk Count",
    fill = "Hunk Count"
  ) +
  theme_minimal(base_size = 14) +
  theme(legend.position = "bottom",
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    axis.line = element_blank()
  ) +
  scale_color_manual(values = ase_colors) +
  scale_fill_manual(values = ase_colors)

# Save to file
dir.create("pdfs", showWarnings = FALSE)
ggsave("pdfs/ASE_Styled_Density_HunkDivergence_Log.pdf", plot = p, width = 7, height = 5)

cat("Saved to pdfs/ASE_Styled_Density_HunkDivergence_Log.pdf\n")
