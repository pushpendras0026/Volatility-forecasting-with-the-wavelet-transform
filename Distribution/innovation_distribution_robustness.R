# Isolated sensitivity experiment. Never sourced by the production runner.
# All production functions are loaded into a private environment; only that
# environment gains GED dispatch and fit-attempt logging. No production edits.

ged_log_density <- function(z, shape) {
  # Unit variance exponential-power density; shape=2 is N(0,1).
  # a = sqrt(Gamma(1/shape)/Gamma(3/shape)).
  log_a <- .5 * (lgamma(1 / shape) - lgamma(3 / shape))
  log(shape) - log(2) - log_a - lgamma(1 / shape) -
    exp(shape * (log(abs(z)) - log_a))
}

fit_garch11_ged <- function(residuals) {
  e <- check_series(residuals); sc <- sqrt(mean(e^2))
  if (sc < 1e-14) stop('GED shape is not identifiable on zero residuals')
  z <- e / sc
  objective <- function(u) {
    if (any(!is.finite(u)) || any(abs(u) > 30)) return(1e15)
    shape <- exp(u[4])
    # Wide numerical guard, explicitly reported if approached by an estimate.
    if (shape < .1 || shape > 100) return(1e15)
    h <- garch_variances(z, garch_parameters(u[1:3]), 1)
    if (any(!is.finite(h)) || any(h <= 0)) return(1e15)
    value <- -sum(ged_log_density(z / sqrt(h), shape) - .5 * log(h))
    if (is.finite(value)) value else 1e15
  }
  starts <- list(c(log(.05), log(2), log(17), log(2)),
                 c(log(.15), 0, log(.7/.15), log(1.5)))
  fits <- lapply(starts, function(u) tryCatch(
    stats::optim(u, objective, method='BFGS', control=list(maxit=350L)),
    error=function(e) NULL))
  good <- Filter(function(f) !is.null(f) && f$convergence == 0L &&
    is.finite(f$value) && f$value < 1e14, fits)
  if (!length(good)) stop('GED GARCH(1,1) did not converge')
  f <- good[[which.min(vapply(good, function(x) x$value, numeric(1)))]]
  par <- garch_parameters(f$par[1:3]); par['omega'] <- par['omega'] * sc^2
  ll <- -f$value - length(e) * log(sc)
  list(par=par, scale=sc, initial_variance=sc^2, constant=FALSE,
    convergence=f$convergence, shape=exp(f$par[4]), loglik=ll,
    AIC=-2*ll+8, BIC=-2*ll+4*log(length(e)), n=length(e), k=4L,
    method='GED_GARCH11_on_fixed_ARMA_residuals', optim=f)
}

distribution_environment <- function(root) {
  env <- new.env(parent=globalenv())
  for (f in list.files(file.path(root, 'R'), '\\.R$', full.names=TRUE))
    sys.source(f, envir=env)
  sys.source(file.path(root, 'config/experiment.R'), envir=env)
  env$ged_log_density <- ged_log_density
  env$fit_garch11_ged <- fit_garch11_ged
  environment(env$fit_garch11_ged) <- env
  env$production_fit_stat_model <- env$fit_stat_model
  env$fit_stat_model <- eval(quote(function(x, p=0L, q=0L, garch=FALSE,
                                             distribution='gaussian') {
    if (distribution != 'ged')
      return(production_fit_stat_model(x, p, q, garch, distribution))
    mean_model <- fit_mean(x, p, q)
    e <- filter_mean(mean_model, x)$residuals
    variance_model <- if (garch) fit_garch11_ged(e) else NULL
    list(mean=mean_model, variance=variance_model, p=p, q=q, garch=garch,
      distribution=distribution, n=length(x),
      diagnostics=model_diagnostics(e, p, q, variance_model),
      method=if (garch) 'two_step_ARMA_ML_then_GARCH11' else 'ARMA_Gaussian_ML')
  }), env)
  env$fit_attempts <- list()
  env$production_fit_pipeline <- env$fit_pipeline
  env$fit_pipeline <- eval(quote(function(inputs, spec, orders, cfg) {
    # run_forecasts supplies this row. Observing it does not change the loop.
    row <- get('row', envir=parent.frame(), inherits=TRUE)
    entry <- data.frame(dataset=row$dataset, period=row$split,
      model_id=spec$model_id, distribution=spec$distribution,
      origin_date=row$origin_date, train_start=row$train_start,
      train_end=row$train_end, p=unname(orders$x['p']), q=unname(orders$x['q']),
      n=length(inputs$x), converged=FALSE, convergence_code=NA_integer_,
      loglik=NA_real_, AIC=NA_real_, BIC=NA_real_, omega=NA_real_,
      alpha=NA_real_, beta=NA_real_, nu=NA_real_, ged_shape=NA_real_,
      shape_near_guard=FALSE, error='', warning='')
    failure <- NULL; warnings <- character()
    fit <- tryCatch(withCallingHandlers(
      production_fit_pipeline(inputs, spec, orders, cfg),
      warning=function(w) {warnings <<- c(warnings, conditionMessage(w)); invokeRestart('muffleWarning')}),
      error=function(e) {failure <<- conditionMessage(e); NULL})
    entry$warning <- paste(unique(warnings), collapse=' | ')
    if (is.null(failure)) {
      v <- fit$x$variance
      entry$converged <- v$convergence == 0L
      entry$convergence_code <- v$convergence
      for (name in c('loglik', 'AIC', 'BIC')) entry[[name]] <- v[[name]]
      for (name in c('omega', 'alpha', 'beta')) entry[[name]] <- unname(v$par[name])
      if (!is.null(v$nu)) entry$nu <- v$nu
      if (!is.null(v$shape)) {
        entry$ged_shape <- v$shape
        entry$shape_near_guard <- v$shape < .101 || v$shape > 99
      }
    } else entry$error <- failure
    fit_attempts[[length(fit_attempts)+1L]] <<- entry
    if (!is.null(failure)) stop(failure, call.=FALSE)
    fit
  }), env)
  env
}

