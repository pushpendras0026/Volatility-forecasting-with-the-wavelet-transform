# Descriptive, normality, stationarity and independence tests in base R.
# Used by tools/analyze.R for tables/descriptive_normality_stationarity.csv and
# validated in tests/test_stat_tests.R against statsmodels 0.15 / scipy 1.18
# reference values (tests/reference/stat_tests_reference.csv) and closed forms.
#
# Tests reported by the papers:
#  * Ismail, Audu & Tumala (2016), Table 1 (daily returns, full sample): sample size,
#    mean, standard deviation, skewness, kurtosis (normal = 3), Ljung-Box Q(24),
#    Jarque-Bera. Tables 2-10: Breusch-Godfrey serial-correlation LM and ARCH-effect
#    tests on ARMA residuals (already in R/models.R::model_diagnostics).
#  * Rubio et al. (2023), Tables 2, 4, 5 (prices, returns, realized volatility):
#    skewness test, kurtosis test, Jarque-Bera, ADF, KPSS, BDS (dimensions 2-6),
#    Shapiro-Wilk, D'Agostino K^2, Anderson-Darling.
# Neither paper uses Phillips-Perron, so it is not implemented.

# Biased (population) moment estimators, as in the JB statistic.
moment_stats <- function(x) {
  n <- length(x); m <- mean(x); d <- x - m
  m2 <- mean(d^2); m3 <- mean(d^3); m4 <- mean(d^4)
  list(n = n, mean = m, sd = stats::sd(x), skewness = m3 / m2^1.5,
       kurtosis_raw = m4 / m2^2, excess_kurtosis = m4 / m2^2 - 3)
}

# Jarque & Bera (1987): JB = n/6 (S^2 + (K-3)^2/4) ~ chi2(2) under normality.
jarque_bera <- function(x) {
  s <- moment_stats(x)
  jb <- s$n / 6 * (s$skewness^2 + s$excess_kurtosis^2 / 4)
  list(statistic = jb, p.value = stats::pchisq(jb, 2, lower.tail = FALSE))
}

# D'Agostino (1970) skewness z-test (same formulas as scipy.stats.skewtest).
skewness_test <- function(x) {
  n <- length(x); b2 <- moment_stats(x)$skewness
  y <- b2 * sqrt(((n + 1) * (n + 3)) / (6 * (n - 2)))
  beta2 <- 3 * (n^2 + 27 * n - 70) * (n + 1) * (n + 3) / ((n - 2) * (n + 5) * (n + 7) * (n + 9))
  W2 <- -1 + sqrt(2 * (beta2 - 1)); delta <- 1 / sqrt(0.5 * log(W2))
  alpha <- sqrt(2 / (W2 - 1)); if (y == 0) y <- 1
  z <- delta * log(y / alpha + sqrt((y / alpha)^2 + 1))
  list(statistic = z, p.value = 2 * stats::pnorm(-abs(z)))
}

# Anscombe & Glynn (1983) kurtosis z-test (scipy.stats.kurtosistest).
kurtosis_test <- function(x) {
  n <- length(x); b2 <- moment_stats(x)$kurtosis_raw
  E <- 3 * (n - 1) / (n + 1)
  varb2 <- 24 * n * (n - 2) * (n - 3) / ((n + 1)^2 * (n + 3) * (n + 5))
  xx <- (b2 - E) / sqrt(varb2)
  sb1 <- 6 * (n^2 - 5 * n + 2) / ((n + 7) * (n + 9)) * sqrt(6 * (n + 3) * (n + 5) / (n * (n - 2) * (n - 3)))
  A <- 6 + 8 / sb1 * (2 / sb1 + sqrt(1 + 4 / sb1^2))
  term1 <- 1 - 2 / (9 * A); denom <- 1 + xx * sqrt(2 / (A - 4))
  term2 <- sign(denom) * ((1 - 2 / A) / abs(denom))^(1 / 3)
  z <- (term1 - term2) / sqrt(2 / (9 * A))
  list(statistic = z, p.value = 2 * stats::pnorm(-abs(z)))
}

