# Load required library
library(beanplot)

# Read data
df <- read.csv("../bugwise_average_divergence.csv")

# Convert relevant columns to numeric
cols <- c("avg_lexical", "avg_ast", "avg_package", "avg_divergence")
df[cols] <- lapply(df[cols], as.numeric)

# Function to create a vertical beanplot
plot_bean_vertical <- function(data, column_name, title, file_name, log_scale=FALSE, unit="") {
  values <- data[[column_name]]
  name_label <- if (unit != "") paste0(title, " (", unit, ")") else title

  pdf(file = paste0("./pdfs/", file_name, ".pdf"), width = 3, height = 5)

  tryCatch({
    beanplot(values, col = "#cccccc", log = ifelse(log_scale, "y", ""),
             names = name_label, yaxt = "n", overallline = "median",
             horizontal = FALSE, ll = 0.00001,
             what = if (column_name == "avg_package") c(1, 0, 0, 0) else c(1, 1, 1, 0),
             bwmode = if (column_name == "avg_package") "none" else "auto")
    
    # Compute statistics
    median_val <- round(median(values, na.rm = TRUE), 4)
    mean_val <- round(mean(values, na.rm = TRUE), 4)
    min_val <- round(min(values, na.rm = TRUE), 4)
    max_val <- round(max(values, na.rm = TRUE), 4)
    pct_25 <- round(quantile(values, 0.25, na.rm = TRUE), 4)
    pct_75 <- round(quantile(values, 0.75, na.rm = TRUE), 4)

    # Annotate plot
    text(x = 1.2, y = median_val * 1.1, labels = paste("Md=", median_val), cex = 1.0, pos = 3)
    axis(2, at = c(min_val, pct_25, pct_75, max_val), labels = c(min_val, pct_25, pct_75, max_val))
    axis(4, at = mean_val, labels = paste("Mean=", mean_val))
  }, error = function(e) {
    warning(paste("Failed to plot", column_name, "due to sparse data."))
    plot(1, type = "n", axes = FALSE, xlab = "", ylab = "")
    title(main = paste("Sparse:", title))
  })

  dev.off()
  system(paste("pdfcrop ./pdfs/", file_name, ".pdf ./pdfs/", file_name, "_cropped.pdf", sep=""))
}

# Ensure output directory exists
dir.create("./pdfs", showWarnings = FALSE)

# Generate beanplots for each divergence dimension
plot_bean_vertical(df, "avg_lexical", "Divergence (Lexical)", "AvgLexical")
plot_bean_vertical(df, "avg_ast", "Divergence (AST)", "AvgAST")
plot_bean_vertical(df, "avg_package", "Divergence (Package)", "AvgPackage")
plot_bean_vertical(df, "avg_divergence", "Divergence", "AvgDivergence")

cat("Vertical beanplots saved and cropped in ./pdfs/\n")
