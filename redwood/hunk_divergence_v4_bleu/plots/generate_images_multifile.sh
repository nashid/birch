set -x

Rscript plot_divergent.R
Rscript plot_vertical_divergence_components_multifile.R

echo "Plots generated and trimmed successfully!"