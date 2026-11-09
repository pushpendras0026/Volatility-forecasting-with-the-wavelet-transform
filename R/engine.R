# One causal model API and forecast loop for every experiment and period.
model_input <- function(past,spec,cfg,cache=NULL) {
  r<-tail(past$r,cfg$max_window)
  if(spec$kind=='stat')return(switch(spec$transform,none=list(x=r),dwt=paired_haar_components(r),modwt=list(x=causal_haar(r))))
  y<-tail(past$y[is.finite(past$y)],cfg$max_window)
  if(spec$kind %in% c('direct','mlp'))return(list(x=y))
  key<-paste(spec$transform,spec$filter,spec$J,sep='_')
  if(!is.null(cache)&&exists(key,cache,inherits=FALSE))return(get(key,cache))
  x<-decompose_prefix(y,spec$transform,spec$filter,spec$J)
  if(!is.null(cache))assign(key,x,cache)
  x
}
choose_orders <- function(inputs,spec,cfg) {
  orders<-tables<-list()
  for(cn in names(inputs)) {
    if(spec$kind=='mra'&&spec$allocation=='mixed'&&grepl('^D',cn)) {
      p<-1L;q<-0L;grid<-data.frame(p=p,q=q,selection='declared_AR1_detail_mean')
    } else {
      s<-select_arma(inputs[[cn]],if(spec$kind=='mra')cfg$component_max_pq else cfg$max_pq,cfg$criterion,diagnostics=spec$kind=='stat')
      p<-s$p;q<-s$q;grid<-s$grid;grid$selection<-paste0(cfg$criterion,'_initial_training')
    }
    orders[[cn]]<-c(p=p,q=q);grid$model_id<-spec$model_id;grid$component<-cn
    grid$chosen<-grid$p==p&grid$q==q;tables[[cn]]<-grid
  }
  list(orders=orders,table=bind_rows_fill(tables))
}
initialize_models <- function(initial,registry,cfg) {
  states<-tables<-selected<-list()
  for(j in seq_len(nrow(registry))) {
    spec<-as.list(registry[j,]);id<-spec$model_id
    if(spec$kind=='baseline')next
    if(spec$order_rule=='raw_plus_one_ma') {
      raw<-states$raw_arima$orders$x
      chosen<-list(orders=list(x=c(p=unname(raw['p']),q=unname(raw['q'])+1L)),table=data.frame())
    } else {
      sister<-if(grepl('_student_t$',id))sub('_student_t$','',id)else if(spec$kind=='stat')sub('_garch$','_arima',id)else id
      chosen<-if(sister!=id&&!is.null(states[[sister]]))list(orders=states[[sister]]$orders,table=data.frame())else
        choose_orders(model_input(initial,spec,cfg),spec,cfg)
    }
    states[[id]]<-list(orders=chosen$orders,fit=NULL,origin=-Inf)
    tables[[id]]<-chosen$table
    for(cn in names(chosen$orders))selected[[length(selected)+1L]]<-data.frame(model_id=id,component=cn,
      p=unname(chosen$orders[[cn]]['p']),q=unname(chosen$orders[[cn]]['q']),
      distribution=spec$distribution,order_rule=spec$order_rule)
  }
  list(states=states,grids=bind_rows_fill(tables),orders=bind_rows_fill(selected))
}
fit_pipeline <- function(inputs,spec,orders,cfg) {
  if(spec$kind=='mlp')return(fit_mlp(inputs$x,spec$hidden,spec$decay,spec$seed,cfg$mlp_maxit))
  fits<-lapply(names(inputs),function(cn) {
    ord<-orders[[cn]]
    mixed_detail<-spec$kind=='mra'&&spec$allocation=='mixed'&&grepl('^D',cn)
    use_garch<-isTRUE(spec$garch)||mixed_detail
    if(!mixed_detail)return(fit_stat_model(inputs[[cn]],unname(ord['p']),unname(ord['q']),use_garch,spec$distribution))
    # Mixed MRA: the detail GARCH variance never enters the summed point forecast.
    # A GARCH failure therefore must not remove the forecast: keep the AR(1) mean
    # and record the variance failure (audit m2).
    tryCatch(fit_stat_model(inputs[[cn]],unname(ord['p']),unname(ord['q']),TRUE,spec$distribution),
      error=function(e){f<-fit_stat_model(inputs[[cn]],unname(ord['p']),unname(ord['q']),FALSE,spec$distribution)
        f$variance_error<-conditionMessage(e);f})
  });setNames(fits,names(inputs))
}
predict_pipeline <- function(fit,inputs,spec,past,cfg) {
  if(spec$kind=='mlp')return(predict_mlp(fit,inputs$x))
  # Component (MRA) forecasts use conditional means only, so no variance forecast is needed.
  pred<-setNames(lapply(names(inputs),function(cn)if(spec$kind=='mra')forecast_mean(fit[[cn]]$mean,inputs[[cn]])else
    predict_stat_model(fit[[cn]],inputs[[cn]])),names(inputs))
  if(spec$kind=='stat') {
    mu<-pred$x$mu;h<-pred$x$h
    # Paired DWT: detail (x) and approximation (a) models, conditioned on r_t (wavelets.R).
    if(spec$transform=='dwt') {z<-restore_paired_dwt_moments(mu,h,pred$a$mu,pred$a$h,tail(past$r,1));mu<-z$mu;h<-z$h}
    if(spec$transform=='modwt') {z<-restore_haar_moments(mu,h,tail(past$r,1),'modwt');mu<-z$mu;h<-z$h}
    value<-return_moments_to_target(mu,h,mean(tail(past$r,cfg$mean_window)))
    return(list(prediction=value,prediction_unclipped=value,return_mean=mu,return_variance=h,fit_status='ok'))
  }
  value<-sum(vapply(pred,function(z)z$mu,numeric(1)))
  list(prediction=max(0,value),prediction_unclipped=value,fit_status='ok')
}
mlp_registry <- function(cfg,selected=NULL) {
  if(is.null(selected)) {
    g<-expand.grid(hidden=cfg$mlp_hidden,decay=cfg$mlp_decay,seed=cfg$mlp_seeds)
    g$model_id<-sprintf('mlp_h%d_d%s_s%d',g$hidden,g$decay,g$seed)
  } else {
    g<-data.frame(hidden=selected$hidden,decay=selected$decay,seed=cfg$mlp_seeds)
    g$model_id<-ifelse(g$seed==101L,'mlp',paste0('mlp_seed',g$seed))
  }
  g$stage<-'neural';g$kind<-'mlp';g$transform<-'none';g$filter<-'none'
  g$allocation<-'none';g$J<-0L;g$garch<-FALSE;g$distribution<-'gaussian';g$order_rule<-'none';g
}
select_mlp <- function(fc,cfg) {
  reg<-mlp_registry(cfg);scores<-list()
  for(id in reg$model_id) {
    z<-fc[fc$model_id==id,];r<-reg[reg$model_id==id,]
    scores[[id]]<-data.frame(model_id=id,hidden=r$hidden,decay=r$decay,seed=r$seed,
      n=nrow(z),coverage=mean(.valid_forecasts(z)),MSE=if(nrow(z)&&all(.valid_forecasts(z)))mean((z$actual-z$prediction)^2)else Inf)
  }
  scores<-bind_rows_fill(scores);rank<-aggregate(MSE~hidden+decay,scores,mean)
  rank<-rank[order(rank$MSE,rank$hidden,rank$decay),]
  selected<-if(nrow(rank)&&is.finite(rank$MSE[1]))list(hidden=rank$hidden[1],decay=rank$decay[1])else NULL
  list(selected=selected,scores=scores,summary=rank)
}
run_forecasts <- function(series,indices,registry,cfg,dataset,period,states,out) {
  ensure_dir(out);rows<-diag<-failures<-list();nr<-0L
  if(is.finite(cfg$max_origins))indices<-head(indices,cfg$max_origins)
  if(!length(indices))return(list(forecasts=data.frame(),states=states,diagnostics=data.frame(),failures=data.frame()))
  for(i in seq_along(indices)) {
    target<-indices[i];origin<-target-1L;past<-series[seq_len(origin),,drop=FALSE]
    cache<-new.env(parent=emptyenv())
    for(j in seq_len(nrow(registry))) {
      spec<-as.list(registry[j,]);id<-spec$model_id;start<-proc.time()['elapsed']
      row<-data.frame(dataset=dataset,profile=period,split=period,model_id=id,stage=spec$stage,
        target_id=cfg$target_id,horizon=1L,origin_date=as.character(series$Date[origin]),
        target_date=as.character(series$Date[target]),actual=series$y[target],
        prediction=NA_real_,prediction_unclipped=NA_real_,return_mean=NA_real_,return_variance=NA_real_,
        moving_mean=mean(tail(past$r,cfg$mean_window)),fit_status='failed',error='',
        elapsed_seconds=0,refitted=FALSE,mape_threshold=cfg$mape_threshold,
        train_start=as.character(series$Date[max(1,origin-cfg$max_window+1)]),train_end=as.character(series$Date[origin]))
      result<-tryCatch({
        if(spec$kind=='baseline') {
          y<-past$y[is.finite(past$y)];v<-if(id=='naive')tail(y,1)else mean(tail(y,20))
          list(prediction=v,prediction_unclipped=v,fit_status='ok')
        } else {
          inputs<-model_input(past,spec,cfg,cache);state<-states[[id]]
          if(is.null(state))state<-list(orders=NULL,fit=NULL,origin=-Inf)
          if(is.null(state$fit)||origin-state$origin>=cfg$refit_every) {
            state$fit<-fit_pipeline(inputs,spec,state$orders,cfg);state$origin<-origin;row$refitted<-TRUE
            if(spec$kind!='mlp')for(cn in names(state$fit)) {
              f<-state$fit[[cn]];v<-f$variance
              diag[[length(diag)+1L]]<-cbind(data.frame(dataset=dataset,period=period,model_id=id,component=cn,
                origin_date=row$origin_date,p=f$p,q=f$q,mean_AIC=f$mean$AIC,mean_BIC=f$mean$BIC,
                omega=if(is.null(v))NA_real_ else v$par['omega'],alpha=if(is.null(v))NA_real_ else v$par['alpha'],
                beta=if(is.null(v))NA_real_ else v$par['beta'],nu=if(is.null(v$nu))NA_real_ else v$nu,variance_error=if(is.null(f$variance_error))'' else f$variance_error),f$diagnostics)
            }
            model_file<-file.path(out,'models',paste0(id,'_first.rds'))
            if(!file.exists(model_file)) {ensure_dir(dirname(model_file));saveRDS(state$fit,model_file)}
          }
          states[[id]]<-state;predict_pipeline(state$fit,inputs,spec,past,cfg)
        }
      },error=function(e)list(error=conditionMessage(e)))
      if(!is.null(result$error)) {row$error<-result$error;failures[[length(failures)+1L]]<-row[,c('model_id','target_date','error')]}else
        for(n in intersect(names(row),names(result)))if(length(result[[n]])==1)row[[n]]<-result[[n]]
      row$elapsed_seconds<-unname(proc.time()['elapsed']-start);nr<-nr+1L;rows[[nr]]<-row
    }
    if(i%%25L==0L||i==length(indices))write_table(data.frame(dataset=dataset,period=period,completed=i,
      requested=length(indices),target_date=as.character(series$Date[target]),time=as.character(Sys.time())),file.path(out,'progress.csv'))
    if(i%%cfg$checkpoint_every==0L||i==length(indices))saveRDS(list(states=states,last_index=target),file.path(out,'checkpoint.rds'))
  }
  ans<-list(forecasts=bind_rows_fill(rows),states=states,diagnostics=bind_rows_fill(diag),failures=bind_rows_fill(failures))
  write_table(ans$forecasts,file.path(out,'forecasts.csv'));write_table(ans$diagnostics,file.path(out,'diagnostics.csv'))
  write_table(ans$failures,file.path(out,'failures.csv'))
  ans
}