distribution_job <- function(job, root, baseline, output) {
  env <- distribution_environment(root)
  env$job <- job; env$root <- root; env$baseline <- baseline; env$output <- output
  with(env, {
    set.seed(101L)
    ds <- job$dataset; core <- job$model
    out <- file.path(output, ds, core); ensure_dir(out)
    done <- file.path(out, 'complete.rds')
    if (file.exists(done)) return(readRDS(done))
    plan <- readRDS(file.path(baseline, 'historical/baseline', ds, 'frozen_plan.rds'))
    cfg <- plan$cfg
    stopifnot(is.infinite(cfg$max_origins), cfg$validation_stride == 1L, cfg$test_stride == 1L)
    split <- calendar_split(make_targets(load_prices(root, ds), cfg$mean_window), cfg)
    reg <- plan$registry[plan$registry$model_id == core, , drop=FALSE]
    stopifnot(nrow(reg) == 1L, reg$distribution == 'gaussian', reg$garch)
    reg <- reg[rep(1L, 3L), ]
    reg$distribution <- c('gaussian', 'student_t', 'ged')
    reg$model_id <- paste(core, reg$distribution, sep='__')
    # All components of the core pipeline: x (raw/MODWT/DWT detail) and, for the
    # paired DWT, the approximation a used to condition on r_t.
    ord <- plan$initial_orders[plan$initial_orders$model_id == core, ]
    stopifnot(nrow(ord) >= 1L, 'x' %in% ord$component)
    orders <- setNames(lapply(seq_len(nrow(ord)), function(i) c(p=ord$p[i], q=ord$q[i])), ord$component)
    states <- setNames(lapply(reg$model_id, function(id)
      list(orders=orders, fit=NULL, origin=-Inf)), reg$model_id)
    write_table(reg, file.path(out, 'registry.csv'))
    write_table(ord, file.path(out, 'frozen_orders.csv'))
    write_table(split$dates, file.path(out, 'split.csv'))
    periods <- list(validation=split$validation_indices, test=split$test_indices)
    manifest <- read.csv(file.path(root, 'data/manifest.csv'))
    if (manifest$type[manifest$dataset == ds] == 'stock') periods$later <- split$later_indices
    forecasts <- list(); reproduction <- list()
    for (period in names(periods)) {
      message(ds, '/', core, ': ', period)
      ans <- run_forecasts(split$series, periods[[period]], reg, cfg, ds, period,
                           states, file.path(out, period))
      states <- ans$states; forecasts[[period]] <- ans$forecasts
      # Verify the Gaussian replay against saved production forecasts, including
      # failures, refit cadence, target dates, and the target moment forecasts.
      ref_file <- if (period == 'later') file.path(baseline, 'later/baseline', ds, 'test_forecasts.csv') else
        file.path(baseline, 'historical/baseline', ds, period, 'forecasts.csv')
      reference <- read.csv(ref_file)
      for (distribution in c('gaussian', 'student_t')) {
        old_id <- if (distribution == 'gaussian') core else paste0(core, '_student_t')
        a <- reference[reference$model_id == old_id, ]
        b <- ans$forecasts[ans$forecasts$model_id == paste(core, distribution, sep='__'), ]
        cols <- c('origin_date', 'target_date', 'actual', 'prediction', 'return_mean',
                  'return_variance', 'fit_status', 'refitted', 'mape_threshold', 'train_start', 'train_end')
        a <- a[, cols]; b <- b[, cols]; rownames(a) <- rownames(b) <- NULL
        # Saved CSVs have decimal serialization rounding; 1e-12 relative tolerance.
        check <- all.equal(a, b, tolerance=1e-12, check.attributes=FALSE)
        reproduction[[length(reproduction)+1L]] <- data.frame(dataset=ds, pipeline=core,
          period=period, distribution=distribution, passed=isTRUE(check),
          detail=if (isTRUE(check)) 'Matched saved baseline (CSV tolerance 1e-12)' else paste(check, collapse=' | '))
      }
      write_table(bind_rows_fill(fit_attempts), file.path(out, 'fit_attempts.csv'))
    }
    fc <- bind_rows_fill(forecasts)
    metrics <- calculate_metrics(fc, cfg$mape_threshold)
    # Wall-clock columns vary between re-runs; keep them out of comparison.csv.
    write_table(metrics[, c('dataset', 'split', 'model_id', 'median_seconds', 'total_seconds')], file.path(out, 'timing.csv'))
    metrics <- metrics[, setdiff(names(metrics), c('median_seconds', 'total_seconds'))]
    metrics$pipeline <- core
    metrics$distribution <- reg$distribution[match(metrics$model_id, reg$model_id)]
    attempts <- bind_rows_fill(fit_attempts)
    rows <- list()
    for (i in seq_len(nrow(metrics))) {
      m <- metrics[i, ]; f <- attempts[attempts$period == m$split & attempts$model_id == m$model_id, ]
      first <- f[f$converged, , drop=FALSE]
      if (nrow(first)) first <- first[1L, ]
      # One explicitly dated fit snapshot, never a sum over overlapping windows.
      m$fit_snapshot_origin <- if (nrow(first)) first$origin_date else NA_character_
      m$fit_n <- if (nrow(first)) first$n else NA_integer_
      for (name in c('loglik', 'AIC', 'BIC', 'omega', 'alpha', 'beta', 'nu', 'ged_shape', 'p', 'q'))
        m[[name]] <- if (nrow(first)) first[[name]] else NA_real_
      m$fit_attempts <- nrow(f); m$fit_failures <- sum(!f$converged)
      m$converged <- nrow(f) > 0L && all(f$converged)
      m$forecast_failures <- m$requested - m$successful
      rows[[i]] <- m
    }
    result <- list(comparison=bind_rows_fill(rows), reproduction=bind_rows_fill(reproduction))
    write_table(result$comparison, file.path(out, 'comparison.csv'))
    write_table(result$reproduction, file.path(out, 'baseline_reproduction.csv'))
    saveRDS(result, done)
    result
  })
}

