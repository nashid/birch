# Author: <Your Name>
# Purpose: Generate vertical beanplots of divergence components
# Input: ../bugwise_average_divergence.csv
# Output: ./pdfs/Lexical.pdf, Structural.pdf, File.pdf, Divergence.pdf
# Date: 2025-05-25

library(beanplot)

# Read data
df <- read.csv("../bugwise_average_divergence.csv", stringsAsFactors = FALSE)

# Convert relevant columns to numeric
cols <- c("avg_lexical", "avg_ast", "avg_file", "avg_divergence")
df[cols] <- lapply(df[cols], as.numeric)

# Create output directory if it doesn't exist
dir.create("./pdfs", showWarnings = FALSE)

# Define color mapping for visual distinction
colors <- list(
  Lexical    = "#a6cee3",
  Structural = "#b2df8a",
  File       = "#fdbf6f",
  Divergence = "#cab2d6"
)

# Plotting function
plot_bean_vertical <- function(data, column_name, file_name, col_fill) {
  values <- na.omit(data[[column_name]])
  bw_val <- if (length(values) > 200) 0.03 else 0.07

  # Dynamically set y-axis limits
  ymin <- min(values)
  ymax <- max(values)

  pdf_path <- file.path("pdfs", paste0(file_name, ".pdf"))
  pdf(pdf_path, width = 3, height = 5)
  par(mar = c(5, 4, 7, 2), xpd = FALSE, cex.axis = 1.2, cex.lab = 1.4)

  tryCatch({
    beanplot(values,
             col         = col_fill,
             overallline = "median",
             beanlinewd  = 1.2,
             ll          = 0.03,
             horizontal  = FALSE,
             from        = 0,
             cut         = 0,
             bw          = bw_val,
             what        = c(1, 1, 1, 0),
             log         = "",
             yaxt        = "n",
             ylim        = c(ymin, ymax))

    # Add actual dots
    points(rep(1, length(values)), values, pch = ".", col = "#666666", cex = 1)

    # Summary statistics
    med <- median(values)
    mu  <- mean(values)

    axis(2, at = pretty(c(ymin, ymax)), labels = sprintf("%.2f", pretty(c(ymin, ymax))))
    axis(4, at = mu, labels = sprintf("Mean=%.2f", mu))

    # Position median label
    label <- paste0("Md=", round(med, 2))
    if (med >= ymax - 0.06) {
      text(x = 1.25, y = ymax - 0.15, labels = label, cex = 1.4)
    } else if (med <= ymin + 0.06) {
      text(x = 0.7, y = ymin + 0.13, labels = label, cex = 1.4)
    } else {
      text(x = 1.0, y = med + 0.05, labels = label, cex = 1.4)
    }

  }, error = function(e) {
    warning("Failed to plot ", column_name, " — drawing placeholder")
    plot.new()
    title(main = paste("Sparse:", column_name))
  })

  dev.off()
  system(sprintf("pdfcrop --margins '5 5 5 5' '%s' '%s'", pdf_path, pdf_path))
}

# Generate all beanplots
plot_bean_vertical(df, "avg_lexical",    "Lexical",    colors$Lexical)
plot_bean_vertical(df, "avg_ast",        "Structural", colors$Structural)
plot_bean_vertical(df, "avg_file",       "File",       colors$File)
plot_bean_vertical(df, "avg_divergence", "Divergence", colors$Divergence)

cat("All beanplots saved and cropped in ./pdfs/\n")
