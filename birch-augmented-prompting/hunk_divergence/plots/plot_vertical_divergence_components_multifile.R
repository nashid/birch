# Author: <Your Name>
# Purpose: Generate vertical beanplots of divergence components
# Input: ../bugwise_average_divergence.csv
# Output: ./pdfs/Lexical_multifile.pdf, Structural_multifile.pdf, File_multifile.pdf, Divergence_multifile.pdf
# Date: 2025-05-25

library(beanplot)

# Read data
df <- read.csv("../multifile_bugwise_average_divergence.csv", stringsAsFactors = FALSE)

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

  pdf_path <- file.path("pdfs", paste0(file_name, ".pdf"))
  pdf(pdf_path, width = 3, height = 5)
  # par(mar = c(5, 4, 7, 2))  # Bottom, Left, Top, Right
  par(mar = c(5, 4, 7, 2), xpd = FALSE, cex.axis = 1.2, cex.lab = 1.4)  # ✅ Increase font size

  tryCatch({
    beanplot(values,
             col         = col_fill,
             overallline = "median",
             beanlinewd  = 1.2,
             ll          = 0.03,
             horizontal  = FALSE,
             from        = 0,
             to          = 1,
             cut         = 0,
             bw          = bw_val,
             what        = c(1, 1, 1, 0),  # KDE + mean + median (no lines)
             log         = "",
             yaxt        = "n",
             ylim        = c(0, 1))

    # ✅ Add actual dots inside the beanplot
    points(rep(1, length(values)), values, pch = ".", col = "#666666", cex = 1)

    # Summary statistics
    med <- median(values)
    mu  <- mean(values)

    axis(2, at = seq(0, 1, 0.2), labels = sprintf("%.1f", seq(0, 1, 0.2)))
    axis(4, at = mu, labels = sprintf("Mean=%.2f", mu))


    # Get plot bounds (y-axis limits)
    # Compute safe vertical position manually
    ymin <- par("usr")[3]
    ymax <- par("usr")[4]
    label <- paste0("Md=", round(med, 2))

    if (med >= 0.94) {
      # Top: draw just below top
      text(x = 1.25, y = ymax - 0.15, labels = label, cex = 1.4)
    } else if (med <= 0.02) {
      # Bottom: draw slightly above bottom
      text(x = 0.7, y = ymin + 0.13, labels = label, cex = 1.4)
    } else {
      # Middle: draw above median
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
plot_bean_vertical(df, "avg_lexical",    "Lexical_multifile",    colors$Lexical)
plot_bean_vertical(df, "avg_ast",        "Structural_multifile", colors$Structural)
plot_bean_vertical(df, "avg_file",       "File_multifile",       colors$File)
plot_bean_vertical(df, "avg_divergence", "Divergence_multifile", colors$Divergence)

cat("All beanplots saved and cropped in ./pdfs/\n")
