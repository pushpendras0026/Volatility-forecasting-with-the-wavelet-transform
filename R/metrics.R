# metrics.R -- Forecast evaluation on explicit, matched observation keys.
# All calculations use the stored squared-decimal-return target, without rescaling.

score_forecasts <- function(actual, prediction, mape_threshold = 1e-12) {
  stopifnot(is.numeric(actual), is.numeric(prediction),
            length(actual) == length(prediction), length(actual) > 0L,
            all(is.finite(actual)), all(is.finite(prediction)),
            length(mape_threshold) == 1L, is.finite(mape_threshold),
            mape_threshold >= 0)
  error <- actual - prediction
  mse <- mean(error^2)
  total_variation <- sum((actual - mean(actual))^2)
  usable <- abs(actual) > mape_threshold
  data.frame(
    n = length(actual), MSE = mse, RMSE = sqrt(mse),
    MAE = mean(abs(error)),
    # This is predictive R-squared; it is NOT squared correlation.
    R2 = if (total_variation > 0) 1 - sum(error^2) / total_variation else NA_real_,
    MAPE = if (all(usable)) 100 * mean(abs(error / actual)) else NA_real_,
    masked_MAPE = if (any(usable))
      100 * mean(abs(error[usable] / actual[usable])) else NA_real_,
    MAPE_excluded = sum(!usable)
  )
}

.empty_scores <- function() {
  data.frame(n = 0L, MSE = NA_real_, RMSE = NA_real_, MAE = NA_real_,
             R2 = NA_real_, MAPE = NA_real_, masked_MAPE = NA_real_,
             MAPE_excluded = 0L)
}

.forecast_keys <- function(x) {
  cols <- intersect(c("origin_date", "target_date", "horizon", "target_id"), names(x))
  if (!"target_date" %in% cols) stop("Forecasts require target_date")
  do.call(paste, c(lapply(x[cols], as.character), sep = "|"))
}

.valid_forecasts <- function(x) {
  valid <- is.finite(x$actual) & is.finite(x$prediction)
  if ("fit_status" %in% names(x)) {
    # Several runners use 'ok', 'success', 'cached' or an annotated success.
    # Explicit failures cannot be rescued by a finite placeholder prediction.
    status <- tolower(as.character(x$fit_status))
    valid <- valid & !is.na(status) &
      !grepl("failed|failure|error|pending|skipped|timeout|iteration_limit|missing_member", status)
  }
  valid
}

calculate_metrics <- function(forecasts, mape_threshold = 1e-12) {
  required <- c("dataset", "profile", "model_id", "split", "target_date",
                "actual", "prediction")
  if (!all(required %in% names(forecasts)))
    stop("Missing forecast columns: ", paste(setdiff(required, names(forecasts)), collapse = ", "))
  if (!nrow(forecasts)) return(data.frame())
  group_cols <- c("dataset", "profile", "split",
                  intersect("target_id", names(forecasts)))
  grouping <- do.call(paste, c(lapply(forecasts[group_cols], as.character), sep = "|"))
  result <- list()
  for (group in split(forecasts, grouping)) {
    models <- split(group, as.character(group$model_id))
    keys <- lapply(models, .forecast_keys)
    if (any(vapply(keys, anyDuplicated, integer(1L)) > 0L))
      stop("Duplicate forecast keys within a model; join/averaging is ambiguous")
    valid <- lapply(models, .valid_forecasts)
    good_keys <- Map(function(k, v) k[v], keys, valid)
    active <- lengths(good_keys) > 0L
    # A wholly failed optional model is reported but cannot erase the evidence
    # for every other model. Partially failing models remain in the intersection.
    common <- if (any(active)) Reduce(intersect, good_keys[active]) else character()
    requested_union <- Reduce(union, keys)
    observed <- group[is.finite(group$actual), ]
    actual_groups <- split(observed$actual, .forecast_keys(observed))
    if (any(vapply(actual_groups, function(a) max(a) - min(a) >
                   1e-12 * max(1, max(abs(a))), logical(1))))
      stop("Actual target differs between models for an identical forecast key")
    for (id in names(models)) {
      x <- models[[id]]
      keep <- match(common, keys[[id]])
      keep <- keep[!is.na(keep)]
      threshold <- mape_threshold
      if ("mape_threshold" %in% names(x)) {
        values <- unique(x$mape_threshold[is.finite(x$mape_threshold)])
        if (length(values) > 1L) stop("MAPE threshold changed within an experiment")
        if (length(values)) threshold <- values
      }
      common_score <- if (length(keep) && active[[id]])
        score_forecasts(x$actual[keep], x$prediction[keep], threshold) else .empty_scores()
      own_score <- if (any(valid[[id]]))
        score_forecasts(x$actual[valid[[id]]], x$prediction[valid[[id]]], threshold) else .empty_scores()
      header <- x[1L, group_cols, drop = FALSE]
      header$model_id <- id
      header$stage <- if ("stage" %in% names(x)) as.character(x$stage[1L]) else "unspecified"
      header$requested <- nrow(x)
      header$requested_group_dates <- length(requested_union)
      header$successful <- sum(valid[[id]])
      header$coverage_pct <- 100 * sum(valid[[id]]) / max(1L, length(requested_union))
      header$n_common <- length(common)
      header$excluded_from_common_comparison <- !active[[id]]
      header$comparison_status <- if (!active[[id]]) "no successful forecasts" else
        if (!length(common)) "no common successful dates" else "matched dates"
      header$common_start <- if (length(keep)) min(as.character(x$target_date[keep])) else NA_character_
      header$common_end <- if (length(keep)) max(as.character(x$target_date[keep])) else NA_character_
      header$mape_threshold <- threshold
      header$independent_n <- own_score$n
      header$independent_MSE <- own_score$MSE
      header$independent_RMSE <- own_score$RMSE
      header$independent_MAE <- own_score$MAE
      times <- if ("elapsed_seconds" %in% names(x)) x$elapsed_seconds else numeric()
      times <- times[is.finite(times) & times >= 0]
      header$median_seconds <- if (length(times)) median(times) else NA_real_
      header$total_seconds <- if (length(times)) sum(times) else NA_real_
      result[[length(result) + 1L]] <- cbind(header, common_score)
    }
  }
  out <- do.call(rbind, result)
  rownames(out) <- NULL
  out
}

# Error correlations use the same jointly complete date keys. NA is returned for
# constant errors. They describe diversification of model errors, not causation.
forecast_error_matrix <- function(forecasts) {
  models <- split(forecasts, as.character(forecasts$model_id))
  keys <- lapply(models, .forecast_keys)
  good <- lapply(models, .valid_forecasts)
  active <- vapply(good, any, logical(1L))
  models <- models[active]; keys <- keys[active]; good <- good[active]
  if (!length(models)) return(matrix(numeric(), nrow = 0L, ncol = 0L))
  common <- Reduce(intersect, Map(function(k, v) k[v], keys, good))
  values <- lapply(names(models), function(id) {
    x <- models[[id]]; i <- match(common, keys[[id]])
    x$actual[i] - x$prediction[i]
  })
  out <- do.call(cbind, values)
  colnames(out) <- names(models); rownames(out) <- common
  out
}
