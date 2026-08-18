# Fit the Habitat-Flood Flexible Model on the historical DCZ panel.
# Expected input: Panel_with_IPCC_Region_FINAL.csv or an equivalent 0.5-degree panel.

suppressPackageStartupMessages({
  library(mgcv)
  library(data.table)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  stop("Usage: Rscript 01_fit_hffm.R <input_csv> <output_rds>")
}
input_csv <- args[[1]]
output_rds <- args[[2]]

df <- fread(input_csv, data.table = FALSE)
df$mean_elevation[df$mean_elevation < 0] <- 0
df$overheat_log <- log1p(df$overheat_penalty_days)
df$elev_log <- log1p(df$mean_elevation)
df$pop_log <- log1p(df$pop_density)
df$thermal_scaled <- as.numeric(scale(df$thermal_suitability_integral))
df$flood_scaled <- df$flood_activation_index

model_hffm <- bam(
  dcz_occ ~
    te(thermal_scaled, flood_scaled, k = c(5, 5)) +
    s(overheat_log, k = 5) +
    offset(surveillance_offset) +
    s(year, k = 5) +
    s(X, Y, bs = "tp") +
    s(mean_NDVI, k = 5) +
    s(elev_log, k = 5) +
    s(pop_log, k = 5),
  data = df,
  family = binomial(link = "logit"),
  discrete = TRUE,
  nthreads = 4
)

print(summary(model_hffm))
dir.create(dirname(output_rds), recursive = TRUE, showWarnings = FALSE)
saveRDS(model_hffm, output_rds)
message("Wrote ", output_rds)