distribution_main <- function(script) {
  experiment <- dirname(normalizePath(script, winslash='/'))
  root <- dirname(experiment)
  args <- commandArgs(trailingOnly=TRUE); workers <- 6L
  if (length(args)) {
    if (length(args) != 2L || args[1] != '--workers') stop('Usage: Rscript innovation_distribution_robustness.R [--workers 6]')
    workers <- as.integer(args[2])
  }
  stopifnot(is.finite(workers), workers >= 1L)
  # LATEST.txt holds a root-relative path; only its basename is used (audit M3).
  baseline <- file.path(root, 'results', basename(trimws(readLines(file.path(root, 'results/LATEST.txt'), warn=FALSE)[1])))
  stopifnot(dir.exists(baseline), file.exists(file.path(baseline, 'RUN_COMPLETE.txt')))
  env <- distribution_environment(root); cfg <- env$experiment_config()
  # Snapshot every existing submission file outside Distribution, including results.
  protected <- list.files(root, recursive=TRUE, full.names=TRUE, all.files=TRUE)
  protected <- protected[!startsWith(normalizePath(protected, winslash='/'), paste0(experiment, '/'))]
  # A concurrently running main job may write its own results folder; protect only
  # code, data and the baseline run this experiment reads.
  protected <- protected[!startsWith(normalizePath(protected, winslash='/'), paste0(normalizePath(file.path(root,'results'), winslash='/'), '/')) |
    startsWith(normalizePath(protected, winslash='/'), paste0(normalizePath(baseline, winslash='/'), '/'))]
  # legacy/ (archived earlier lineage, maintained separately) is not an input.
  protected <- protected[!startsWith(normalizePath(protected, winslash='/'), paste0(normalizePath(root, winslash='/'), '/legacy/'))]
  before <- tools::md5sum(protected)
  sources <- c(list.files(file.path(root, 'R'), full.names=TRUE),
    file.path(root, 'config/experiment.R'), script,
    file.path(experiment, 'tests.R'), file.path(root, 'data/manifest.csv'),
    list.files(file.path(root, 'data'), '\\.csv$', full.names=TRUE, recursive=TRUE),
    file.path(baseline, 'historical/baseline', cfg$dataset_ids, 'frozen_plan.rds'))
  # Root-relative, line-ending-normalized fingerprint: location independent (audit M2).
  cfg$workers <- NULL
  fingerprint <- env$config_fingerprint(cfg, sources, root)
  output <- file.path(experiment, 'results', fingerprint); env$ensure_dir(output)
  env$write_run_metadata(cfg, output)
  env$write_table(data.frame(file=env$relative_path(sources, root), md5_lf=env$normalized_md5(sources)), file.path(output, 'input_checksums.csv'))
  writeLines(file.path('results', basename(baseline)), file.path(output, 'baseline_source.txt'))
  Sys.setenv(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
  jobs <- expand.grid(dataset=cfg$dataset_ids,
    model=c('raw_garch', 'dwt_garch', 'modwt_garch'), stringsAsFactors=FALSE)
  jobs <- lapply(seq_len(nrow(jobs)), function(i) as.list(jobs[i, ]))
  message('Robustness output: ', output, ' | jobs: ', length(jobs), ' | workers: ', workers)
  cl <- parallel::makePSOCKcluster(min(workers, length(jobs)))
  parallel::clusterExport(cl, c('ged_log_density', 'fit_garch11_ged',
    'distribution_environment', 'distribution_job'), envir=environment(distribution_main))
  results <- tryCatch(parallel::parLapplyLB(cl, jobs, function(job, root, baseline, output) {
    tryCatch(distribution_job(job, root, baseline, output), error=function(e)
      list(job_failure=data.frame(dataset=job$dataset, pipeline=job$model, error=conditionMessage(e))))
  }, root=root, baseline=baseline, output=output), finally=parallel::stopCluster(cl))
  comparison <- env$bind_rows_fill(lapply(results, function(x) x$comparison))
  reproduction <- env$bind_rows_fill(lapply(results, function(x) x$reproduction))
  failures <- env$bind_rows_fill(lapply(results, function(x) x$job_failure))
  env$write_table(comparison, file.path(output, 'innovation_distribution_comparison.csv'))
  env$write_table(reproduction, file.path(output, 'baseline_reproduction.csv'))
  env$write_table(failures, file.path(output, 'job_failures.csv'))
  after <- tools::md5sum(protected)
  integrity <- data.frame(file=env$relative_path(protected, root),
    before_md5=unname(before), after_md5=unname(after), unchanged=unname(before == after))
  env$write_table(integrity, file.path(output, 'baseline_integrity.csv'))
  stopifnot(all(integrity$unchanged))
  writeLines(file.path('results', fingerprint), file.path(experiment, 'LATEST.txt'))
  if (nrow(failures)) stop('Some jobs failed; inspect job_failures.csv. Completed jobs are retained.')
  if (!nrow(reproduction) || !all(reproduction$passed)) stop('Baseline replay mismatch; inspect baseline_reproduction.csv.')
  writeLines('Complete; all protected files unchanged and Gaussian/Student-t replays verified.', file.path(output, 'COMPLETE.txt'))
  print(comparison[comparison$split != 'validation', c('dataset', 'pipeline', 'split', 'distribution', 'MSE', 'MAE', 'coverage_pct', 'converged')], row.names=FALSE)
  message('Finished: ', output)
  invisible(output)
}

if (sys.nframe() == 0L) {
  script <- sub('^--file=', '', grep('^--file=', commandArgs(), value=TRUE)[1])
  distribution_main(script)
}
