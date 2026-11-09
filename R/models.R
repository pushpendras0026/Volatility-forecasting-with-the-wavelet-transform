# Statistical forecasting functions. Only base R is required.
#
# ARMA parameters use Gaussian ML. GARCH(1,1) is fitted in a SECOND STEP to
# the ARMA residuals, not by joint ARMA-GARCH maximum likelihood. This choice
# is recorded in every model object and must remain explicit in the report.
# Between parameter refits, residuals and variance states are updated from the
# entire supplied past prefix. A forecast never reuses yesterday's stale state.

check_series <- function(x, minimum = 20L) {
  x <- as.numeric(x)
  if (length(x) < minimum || any(!is.finite(x)))
    stop("A finite numeric series with at least ", minimum, " observations is required")
  x
}

# Exact Gaussian ML for the mean model. Scaling uses training data only.
fit_mean <- function(x, p = 0L, q = 0L) {
  x <- check_series(x)
  p <- as.integer(p); q <- as.integer(q)
  if (p < 0L || q < 0L || length(x) <= 3L * (p + q + 1L))
    stop("Invalid or excessive ARMA orders")
  scale <- stats::sd(x)
  if (!is.finite(scale) || scale <= .Machine$double.eps * max(1, abs(mean(x)))) {
    if (p != 0L || q != 0L) stop("Only the constant model is identifiable on constant data")
    return(list(p = 0L, q = 0L, scale = 1, coef = c(intercept = mean(x)),
                sigma2 = 0, fit = NULL, constant = TRUE, n = length(x),
                k = 2L, loglik = NA_real_, AIC = NA_real_, BIC = NA_real_,
                convergence = 0L, method = "constant_series"))
  }
  z <- x / scale
  attempt <- function(method, ss = "Gardner1980") tryCatch(
    suppressWarnings(stats::arima(z, order = c(p, 0L, q), include.mean = TRUE,
      method = method, SSinit = ss, optim.control = list(maxit = 300L))),
    error = function(e) NULL)
  fit <- attempt("CSS-ML")
  admissible_roots <- function(f) {
    cf <- stats::coef(f)
    ar_ok <- if (p) all(Mod(polyroot(c(1, -cf[paste0("ar", seq_len(p))]))) > 1 + 1e-8) else TRUE
    ma_ok <- if (q) all(Mod(polyroot(c(1, cf[paste0("ma", seq_len(q))]))) > 1 + 1e-8) else TRUE
    isTRUE(ar_ok && ma_ok)
  }
  good <- function(f) !is.null(f) && (is.null(f$code) || f$code == 0L) &&
    all(is.finite(stats::coef(f))) && is.finite(f$loglik) && is.finite(f$sigma2) &&
    admissible_roots(f)
  method <- "CSS-ML"
  if (!good(fit)) { fit <- attempt("ML", "Rossignol2011"); method <- "ML_Rossignol2011" }
  if (!good(fit)) stop(sprintf("ARMA(%d,%d) failed to converge under ML", p, q))
  # Restore likelihood to the original input units (Jacobian of x/scale).
  n <- length(x); k <- length(stats::coef(fit)) + 1L
  ll <- as.numeric(fit$loglik) - n * log(scale)
  list(p = p, q = q, scale = scale, coef = stats::coef(fit),
       sigma2 = fit$sigma2 * scale^2, fit = fit, constant = FALSE,
       n = n, k = k, loglik = ll, AIC = -2 * ll + 2 * k,
       BIC = -2 * ll + log(n) * k, convergence = 0L, method = method)
}

# Refilter with fixed fitted coefficients using the exact Gaussian state-space
# initialization used for estimation. Zero-start MA recursion is unsafe for
# Haar differences: an MA root near one retains its initialization error across
# the entire training window. No parameters are re-estimated here.
filter_mean <- function(fit, x) {
  x <- check_series(x)
  if (isTRUE(fit$constant)) return(list(residuals=x-fit$coef[["intercept"]],mu=fit$coef[["intercept"]]))
  state <- stats::arima(x / fit$scale, order=c(fit$p,0L,fit$q),
    include.mean=TRUE, fixed=fit$coef, transform.pars=FALSE, method="ML",
    SSinit=if(identical(fit$method,"ML_Rossignol2011")) "Rossignol2011" else "Gardner1980")
  e <- as.numeric(stats::residuals(state))*fit$scale
  mu <- as.numeric(stats::predict(state,n.ahead=1L)$pred)*fit$scale
  if(any(!is.finite(e)) || !is.finite(mu)) stop("Nonfinite exact ARMA state")
  list(residuals=e,mu=mu)
}

