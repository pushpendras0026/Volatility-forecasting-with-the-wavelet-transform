validation_rank <- function(fc,ids,min_coverage=.95) {
  dates<-sort(unique(fc$target_date));scores<-list();good_dates<-list()
  for(id in ids) {
    z<-fc[fc$model_id==id,];valid<-.valid_forecasts(z)
    coverage<-sum(valid)/length(dates)
    scores[[id]]<-data.frame(model_id=id,coverage=coverage,eligible=coverage>=min_coverage,MSE=Inf,n_common=0L)
    if(coverage>=min_coverage)good_dates[[id]]<-z$target_date[valid]
  }
  common<-if(length(good_dates))Reduce(intersect,good_dates)else character()
  scores<-bind_rows_fill(scores)
  if(length(common))for(id in names(good_dates)) {
    z<-fc[fc$model_id==id&fc$target_date %in% common,]
    scores$MSE[scores$model_id==id]<-mean((z$actual-z$prediction)^2)
    scores$n_common[scores$model_id==id]<-nrow(z)
  }
  scores
}
select_ensembles <- function(validation,registry,cfg) {
  base<-c('raw_arima','dwt_arima','raw_garch','dwt_garch','modwt_arima','modwt_garch')
  chosen<-tables<-list()
  for(tr in c('dwt','modwt'))for(al in c('all_arima','mixed')) {
    ids<-registry$model_id[registry$kind=='mra'&registry$transform==tr&registry$allocation==al]
    s<-validation_rank(validation,ids,cfg$selection_min_coverage)
    fallback<-registry$model_id[registry$kind=='mra'&registry$transform==tr&registry$allocation==al&registry$filter=='haar'&registry$J==2]
    winner<-if(any(is.finite(s$MSE)))s$model_id[which.min(s$MSE)]else fallback
    family<-paste(tr,al,sep='_');chosen[[family]]<-winner
    s$family<-family;s$selected<-s$model_id==winner;s$fallback<-!any(is.finite(s$MSE));tables[[family]]<-s
  }
  list(base=base,all=c(base,'direct_y_arima',unlist(chosen,use.names=FALSE)),
    modwt=c('modwt_arima','modwt_garch',chosen$modwt_all_arima,chosen$modwt_mixed),
    selection=bind_rows_fill(tables))
}
add_ensembles <- function(fc,members) bind_rows_fill(list(fc,
  make_ensemble(fc,members$base,'ensemble_base_only'),
  make_ensemble(fc,members$all,'ensemble_all'),make_ensemble(fc,members$modwt,'ensemble_modwt')))
make_ensemble <- function(forecasts,members,model_id) {
  stopifnot(!anyDuplicated(members))
  sub<-forecasts[forecasts$model_id %in% members,]
  if(!nrow(sub))return(data.frame())
  keys<-c('dataset','profile','split','origin_date','target_date','horizon','target_id')
  key<-do.call(paste,c(lapply(sub[keys],as.character),sep='|'))
  if(anyDuplicated(paste(key,sub$model_id)))stop('Duplicate ensemble member/date')
  bind_rows_fill(lapply(split(seq_len(nrow(sub)),key),function(idx) {
    z<-sub[idx,];row<-z[1,];stopifnot(length(unique(z$actual))==1)
    good<-setequal(z$model_id,members)&&nrow(z)==length(members)&&all(.valid_forecasts(z))
    row$model_id<-model_id;row$stage<-'ensemble';row$prediction<-if(good)mean(z$prediction)else NA_real_
    row$prediction_unclipped<-row$prediction;row$return_mean<-row$return_variance<-NA_real_
    row$fit_status<-if(good)'ok'else'missing_member';row$error<-if(good)''else'At least one frozen member unavailable'
    row$elapsed_seconds<-0;row
  }))
}
