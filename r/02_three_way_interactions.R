# Three-way thermal-flood interactions with elevation, population and NDVI.
# These models correspond to Supplementary Fig. 4 / Supplementary Table 5.

suppressPackageStartupMessages({
  library(mgcv)
  library(data.table)
  library(ggplot2)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  stop("Usage: Rscript 02_three_way_interactions.R <input_csv> <output_dir>")
}
input_csv <- args[[1]]
output_dir <- args[[2]]
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

df <- fread(input_csv, data.table = FALSE)
df$mean_elevation[df$mean_elevation < 0] <- 0
df$overheat_log <- log1p(df$overheat_penalty_days)
df$elev_log <- log1p(df$mean_elevation)
df$pop_log <- log1p(df$pop_density)
df$thermal_scaled <- as.numeric(scale(df$thermal_suitability_integral))
df$flood_scaled <- df$flood_activation_index

fit_interact <- function(z_term, rhs_extra) {
  fml <- as.formula(paste0(
    "dcz_occ ~ te(thermal_scaled, flood_scaled, ", z_term, ", k = c(5, 5, 5)) + ",
    "s(overheat_log, k = 5) + offset(surveillance_offset) + s(year, k = 5) + ",
    "s(X, Y, bs = 'tp') + ", rhs_extra
  ))
  bam(fml, data = df, family = binomial(link = "logit"), discrete = TRUE, nthreads = 4)
}

model_elev <- fit_interact("elev_log", "s(mean_NDVI, k = 5) + s(pop_log, k = 5)")
model_pop  <- fit_interact("pop_log",  "s(mean_NDVI, k = 5) + s(elev_log, k = 5)")
model_ndvi <- fit_interact("mean_NDVI", "s(pop_log, k = 5) + s(elev_log, k = 5)")

capture.output(summary(model_elev), file = file.path(output_dir, "summary_elev.txt"))
capture.output(summary(model_pop),  file = file.path(output_dir, "summary_pop.txt"))
capture.output(summary(model_ndvi), file = file.path(output_dir, "summary_ndvi.txt"))
saveRDS(model_elev, file.path(output_dir, "hffm_elev_interact.rds"))
saveRDS(model_pop,  file.path(output_dir, "hffm_pop_interact.rds"))
saveRDS(model_ndvi, file.path(output_dir, "hffm_ndvi_interact.rds"))

base_grid <- expand.grid(
  thermal_scaled = seq(min(df$thermal_scaled, na.rm = TRUE), max(df$thermal_scaled, na.rm = TRUE), length.out = 80),
  flood_scaled   = seq(min(df$flood_scaled, na.rm = TRUE), max(df$flood_scaled, na.rm = TRUE), length.out = 80),
  pop_log        = median(df$pop_log, na.rm = TRUE),
  overheat_log   = median(df$overheat_log, na.rm = TRUE),
  surveillance_offset = median(df$surveillance_offset, na.rm = TRUE),
  year           = median(df$year, na.rm = TRUE),
  X              = median(df$X, na.rm = TRUE),
  Y              = median(df$Y, na.rm = TRUE),
  mean_NDVI      = median(df$mean_NDVI, na.rm = TRUE),
  elev_log       = median(df$elev_log, na.rm = TRUE)
)

predict_surface <- function(model, grid, z_name, z_values, z_labels, exclude) {
  pieces <- lapply(seq_along(z_values), function(i) {
    tmp <- grid
    tmp[[z_name]] <- z_values[[i]]
    tmp$Predicted_Risk <- predict(model, newdata = tmp, exclude = exclude, type = "response")
    tmp$facet <- z_labels[[i]]
    tmp
  })
  do.call(rbind, pieces)
}

elev_m <- c(500, 1000, 2000, 3000)
plot_elev <- predict_surface(
  model_elev, base_grid, "elev_log", log1p(elev_m), paste0(elev_m, " m"),
  c("s(X,Y)", "s(year)", "s(mean_NDVI)", "s(pop_log)", "s(overheat_log)")
)
pop_d <- c(2000, 4000, 6000, 8000)
plot_pop <- predict_surface(
  model_pop, base_grid, "pop_log", log1p(pop_d), paste0(pop_d, " people/km2"),
  c("s(X,Y)", "s(year)", "s(mean_NDVI)", "s(elev_log)", "s(overheat_log)")
)
ndvi_q <- as.numeric(quantile(df$mean_NDVI, probs = c(0.1, 0.2, 0.3, 0.4), na.rm = TRUE))
plot_ndvi <- predict_surface(
  model_ndvi, base_grid, "mean_NDVI", ndvi_q,
  paste0("NDVI = ", round(ndvi_q, 3)),
  c("s(X,Y)", "s(year)", "s(pop_log)", "s(elev_log)", "s(overheat_log)")
)

save_plot <- function(dat, file) {
  p <- ggplot(dat, aes(x = thermal_scaled, y = flood_scaled, z = Predicted_Risk)) +
    geom_contour_filled() +
    facet_wrap(~ facet, nrow = 1) +
    theme_minimal(base_size = 9)
  ggsave(file, p, width = 12, height = 4)
}

save_plot(plot_elev, file.path(output_dir, "interaction_elevation.svg"))
save_plot(plot_pop,  file.path(output_dir, "interaction_population.svg"))
save_plot(plot_ndvi, file.path(output_dir, "interaction_ndvi.svg"))
message("Wrote interaction models and surfaces to ", output_dir)