forecast_mean <- function(fit, x) {
  state <- filter_mean(fit, x)
  list(mu = state$mu, h = fit$sigma2, residuals = state$residuals)
}

select_arma <- function(x, max_pq = 3L, criterion = "AIC", diagnostics=FALSE) {
  criterion <- match.arg(toupper(criterion), c("AIC", "BIC"))
  x <- check_series(x)
  grid <- vector("list", (max_pq + 1L)^2L)
  best <- NULL; k <- 0L
  for (p in 0:max_pq) for (q in 0:max_pq) {
    k <- k + 1L
    error <- ""
    fit <- tryCatch(fit_mean(x, p, q), error = function(e) { error <<- conditionMessage(e); NULL })
    grid[[k]] <- data.frame(p = p, q = q,
      AIC = if (is.null(fit)) NA_real_ else fit$AIC,
      BIC = if (is.null(fit)) NA_real_ else fit$BIC,
      loglik = if (is.null(fit)) NA_real_ else fit$loglik,
      n = length(x), k = if (is.null(fit)) NA_integer_ else fit$k,
      converged = !is.null(fit), message = error, stringsAsFactors = FALSE)
    if(diagnostics) {
      d <- if(is.null(fit)) model_diagnostics(rep(0,length(x)),p,q) else
        model_diagnostics(filter_mean(fit,x)$residuals,p,q)
      names(d)[names(d)=="n"] <- "diagnostic_n"
      grid[[k]] <- cbind(grid[[k]],d)
    }
    if (!is.null(fit) && (is.null(best) ||
        (is.finite(fit[[criterion]]) &&
         (!is.finite(best$fit[[criterion]]) || fit[[criterion]] < best$fit[[criterion]]))))
      best <- list(p = p, q = q, fit = fit)
  }
  if (is.null(best)) stop("Every ARMA candidate failed")
  best$grid <- do.call(rbind, grid)
  best$criterion <- criterion
  best
}

# Positive, covariance-stationary parameter map. Softmax leaves positive slack
# below alpha+beta=1. It does not reproduce the nonstationary Nigeria estimates
# printed in the paper, which are flagged in the reproduction notes.
garch_parameters <- function(u) {
  a <- exp(u[2L]); b <- exp(u[3L]); den <- 1 + a + b
  c(omega = exp(u[1L]), alpha = a / den, beta = b / den)
}

garch_variances <- function(e, par, initial_variance) {
  n <- length(e)
  drive <- par[["omega"]] + par[["alpha"]] * c(0, head(e, -1L)^2)
  drive[1L] <- initial_variance
  as.numeric(stats::filter(drive, par[["beta"]], method = "recursive", init = 0))
}

fit_garch11 <- function(residuals) {
  e <- check_series(residuals)
  scale <- sqrt(mean(e^2))
  if (!is.finite(scale) || scale < 1e-14) {
    return(list(par = c(omega = 0, alpha = 0, beta = 0), scale = 1,
      initial_variance = 0, constant = TRUE, convergence = 0L,
      loglik = NA_real_, AIC = NA_real_, BIC = NA_real_, n = length(e),
      k = 3L, method = "zero_residual_variance"))
  }
  z <- e / scale
  objective <- function(u) {
    if (any(!is.finite(u)) || any(abs(u) > 30)) return(1e15)
    par <- garch_parameters(u)
    h <- garch_variances(z, par, 1)
    if (any(!is.finite(h)) || any(h <= 0)) return(1e15)
    0.5 * sum(log(2 * pi) + log(h) + z^2 / h)
  }
  starts <- list(c(log(.05), log(.10/.05), log(.85/.05)),
                 c(log(.15), log(.15/.15), log(.70/.15)))
  fits <- lapply(starts, function(u) tryCatch(
    stats::optim(u, objective, method = "BFGS", control = list(maxit = 250L)),
    error = function(e) NULL))
  good <- vapply(fits, function(f) !is.null(f) && f$convergence == 0L &&
                   is.finite(f$value) && f$value < 1e14, logical(1L))
  if (!any(good)) stop("GARCH(1,1) did not converge")
  fit <- fits[good][[which.min(vapply(fits[good], function(z) z$value, numeric(1L)))]]
  par <- garch_parameters(fit$par)
  par[["omega"]] <- par[["omega"]] * scale^2
  ll <- -fit$value - length(e) * log(scale)
  list(par = par, scale = scale, initial_variance = scale^2, constant = FALSE,
       convergence = fit$convergence, loglik = ll,
       AIC = -2 * ll + 6, BIC = -2 * ll + 3 * log(length(e)), n = length(e), k = 3L,
       method = "Gaussian_GARCH11_on_fixed_ARMA_residuals", optim = fit)
}

