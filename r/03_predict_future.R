# Project fitted HFFM probabilities onto a future prepared panel (step1 -> step2).

suppressPackageStartupMessages({
  library(mgcv)
  library(data.table)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 3) {
  stop("Usage: Rscript 03_predict_future.R <model_rds> <step1_csv> <output_csv>")
}
model <- readRDS(args[[1]])
newdata <- fread(args[[2]], data.table = FALSE)
newdata$pred_prob <- predict(model, newdata = newdata, type = "response")
dir.create(dirname(args[[3]]), recursive = TRUE, showWarnings = FALSE)
fwrite(newdata, args[[3]])
message("Wrote ", args[[3]])
