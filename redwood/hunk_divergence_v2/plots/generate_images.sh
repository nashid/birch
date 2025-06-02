set -x

Rscript plot_divergent.R
Rscript plot_vertical_divergence_components.R

mv total_cost_cropped.pdf ./pdfs

magick ./pdfs/total_cost_cropped.pdf -trim +repage ./pdfs/total_cost_cropped.pdf

echo "Plots generated and trimmed successfully!"