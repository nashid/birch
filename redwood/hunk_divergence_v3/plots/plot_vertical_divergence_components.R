# Load required library
library(beanplot)

# Read data
df <- read.csv("../bugwise_average_divergence.csv", stringsAsFactors = FALSE)

# Convert relevant columns to numeric
cols <- c("avg_lexical", "avg_ast", "avg_file", "avg_divergence")
df[cols] <- lapply(df[cols], as.numeric)

# Create output directory if it doesn't exist
dir.create("./pdfs", showWarnings = FALSE)

# Function to create a vertical beanplot with median inside, mean at side
plot_bean_vertical <- function(data, column_name, title, file_name, log_scale = FALSE) {
  # 1) Extract values and drop NAs
  values <- na.omit(data[[column_name]])
  
  # 2) Choose KDE bandwidth
  bw_val <- 0.05
  
  # 3) Open PDF device
  pdf_path <- file.path("pdfs", paste0(file_name, ".pdf"))
  pdf(pdf_path, width = 3, height = 5)
  # par(mar = c(5, 4, 6, 2) + 0.1)  # margins: bottom, left, top, right
  par(mar = c(5, 4, 7, 2))  # Bottom, Left, Top, Right

  tryCatch({
    # 4) Draw the beanplot, restrict KDE to [0,1]
    beanplot(values,
             col         = "#cccccc",
             overallline = "median",
             horizontal  = FALSE,
             from        = 0,
             to          = 1,
             cut         = 0,
             bw          = bw_val,
             what        = c(1, 1, 1, 0),
             log         = ifelse(log_scale, "y", ""),
             yaxt        = "n",
             ylim        = c(0, 1)
    )
    
    # 5) Compute summary stats
    med  <- median(values)
    mu   <- mean(values)
    q25  <- quantile(values, 0.25)
    q75  <- quantile(values, 0.75)
    
    # 6) Y-axis labels
    axis(2, at = c(0, q25, q75, 1),
         labels = c("0", sprintf("%.2f", q25),
                         sprintf("%.2f", q75), "1"))
    
    # 7) Right-side axis: mean only
    axis(4, at = mu,
         labels = sprintf("Mean=%.2f", mu))
    
    # 8) Inline median label
    # text(x = 1, y = min(0.97, med + 0.01),
    #  labels = paste0("md=", round(med, 2)),
    #  pos = 3, cex = 0.9)
    # text(x = 1, y = min(0.94, med + 0.01), 
    #   labels = paste0("md=", round(med, 2)), 
    #   pos = 3, cex = 0.9)

    if (med > 0.95) {
      text(x = 1, y = med - 0.015, labels = paste0("Md=", round(med, 2)), pos = 1, cex = 0.9)
    } else {
      text(x = 1, y = med + 0.01, labels = paste0("Md=", round(med, 2)), pos = 3, cex = 0.9)
    }

    # Overlay raw data points
    # points(rep(1, length(values)), values,
    #        pch = 16, col = "#666666", cex = 0.2)

    # 9) Title
    # title(main = title, line = 4)
    
  }, error = function(e) {
    warning("Failed to plot ", column_name, " — drawing placeholder")
    plot.new()
    title(main = paste("Sparse:", title))
  })
  
  dev.off() 
  
  # 10) Crop whitespace
  system(sprintf("pdfcrop --margins '5 5 5 5' '%s' '%s'", pdf_path, pdf_path))
}

# Generate beanplots for each column
plot_bean_vertical(df, "avg_lexical",    "Divergence (Lexical)",  "Lexical")
plot_bean_vertical(df, "avg_ast",        "Divergence (AST)",      "Structural")
plot_bean_vertical(df, "avg_file",       "Divergence (File)",     "File")
plot_bean_vertical(df, "avg_divergence", "Overall Divergence",    "Divergence")

# Final message
cat("All beanplots saved and cropped in ./pdfs/\n")
