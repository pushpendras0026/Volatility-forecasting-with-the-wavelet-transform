# Wavelets for the base comparison and component extension. Only base R.
# Numeric db4/db6 coefficients checked against PyWavelets' coefficient source:
# https://github.com/PyWavelets/pywt/blob/main/pywt/_extensions/c/wavelets_coeffs.template.h
# db4 means 4 vanishing moments / 8 filter taps; db6 means 6 / 12 taps.
# The pyramid formulas adapt the existing project's independently written R code.

wavelet_filter <- function(name = "haar") {
  g <- switch(name,
    haar = c(1, 1) / sqrt(2),
    db4 = c(.23037781330889650, .71484657055291565, .63088076792985891,
            -.027983769416859854, -.18703481171909308, .030841381835560764,
            .032883011666885200, -.010597401785069032),
    db6 = c(.11154074335010946, .49462389039845309, .75113390802109535,
            .31525035170919763, -.22626469396543982, -.12976686756726194,
            .097501605587323049, .027522865530305729, -.031582039317486030,
            .00055384220116149614, .0047772575109455106, -.0010773010853084796),
    stop("Supported filters: haar, db4, db6; got ", name))
  L <- length(g)
  list(name = name, g = g, h = rev(g) * (-1)^(0:(L - 1L)), L = L)
}

# One-level, causal Haar forecasts. Both differences use only observed returns.
causal_haar <- function(r) {
  if (length(r) < 3L || any(!is.finite(r))) stop("Invalid return prefix")
  diff(r) / 2
}

# Paired (decimated) one-level Haar DWT of the return prefix r_1..r_t.
# The pair to be forecast is (r_t, r_{t+1}); r_t is already observed. The fitted
# history therefore ends with the complete pair (r_{t-2}, r_{t-1}); an odd prefix
# drops its oldest observation. Pair k = (u_k, v_k) gives
#   detail        d_k = (v_k - u_k)/sqrt(2)
#   approximation a_k = (v_k + u_k)/sqrt(2).
# Returns list(x = details, a = approximations), both of length floor((t-1)/2).
paired_haar_components <- function(r) {
  if (length(r) < 5L || any(!is.finite(r))) stop("Invalid return prefix")
  x <- head(r, -1L)  # r_t is the known first element of the next pair (r_t, r_t+1).
  if (length(x) %% 2L) x <- x[-1L]
  pairs <- matrix(x, ncol = 2L, byrow = TRUE)
  list(x = (pairs[, 2L] - pairs[, 1L]) / sqrt(2),
       a = (pairs[, 2L] + pairs[, 1L]) / sqrt(2))
}
paired_haar <- function(r) paired_haar_components(r)$x

# MODWT restoration (overlapping differences w_t = (r_t - r_{t-1})/2):
#   r_{t+1} = r_t + 2 w_{t+1}  =>  mu_r = r_t + 2 mu_w,  h_r = 4 h_w.
restore_haar_moments <- function(mu_detail, h_detail, last_return,
                                 transform = c("modwt", "dwt")) {
  transform <- match.arg(transform)
  if (transform == "dwt")
    stop("Paired DWT needs restore_paired_dwt_moments(), which conditions on r_t")
  list(mu = last_return + 2 * mu_detail, h = 4 * h_detail)
}

# Paired DWT restoration that conditions on the already-observed r_t.
# The next pair (r_t, r_{t+1}) has coefficients a = (r_t + r_{t+1})/sqrt(2) and
# d = (r_{t+1} - r_t)/sqrt(2). The approximation and detail ARMA(-GARCH) models,
# fitted on past pairs only, give one-step moments a ~ (mu_a, h_a), d ~ (mu_d, h_d).
# Haar is orthonormal, so a and d are treated as conditionally uncorrelated
# (exactly so when the two returns of a pair have equal conditional variance).
# Inverting, r_t = (a - d)/sqrt(2) and r_{t+1} = (a + d)/sqrt(2). Let
# s = a - d = sqrt(2) r_t (observed). Under joint normality,
#   Cov(d, s) = -h_d,  Var(s) = h_a + h_d,
#   E[d | s]   = mu_d - h_d/(h_a + h_d) * (s - (mu_a - mu_d)),
#   Var(d | s) = h_a h_d/(h_a + h_d).
# Since r_{t+1} = r_t + sqrt(2) d:
#   mu_r = r_t + sqrt(2) E[d | s],   h_r = 2 h_a h_d/(h_a + h_d).
# Check for iid N(m, s2): mu_a = sqrt(2) m, mu_d = 0, h_a = h_d = s2 give
# mu_r = m and h_r = s2, i.e. the raw-return forecast. The earlier mapping
# mu_r = r_t + sqrt(2) mu_d, h_r = 2 h_d ignored r_t and gave mu_r ~ r_t and
# h_r ~ 2 s2 (target forecast about 2.8 times too large under iid returns).
restore_paired_dwt_moments <- function(mu_detail, h_detail, mu_approx, h_approx,
                                       last_return) {
  total <- h_approx + h_detail
  if (!all(is.finite(c(mu_detail, h_detail, mu_approx, h_approx, last_return))) ||
      h_detail < 0 || h_approx < 0) stop("Invalid paired DWT moments")
  if (total <= 0) {
    # Degenerate: both coefficient variances are zero; use the mean mapping only.
    return(list(mu = (mu_approx + mu_detail) / sqrt(2), h = 0))
  }
  s <- sqrt(2) * last_return
  weight <- h_detail / total
  mu_d <- mu_detail - weight * (s - (mu_approx - mu_detail))
  list(mu = last_return + sqrt(2) * mu_d, h = 2 * h_approx * h_detail / total)
}

