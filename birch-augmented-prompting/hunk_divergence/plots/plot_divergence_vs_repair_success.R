# Load necessary libraries
library(ggplot2)
library(readr)
library(dplyr)

# Read the CSV
df <- read_csv("../bugwise_average_divergence.csv")

# Ensure the column names are lowercase
colnames(df) <- tolower(colnames(df))

# Convert 'solved' to a factor for plotting
df$solved <- as.factor(df$solved)

# Run Mann-Whitney U Test (Wilcoxon Rank-Sum Test)
test_result <- wilcox.test(avg_divergence ~ solved, data = df)

# Extract p-value
p_val <- signif(test_result$p.value, 4)

# Create boxplot
ggplot(df, aes(x = solved, y = avg_divergence, fill = solved)) +
  geom_boxplot() +
  scale_fill_manual(values = c("FALSE" = "red", "TRUE" = "green")) +
  labs(
    title = paste("Overall Hunk Divergence by Repair Outcome\nWilcoxon Test p =", p_val),
    x = "Bug Solved by LLM",
    y = "Average Hunk Divergence"
  ) +
  scale_x_discrete(labels = c("FALSE" = "Unsolved", "TRUE" = "Solved")) +
  theme_minimal()