# D'Agostino-Pearson K^2 = Z_skew^2 + Z_kurt^2 ~ chi2(2) (scipy.stats.normaltest).
dagostino_k2 <- function(x) {
  k2 <- skewness_test(x)$statistic^2 + kurtosis_test(x)$statistic^2
  list(statistic = k2, p.value = stats::pchisq(k2, 2, lower.tail = FALSE))
}

# Anderson-Darling normality test with estimated mean and variance.
# A^2 as scipy.stats.anderson; p-value from the modified statistic
# A* = A^2 (1 + 0.75/n + 2.25/n^2), D'Agostino & Stephens (1986, Table 4.9).
anderson_darling <- function(x) {
  x <- sort(x); n <- length(x)
  z <- (x - mean(x)) / stats::sd(x)
  i <- seq_len(n)  # log-scale tails avoid log(0) for extreme returns
  a2 <- -n - mean((2 * i - 1) * (stats::pnorm(z, log.p = TRUE) +
                                 rev(stats::pnorm(z, lower.tail = FALSE, log.p = TRUE))))
  aa <- a2 * (1 + 0.75 / n + 2.25 / n^2)
  pv <- if (aa < 0.2) 1 - exp(-13.436 + 101.14 * aa - 223.73 * aa^2) else
    if (aa < 0.34) 1 - exp(-8.318 + 42.796 * aa - 59.938 * aa^2) else
    if (aa < 0.6) exp(0.9177 - 4.279 * aa - 1.38 * aa^2) else
    if (aa < 10) exp(1.2937 - 5.709 * aa + 0.0186 * aa^2) else 3.7e-24
  list(statistic = a2, modified = aa, p.value = pv)
}

# Shapiro-Wilk (Royston 1995) from base R; defined only for 3 <= n <= 5000.
shapiro_wilk <- function(x) {
  if (length(x) > 5000L) return(list(statistic = NA_real_, p.value = NA_real_))
  z <- stats::shapiro.test(x); list(statistic = unname(z$statistic), p.value = z$p.value)
}

# OLS with Gaussian log likelihood (as statsmodels OLS.llf / aic).
.ols <- function(y, X) {
  f <- stats::lm.fit(X, y); n <- length(y); ssr <- sum(f$residuals^2)
  llf <- -n / 2 * (log(2 * pi) + log(ssr / n) + 1)
  list(fit = f, n = n, k = ncol(X), ssr = ssr, aic = -2 * llf + 2 * ncol(X))
}

# MacKinnon (1994) p-value for the ADF tau statistic, constant, N = 1
# (coefficients as tabulated in MacKinnon 1994, Table 3; statsmodels mackinnonp).
mackinnon_p_c <- function(tau) {
  if (tau > 2.74) return(1); if (tau < -18.83) return(0)
  if (tau <= -1.61) {
    b <- c(2.1659, 1.4412, 3.8269e-2); stats::pnorm(b[1] + b[2] * tau + b[3] * tau^2)
  } else {
    b <- c(1.7339, 9.3202e-1, -1.2745e-1, -1.0368e-2)
    stats::pnorm(b[1] + b[2] * tau + b[3] * tau^2 + b[4] * tau^3)
  }
}
# MacKinnon (2010, Table 2) finite-sample critical values, constant, N = 1:
# c(T) = b_inf + b1/T + b2/T^2 + b3/T^3.
mackinnon_crit_c <- function(nobs) {
  b <- rbind(`1%` = c(-3.43035, -6.5393, -16.786, -79.433),
             `5%` = c(-2.86154, -2.8903, -4.234, -40.040),
             `10%` = c(-2.56677, -1.5384, -2.809, 0))
  drop(b %*% (1 / nobs)^(0:3))
}