forecast_garch11 <- function(fit, residuals) {
  e <- check_series(residuals)
  if (isTRUE(fit$constant)) return(0)
  h <- garch_variances(e, fit$par, fit$initial_variance)
  ans <- fit$par[["omega"]] + fit$par[["alpha"]] * tail(e, 1L)^2 +
    fit$par[["beta"]] * tail(h, 1L)
  if (!is.finite(ans) || ans <= 0) stop("Invalid GARCH forecast variance")
  as.numeric(ans)
}

fit_stat_model <- function(x, p = 0L, q = 0L, garch = FALSE, distribution="gaussian") {
  stopifnot(distribution %in% c("gaussian","student_t"))
  mean_model <- fit_mean(x, p, q)
  # Exact state initialization is shared by estimation and state updating.
  e <- filter_mean(mean_model, x)$residuals
  variance_model <- if (garch) {if(distribution=="student_t") fit_garch11_t(e) else fit_garch11(e)} else NULL
  diagnostics <- model_diagnostics(e, p, q, variance_model)
  list(mean = mean_model, variance = variance_model, p = p, q = q,
       garch = garch, distribution=distribution, n = length(x),
       diagnostics = diagnostics,
       method = if (garch) "two_step_ARMA_ML_then_GARCH11" else "ARMA_Gaussian_ML")
}

# Auxiliary lag regression, as in acorr_lm / Engle ARCH diagnostics.
# F uses its usual regression reference; LM uses (n-ddof)*R^2. These are
# approximate diagnostics on estimated ARMA residuals, not exact finite-sample tests.
residual_lag_test <- function(e, lags=12L, squared=FALSE, ddof=0L, alpha=.05) {
  empty <- data.frame(aux_n=NA_integer_,F=NA_real_,F_p=NA_real_,df1=NA_integer_,
    df2=NA_integer_,LM=NA_real_,LM_p=NA_real_,decision="Not testable")
  if(any(!is.finite(e))||length(e)<=2*lags+2||sd(e)==0) return(empty)
  e <- e/sd(e) # Regression tests are invariant to response scale.
  if(squared) e <- e^2
  z <- embed(e,lags+1L); y <- z[,1]; X <- cbind(1,z[,-1,drop=FALSE])
  fit <- lm.fit(X,y); n <- length(y); k <- fit$rank
  if(k!=ncol(X)||n<=k||sum((y-mean(y))^2)<=0) return(empty)
  rss <- sum(fit$residuals^2); tss <- sum((y-mean(y))^2)
  r2 <- max(0,min(1,1-rss/tss)); F <- (max(0,tss-rss)/lags)/(rss/(n-k))
  fp <- pf(F,lags,n-k,lower.tail=FALSE); LM <- max(0,n-ddof)*r2
  data.frame(aux_n=n,F=F,F_p=fp,df1=lags,df2=n-k,LM=LM,
    LM_p=pchisq(LM,lags,lower.tail=FALSE),
    decision=if(fp<alpha) "Significant" else "Not significant")
}