# Circular filtering by vectorized shifts. The outer loop is over <=12 taps,
# not over all observations; this is much faster than the old nested R loops.
circular_filter <- function(x, weights, step = 1L, forward = FALSE) {
  n <- length(x); idx <- 0:(n - 1L); out <- numeric(n)
  direction <- if (forward) 1L else -1L
  for (k in seq_along(weights))
    out <- out + weights[k] * x[(idx + direction * step * (k - 1L)) %% n + 1L]
  out
}

dwt_decompose <- function(x, J, f) {
  if (length(x) %% 2^J) stop("DWT working length must be divisible by 2^J")
  W <- vector("list", J); v <- x
  for (j in seq_len(J)) {
    keep <- seq.int(2L, length(v), by = 2L)
    W[[j]] <- circular_filter(v, f$h)[keep]
    v <- circular_filter(v, f$g)[keep]
  }
  list(W = W, V = v)
}

dwt_synthesis_step <- function(w, v, f) {
  n <- 2L * length(v); uw <- uv <- numeric(n)
  keep <- seq.int(2L, n, by = 2L)
  uw[keep] <- w; uv[keep] <- v
  circular_filter(uw, f$h, forward = TRUE) +
    circular_filter(uv, f$g, forward = TRUE)
}

modwt_decompose <- function(x, J, f) {
  W <- vector("list", J); v <- x
  for (j in seq_len(J)) {
    step <- 2^(j - 1L)
    W[[j]] <- circular_filter(v, f$h / sqrt(2), step)
    v <- circular_filter(v, f$g / sqrt(2), step)
  }
  list(W = W, V = v)
}

modwt_synthesis_step <- function(w, v, j, f) {
  step <- 2^(j - 1L)
  circular_filter(w, f$h / sqrt(2), step, forward = TRUE) +
    circular_filter(v, f$g / sqrt(2), step, forward = TRUE)
}

# Return additive, full-length MRA components A_J, D_J, ..., D_1.
# Reflection uses only this prefix. If DWT needs extra length, pad at the LEFT
# with available early observations, preserving the original end of the prefix.
# Strip the padding after reconstruction; no real observations are discarded.
decompose_prefix <- function(x, method = c("modwt", "dwt"),
                              filter = "haar", J = 2L) {
  method <- match.arg(method); J <- as.integer(J)
  x <- as.numeric(x)
  if (length(x) < 2^J || any(!is.finite(x)) || J < 1L || J > 5L)
    stop("Invalid decomposition prefix or level")
  f <- wavelet_filter(filter)
  n <- length(x); pad <- 0L
  if (method == "dwt") pad <- (2^J - n %% 2^J) %% 2^J
  padded <- if (pad) c(rev(x[seq_len(pad)]), x) else x
  extended <- c(padded, rev(padded))
  wt <- if (method == "dwt") dwt_decompose(extended, J, f) else modwt_decompose(extended, J, f)
  reconstruct <- function(retain_detail) {
    v <- if (retain_detail == 0L) wt$V else numeric(length(wt$V))
    for (j in J:1L) {
      w <- if (j == retain_detail) wt$W[[j]] else numeric(length(wt$W[[j]]))
      v <- if (method == "dwt") dwt_synthesis_step(w, v, f) else
        modwt_synthesis_step(w, v, j, f)
    }
    v[(pad + 1L):(pad + n)]
  }
  out <- c(setNames(list(reconstruct(0L)), paste0("A", J)),
           setNames(lapply(J:1L, reconstruct), paste0("D", J:1L)))
  err <- max(abs(x - Reduce(`+`, out)))
  if (err > 1e-8 * max(1, max(abs(x)))) stop("Wavelet reconstruction check failed")
  attr(out, "reconstruction_error") <- err
  attr(out, "filter") <- filter
  attr(out, "method") <- method
  attr(out, "boundary") <- "reflection_of_available_prefix"
  attr(out, "left_padding") <- pad
  out
}
