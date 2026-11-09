# Extension 3: seven past-only features -> one hidden layer -> one y forecast.
mlp_features <- function(y) {
  stopifnot(length(y)>=20L)
  t <- length(y)
  c(setNames(y[t:(t-4L)],paste0("lag",1:5)),
    mean5=mean(tail(y,5L)),mean20=mean(tail(y,20L)))
}
make_mlp_rows <- function(y) {
  if(length(y)<25L) stop("Not enough target history for the MLP")
  origins <- seq.int(20L,length(y)-1L)
  x <- t(vapply(origins,function(t) mlp_features(y[seq_len(t)]),numeric(7L)))
  actual <- y[origins+1L]
  good <- apply(is.finite(x),1L,all)&is.finite(actual)
  list(x=x[good,,drop=FALSE],y=actual[good],origin=origins[good],target=origins[good]+1L)
}
fit_mlp <- function(y, hidden=5L, decay=.01, seed=101L,maxit=300L) {
  rows <- make_mlp_rows(y)
  if(nrow(rows$x)<40L) stop("Fewer than 40 complete MLP training rows")
  center <- colMeans(rows$x); spread <- apply(rows$x,2L,sd)
  spread[!is.finite(spread)|spread==0] <- 1
  xs <- sweep(sweep(rows$x,2L,center,"-"),2L,spread,"/")
  scale <- max(mean(rows$y),1e-12)
  set.seed(seed)
  model <- nnet::nnet(x=xs,y=rows$y/scale,size=hidden,linout=TRUE,
                       skip=FALSE,decay=decay,maxit=maxit,trace=FALSE)
  # An iteration limit is visible, rather than quietly treated as convergence.
  list(model=model,center=center,spread=spread,scale=scale,
       convergence=model$convergence,hidden=hidden,decay=decay,seed=seed)
}
predict_mlp <- function(fit,y) {
  # Register nnet's S3 methods in THIS process before predict(). A fresh PSOCK
  # worker that restores a saved fit has not yet called nnet::nnet(), so
  # predict() would otherwise fail; results then depended on scheduling (audit B1).
  loadNamespace("nnet")
  x <- matrix(mlp_features(y),nrow=1L)
  xs <- sweep(sweep(x,2L,fit$center,"-"),2L,fit$spread,"/")
  raw <- as.numeric(predict(fit$model,xs))*fit$scale
  if(!is.finite(raw)) stop("Non-finite MLP prediction")
  list(prediction=pmax(0,raw),prediction_unclipped=raw,
       fit_status=if(fit$convergence==0L) "ok" else "iteration_limit")
}