# Augmented Dickey-Fuller test with a constant. Lag order chosen by AIC over
# 0..maxlag on a common sample, maxlag = ceiling(12 (n/100)^(1/4)) (Schwert 1989),
# then the regression is re-estimated with the chosen lag on all usable
# observations (same algorithm as statsmodels adfuller(autolag='AIC')).
adf_test <- function(x, maxlag = NULL) {
  n <- length(x); dx <- diff(x)
  if (is.null(maxlag)) maxlag <- ceiling(12 * (n / 100)^(1 / 4))
  maxlag <- min(maxlag, n %/% 2 - 1L - 1L)
  design <- function(lag) {
    nobs <- length(dx) - lag
    rows <- (lag + 1):length(dx)
    X <- cbind(x[rows], if (lag) sapply(seq_len(lag), function(k) dx[rows - k]) else NULL)
    list(y = dx[rows], X = X, nobs = nobs)
  }
  full <- design(maxlag)
  aic <- vapply(0:maxlag, function(l)
    .ols(full$y, cbind(1, full$X[, seq_len(l + 1L), drop = FALSE]))$aic, numeric(1))
  lag <- (0:maxlag)[which.min(aic)]
  d <- design(lag); X <- cbind(d$X, 1)
  o <- .ols(d$y, X)
  sigma2 <- o$ssr / (o$n - o$k)
  se <- sqrt(sigma2 * diag(chol2inv(qr.R(qr(X))))[1])
  tau <- unname(o$fit$coefficients[1] / se)
  list(statistic = tau, lag = lag, nobs = d$nobs, maxlag = maxlag,
       p.value = mackinnon_p_c(tau), critical = mackinnon_crit_c(d$nobs))
}

# KPSS level-stationarity test (Kwiatkowski et al. 1992) with a Bartlett-kernel
# Newey-West long-run variance and the Hobijn, Franses & Ooms (1998) automatic
# bandwidth (statsmodels kpss(nlags='auto')). p-value: linear interpolation in
# the KPSS (1992, Table 1) critical values, truncated to [0.01, 0.10].
kpss_bandwidth <- function(e) {
  n <- length(e); covlags <- floor(n^(2 / 9))
  s0 <- sum(e^2) / n; s1 <- 0
  for (i in seq_len(covlags)) {
    p <- sum(e[(i + 1):n] * e[1:(n - i)]) / (n / 2)
    s0 <- s0 + p; s1 <- s1 + i * p
  }
  floor(1.1447 * ((s1 / s0)^2)^(1 / 3) * n^(1 / 3))
}
kpss_test <- function(x, lags = NULL) {
  n <- length(x); e <- x - mean(x)
  if (is.null(lags)) lags <- min(kpss_bandwidth(e), n - 1L)
  s <- sum(e^2)
  for (i in seq_len(lags)) s <- s + 2 * (1 - i / (lags + 1)) * sum(e[(i + 1):n] * e[1:(n - i)])
  eta <- sum(cumsum(e)^2) / n^2
  stat <- eta / (s / n)
  crit <- c(`10%` = 0.347, `5%` = 0.463, `2.5%` = 0.574, `1%` = 0.739)
  p <- stats::approx(crit, c(.10, .05, .025, .01), stat, rule = 2)$y
  list(statistic = stat, lag = lags, p.value = p, critical = crit,
       p_bound = if (stat < crit[1]) 'p > 0.10' else if (stat > crit[4]) 'p < 0.01' else 'interpolated')
}

# Ljung-Box Q(lag) on x and on squared deviations (stats::Box.test).
ljung_box <- function(x, lag = 24L) {
  b <- stats::Box.test(x, lag = lag, type = 'Ljung-Box')
  list(statistic = unname(b$statistic), p.value = b$p.value)
}

# Engle (1982) ARCH-LM: regress squared demeaned returns on 12 own lags; LM = n R^2.
arch_lm <- function(x, lags = 12L) {
  e <- (x - mean(x))^2; z <- stats::embed(e, lags + 1L)
  o <- stats::lm.fit(cbind(1, z[, -1]), z[, 1])
  r2 <- 1 - sum(o$residuals^2) / sum((z[, 1] - mean(z[, 1]))^2)
  lm <- nrow(z) * r2
  list(statistic = lm, p.value = stats::pchisq(lm, lags, lower.tail = FALSE))
}

