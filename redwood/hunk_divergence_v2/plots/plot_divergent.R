# Load required library
library(beanplot)

# Read data
df <- read.csv("../total_hunk_divergence_results.csv")

# Use divergence as-is, on a 0–1 scale
df$DivergentTotal <- as.numeric(df$divergence)

# Function to create a horizontal beanplot
plot_bean <- function(data, column_name, title, file_name, log_scale=FALSE, unit="") {
  values <- data[[column_name]]
  
  # Conditionally format the label
  name_label <- if (unit != "") paste0(title, " (", unit, ")") else title

  # Create PDF output
  pdf(file = paste0("./pdfs/", file_name, ".pdf"), width = 7, height = 3)

  # Create horizontal beanplot
  beanplot(values, col = "#cccccc", log = ifelse(log_scale, "x", ""),
           names = name_label, xaxt = "n",
           overallline = "median", horizontal = TRUE, ll = 0.00001)

  # Compute statistics
  median_val <- round(median(values, na.rm = TRUE), 4)
  mean_val <- round(mean(values, na.rm = TRUE), 4)
  min_val <- round(min(values, na.rm = TRUE), 4)
  max_val <- round(max(values, na.rm = TRUE), 4)
  pct_25 <- round(quantile(values, 0.25, na.rm = TRUE), 4)
  pct_75 <- round(quantile(values, 0.75, na.rm = TRUE), 4)

  # Annotate plot
  text(x = median_val * 1.3, y = 1.2, labels = paste("Md=", median_val, sep=""), cex = 1.2, pos = 4)
  axis(1, at = c(min_val, pct_25, pct_75, max_val), labels = c(min_val, pct_25, pct_75, max_val))
  axis(3, at = mean_val, labels = paste("Mean=", mean_val, sep=""))

  dev.off()

  # Crop the generated PDF
  system(paste("pdfcrop ./pdfs/", file_name, ".pdf ./pdfs/", file_name, "_cropped.pdf", sep=""))
}

# Ensure output directory exists
dir.create("./pdfs", showWarnings = FALSE)

# Generate the divergence score beanplot
plot_bean(df, "DivergentTotal", "Divergence Score", "DivergentTotal", log_scale=FALSE)

cat("Beanplot saved and cropped at './pdfs/DivergentTotal_cropped.pdf'\n")
