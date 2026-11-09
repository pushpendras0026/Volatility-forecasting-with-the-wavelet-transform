script <- sub('^--file=', '', grep('^--file=', commandArgs(), value=TRUE)[1])
experiment <- dirname(normalizePath(script, winslash='/')); root <- dirname(experiment)
source(file.path(experiment, 'innovation_distribution_robustness.R'))
env <- distribution_environment(root)
# Density normalization, unit variance, Gaussian nesting and Laplace special case.
for (shape in c(.7, 1, 1.5, 2, 4)) {
  density <- function(x) exp(ged_log_density(x, shape))
  stopifnot(abs(integrate(density, -Inf, Inf)$value-1) < 1e-6,
    abs(integrate(function(x) x^2*density(x), -Inf, Inf)$value-1) < 1e-6)
}
x <- seq(-5, 5, length.out=101)
stopifnot(max(abs(ged_log_density(x, 2)-dnorm(x, log=TRUE))) < 1e-12,
  max(abs(ged_log_density(x, 1)-(log(sqrt(2)/2)-sqrt(2)*abs(x)))) < 1e-12)
set.seed(719); e <- rt(800, 5)*sqrt(3/5)*.01
ged <- env$fit_garch11_ged(e); scaled <- env$fit_garch11_ged(100*e)
stopifnot(ged$shape > .1, ged$convergence == 0L,
  sum(ged$par[c('alpha','beta')]) < 1,
  abs(env$forecast_garch11(scaled, 100*e)/(1e4*env$forecast_garch11(ged,e))-1) < .002,
  abs((scaled$loglik-ged$loglik)+length(e)*log(100)) < .01)
# Delegated Gaussian/Student-t fitting is exactly the production implementation.
production <- new.env(); sys.source(file.path(root, 'R/models.R'), production)
for (distribution in c('gaussian','student_t'))
  stopifnot(identical(env$fit_stat_model(e, 0, 0, TRUE, distribution),
    production$fit_stat_model(e, 0, 0, TRUE, distribution)))
# Use real unchanged forecast loop: target/prefix invariance and failure isolation.
cfg <- env$experiment_config(); cfg$mape_threshold <- 1e-12
reg <- env$model_registry(cfg); reg <- reg[reg$model_id == 'raw_garch', ]
reg <- reg[rep(1L,3L), ]; reg$distribution <- c('gaussian','student_t','ged')
reg$model_id <- paste0('test_', reg$distribution)
states <- setNames(lapply(reg$model_id,function(id)
  list(orders=list(x=c(p=0L,q=0L)),fit=NULL,origin=-Inf)),reg$model_id)
series <- data.frame(Date=as.Date('2004-01-01')+seq_along(e),r=e,y=e^2)
out <- file.path(tempdir(), 'distribution_test_artifacts'); env$ensure_dir(out)  # never write into the delivered tree (audit m6)
a <- env$run_forecasts(series, 601:602, reg, cfg, 'synthetic', 'test', states, file.path(out,'a'))
changed <- series; changed$r[601:800] <- 10; changed$y[601:800] <- 100
b <- env$run_forecasts(changed, 601, reg, cfg, 'synthetic', 'test', states, file.path(out,'b'))
stopifnot(all(a$forecasts$fit_status == 'ok'),
  identical(a$forecasts$prediction[1:3], b$forecasts$prediction))
env$fit_garch11_ged <- function(residuals) stop('injected GED fitting failure')
failed <- env$run_forecasts(series, 601:602, reg, cfg, 'synthetic', 'test', states, file.path(out,'failure'))
stopifnot(all(failed$forecasts$fit_status[failed$forecasts$model_id=='test_ged']=='failed'),
  all(failed$forecasts$fit_status[failed$forecasts$model_id!='test_ged']=='ok'),
  sum(!env$bind_rows_fill(env$fit_attempts)$converged)==2L)
cat('PASS: GED density, variance, Gaussian nesting, scale equivariance, exact production delegation, causal forecasts, failure isolation.\n')