# Brock, Dechert, Scheinkman & LeBaron (1996) BDS test, epsilon = 1.5 sd,
# dimensions 2..max_dim, asymptotic N(0,1) two-sided p-values (as statsmodels bds).
bds_test <- function(x, max_dim = 6L, distance = 1.5) {
  n <- length(x); eps <- distance * stats::sd(x)
  ind <- abs(outer(x, x, '-')) < eps
  upper_mean <- function(m) mean(m[upper.tri(m)])
  c1 <- upper_mean(ind)
  k <- (sum(rowSums(ind)^2) - 3 * sum(ind) + 2 * n) / (n * (n - 1) * (n - 2))
  joint <- ind; cm <- numeric(max_dim); cm[1] <- c1
  for (m in 2:max_dim) {
    nn <- nrow(joint); joint <- joint[-1, -1] & joint[-nn, -nn]; cm[m] <- upper_mean(joint)
  }
  rm(joint)
  out <- lapply(2:max_dim, function(m) {
    tmp <- sum(vapply(1:(m - 1), function(j) k^(m - j) * c1^(2 * j), numeric(1)))
    v <- 4 * (k^m + 2 * tmp + (m - 1)^2 * c1^(2 * m) - m^2 * k * c1^(2 * m - 2))
    sub <- ind[m:n, m:n]; c1m <- upper_mean(sub)
    z <- sqrt(n - m + 1) * (cm[m] - c1m^m) / sqrt(v)
    c(dim = m, statistic = z, p.value = 2 * stats::pnorm(-abs(z)))
  })
  as.data.frame(do.call(rbind, out))
}

# One row of the descriptive/normality/stationarity table for a return vector.
describe_returns <- function(r, with_bds = TRUE) {
  s <- moment_stats(r); jb <- jarque_bera(r); sk <- skewness_test(r); ku <- kurtosis_test(r)
  k2 <- dagostino_k2(r); ad <- anderson_darling(r); sw <- shapiro_wilk(r)
  adf <- adf_test(r); kp <- kpss_test(r); q <- ljung_box(r); q2 <- ljung_box((r - mean(r))^2)
  arch <- arch_lm(r)
  row <- data.frame(n = s$n, mean = s$mean, sd = s$sd, min = min(r), max = max(r),
    skewness = s$skewness, excess_kurtosis = s$excess_kurtosis, kurtosis_raw = s$kurtosis_raw,
    JB = jb$statistic, JB_p = jb$p.value, skew_z = sk$statistic, skew_p = sk$p.value,
    kurt_z = ku$statistic, kurt_p = ku$p.value, K2 = k2$statistic, K2_p = k2$p.value,
    AD = ad$statistic, AD_p = ad$p.value, SW = sw$statistic, SW_p = sw$p.value,
    ADF_tau = adf$statistic, ADF_lag = adf$lag, ADF_nobs = adf$nobs, ADF_p = adf$p.value,
    ADF_crit_1 = adf$critical[['1%']], ADF_crit_5 = adf$critical[['5%']], ADF_crit_10 = adf$critical[['10%']],
    KPSS = kp$statistic, KPSS_lag = kp$lag, KPSS_p = kp$p.value, KPSS_p_bound = kp$p_bound,
    Q24 = q$statistic, Q24_p = q$p.value, Q24_sq = q2$statistic, Q24_sq_p = q2$p.value,
    ARCH_LM12 = arch$statistic, ARCH_LM12_p = arch$p.value)
  if (with_bds) {
    b <- bds_test(r)
    for (i in seq_len(nrow(b))) {
      row[[paste0('BDS_m', b$dim[i])]] <- b$statistic[i]
      row[[paste0('BDS_m', b$dim[i], '_p')]] <- b$p.value[i]
    }
  }
  row
}
