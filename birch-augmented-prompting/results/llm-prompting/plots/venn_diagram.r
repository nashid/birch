# 📌 Install Required Libraries
if (!require("ggVennDiagram")) install.packages("ggVennDiagram", dependencies=TRUE)
if (!require("ggplot2")) install.packages("ggplot2", dependencies=TRUE)
library(ggVennDiagram)
library(ggplot2)

# 📌 Load the Data
file_path <- "./llm_bug_passed_mapping.csv"
if (!file.exists(file_path)) stop("❌ Error: llm_bug_passed_mapping.csv not found!")

data <- read.csv(file_path, stringsAsFactors=FALSE)

# 🚨 Ensure required columns exist
if (!all(c("BUG_ID", "LLM") %in% colnames(data))) {
  stop("❌ Error: Required columns ('BUG_ID' and 'LLM') not found!")
}

# 📌 Convert to Named List Format
venn_data <- split(data$BUG_ID, data$LLM)
venn_data <- lapply(venn_data, function(x) unique(as.character(x)))

# 🚩 Set the order of LLMs
techniques_order <- c("Llama3.3", "Mistral-2407", "Nova-pro", "o4-mini", "Gemini-2.5")
venn_data <- venn_data[techniques_order]

# 🚨 Check for empty sets
empty_sets <- names(venn_data)[sapply(venn_data, length) == 0 | sapply(venn_data, is.null)]
if (length(empty_sets) > 0) stop(paste("❌ Error: The following sets are empty:", paste(empty_sets, collapse=", ")))

# 🎨 Create the Venn Diagram using a compatible color scale
venn_plot <- ggVennDiagram(
  venn_data,
  category.names = techniques_order,
  label = "count",
  label_size = 8,
  label_style = list(fontface = "bold"),
  edge_size = 1.5,
  set_size = 11,
  set_style = list(fontface = "bold")
) +
  scale_fill_distiller(palette = "Set2") +  # Use a qualitative color palette
  coord_cartesian(clip = "off") +  # ✅ Allow text to extend beyond plot box
  theme_void() +
  theme(
    plot.background = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "white", color = NA),
    legend.position = "none",
    plot.margin = margin(30, 30, 30, 30)
  )

# 📌 Save the Plot
output_file <- "./venn_llm_model_families.png"
ggsave(output_file, venn_plot, width = 12, height = 10, dpi = 600, bg = "white")

print(paste("✅ Venn Diagram saved at:", output_file))