# Residual checks are descriptive, not automatic proof that a model is correct.
# For GARCH, inspect standardized residuals, not raw residuals with changing scale.
model_diagnostics <- function(residuals, p = 0L, q = 0L, variance_fit = NULL) {
  e <- residuals
  if (!is.null(variance_fit) && !isTRUE(variance_fit$constant)) {
    h <- garch_variances(e, variance_fit$par, variance_fit$initial_variance)
    e <- e / sqrt(h)
  }
  # Exclude the declared max(p,q) startup observations for diagnostics.
  burn <- max(p, q)
  if (burn > 0L) e <- e[-seq_len(burn)]
  lag <- min(length(e) - 1L, max(24L, p + q + 5L))
  lb <- lb2 <- Q <- Q2 <- NA_real_
  if (length(e) > p + q + 5L && stats::sd(e) > 0) {
    b <- tryCatch(stats::Box.test(e,lag=lag,type="Ljung-Box",fitdf=p+q),error=function(e)NULL)
    b2 <- tryCatch(stats::Box.test(e^2,lag=lag,type="Ljung-Box"),error=function(e)NULL)
    if(!is.null(b)) {lb<-b$p.value;Q<-unname(b$statistic)}
    if(!is.null(b2)) {lb2<-b2$p.value;Q2<-unname(b2$statistic)}
  }
  serial <- residual_lag_test(e,12L,ddof=p+q)
  arch <- residual_lag_test(e,12L,squared=TRUE,ddof=p+q)
  names(serial) <- paste0("serial_",names(serial)); names(arch) <- paste0("arch_",names(arch))
  cbind(data.frame(n = length(e), lag = lag, standardized = !is.null(variance_fit),
             ljung_box_p = lb, squared_ljung_box_p = lb2,
             ljung_box_Q=Q,ljung_box_df=lag-p-q,squared_ljung_box_Q=Q2,
             residual_sd = stats::sd(e), stringsAsFactors = FALSE),serial,arch)
}

predict_stat_model <- function(fit, x) {
  fc <- forecast_mean(fit$mean, x)
  if (fit$garch) fc$h <- forecast_garch11(fit$variance, fc$residuals)
  fc$parameters <- if (fit$garch) fit$variance$par else c(variance = fc$h)
  if (any(!is.finite(c(fc$mu, fc$h))) || fc$h < 0) stop("Invalid statistical forecast")
  fc
}

return_moments_to_target <- function(mu, h, moving_mean) {
  if (any(!is.finite(c(mu, h, moving_mean))) || any(h < 0)) stop("Invalid moments")
  h + (mu - moving_mean)^2
}

# Variance-standardized Student-t innovations (nu > 2).
fit_garch11_t <- function(residuals) {
  e <- check_series(residuals); sc <- sqrt(mean(e^2))
  if(sc<1e-14) return(fit_garch11(e))
  z <- e/sc
  objective <- function(u) {
    if(any(!is.finite(u))||any(abs(u)>30)) return(1e15)
    par <- garch_parameters(u[1:3]); nu <- 2+exp(u[4])
    h <- garch_variances(z,par,1)
    if(any(!is.finite(h))||any(h<=0)) return(1e15)
    -sum(lgamma((nu+1)/2)-lgamma(nu/2)-.5*log(pi*(nu-2))-
      .5*log(h)-((nu+1)/2)*log1p(z^2/(h*(nu-2))))
  }
  starts <- list(c(log(.05),log(2),log(17),log(6)),c(log(.15),0,log(.7/.15),log(3)))
  fits <- lapply(starts,function(u) tryCatch(optim(u,objective,method='BFGS',control=list(maxit=350)),error=function(e)NULL))
  good <- Filter(function(f)!is.null(f)&&f$convergence==0&&is.finite(f$value)&&f$value<1e14,fits)
  if(!length(good)) stop('Student-t GARCH failed to converge')
  f <- good[[which.min(vapply(good,function(z)z$value,numeric(1)))]]
  par <- garch_parameters(f$par[1:3]); par['omega'] <- par['omega']*sc^2
  ll <- -f$value-length(e)*log(sc)
  list(par=par,scale=sc,initial_variance=sc^2,constant=FALSE,convergence=0L,
       nu=2+exp(f$par[4]),loglik=ll,AIC=-2*ll+8,BIC=-2*ll+4*log(length(e)),
       n=length(e),k=4L,method='Student_t_GARCH11_on_fixed_ARMA_residuals')
}

