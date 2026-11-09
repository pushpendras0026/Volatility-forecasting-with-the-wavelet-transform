scenario_config <- function(cfg,scenario) {
  if(scenario=='baseline')return(cfg)
  row<-sensitivity_plan();row<-row[row$scenario==scenario,];stopifnot(nrow(row)==1)
  for(n in c('max_window','refit_every','criterion','max_pq'))cfg[[n]]<-row[[n]]
  cfg
}
experiment_registry <- function(cfg,scenario) {
  reg<-model_registry(cfg)
  if(scenario!='baseline')reg<-reg[reg$model_id %in% c('raw_garch','dwt_garch','modwt_garch'),]
  reg
}
dataset_directory <- function(run,id,scenario)file.path(run,'historical',scenario,id)

run_historical_job <- function(job,root,run,cfg) {
  id<-job$dataset;scenario<-job$scenario;out<-dataset_directory(run,id,scenario)
  ensure_dir(out);done<-file.path(out,'COMPLETE.rds')
  if(file.exists(done))return(readRDS(done))
  tryCatch({
    local<-scenario_config(cfg,scenario);series<-make_targets(load_prices(root,id),local$mean_window)
    split<-calendar_split(series,local);series<-split$series
    train<-series[seq_len(split$train_end_index),]
    local$mape_threshold<-max(1e-12,.01*median(train$y[is.finite(train$y)&train$y>0]))
    write_table(split$dates,file.path(out,'split.csv'))
    reg<-experiment_registry(local,scenario);initial<-initialize_models(train,reg,local)
    write_table(initial$grids,file.path(out,'initial_aic_diagnostics.csv'))
    write_table(initial$orders,file.path(out,'initial_orders.csv'))
    candidates<-if(scenario=='baseline')bind_rows_fill(list(reg,mlp_registry(local)))else reg
    val<-run_forecasts(series,split$validation_indices,candidates,local,id,'validation',initial$states,file.path(out,'validation'))
    selected_modwt<-selected_component<-NA_character_;members<-NULL;mlp<-NULL
    if(scenario=='baseline') {
      members<-select_ensembles(val$forecasts,reg,local)
      write_table(members$selection,file.path(out,'ensemble_selection.csv'))
      mlp<-select_mlp(val$forecasts,local)
      write_table(mlp$scores,file.path(out,'mlp_validation_scores.csv'))
      write_table(mlp$summary,file.path(out,'mlp_architecture_scores.csv'))
      mlp$fallback<-is.null(mlp$selected)
      if(mlp$fallback)mlp$selected<-list(hidden=5L,decay=.01)
      reg<-bind_rows_fill(list(reg,mlp_registry(local,mlp$selected)))
      ids<-reg$model_id[reg$kind=='stat'&reg$transform=='modwt'&reg$garch]
      ranks<-validation_rank(val$forecasts,ids,local$selection_min_coverage)
      selected_modwt<-if(any(is.finite(ranks$MSE)))ranks$model_id[which.min(ranks$MSE)]else'modwt_garch'
      ranks$selected<-ranks$model_id==selected_modwt
      write_table(ranks,file.path(out,'modwt_validation_selection.csv'))
      component_ranks<-validation_rank(val$forecasts,reg$model_id[reg$kind=='mra'],local$selection_min_coverage)
      selected_component<-if(any(is.finite(component_ranks$MSE)))component_ranks$model_id[which.min(component_ranks$MSE)]else'mra_modwt_haar_all_arima'
      component_ranks$selected<-component_ranks$model_id==selected_component
      write_table(component_ranks,file.path(out,'component_validation_selection.csv'))
    }
    plan<-list(registry=reg,members=members,selected_modwt=selected_modwt,selected_component=selected_component,mlp=mlp,
      initial_orders=initial$orders,cfg=local,validation_end=as.character(max(series$Date[split$validation_indices])))
    saveRDS(plan,file.path(out,'frozen_plan.rds'));write_table(reg,file.path(out,'frozen_registry.csv'))
    test<-run_forecasts(series,split$test_indices,reg,local,id,'test',val$states,file.path(out,'test'))
    fc<-if(scenario=='baseline')add_ensembles(test$forecasts,members)else test$forecasts
    write_table(fc,file.path(out,'test_forecasts.csv'));write_table(calculate_metrics(fc),file.path(out,'metrics.csv'))
    status<-data.frame(dataset=id,scenario=scenario,phase='historical',status='finished',n_dates=length(split$test_indices),message='')
    saveRDS(status,done);status
  },error=function(e){writeLines(conditionMessage(e),file.path(out,'ERROR.txt'));
    data.frame(dataset=id,scenario=scenario,phase='historical',status='failed',n_dates=0,message=conditionMessage(e))})
}

freeze_sensitivity_choices <- function(run,cfg) {
  rows<-list();details<-list()
  for(ds in cfg$dataset_ids)for(id in c('raw_garch','dwt_garch','modwt_garch')) {
    data<-list()
    for(scenario in c('baseline',sensitivity_plan()$scenario)) {
      f<-file.path(dataset_directory(run,ds,scenario),'validation/forecasts.csv')
      z<-read.csv(f);z<-z[z$model_id==id,];z$model_id<-scenario;data[[scenario]]<-z
    }
    ranks<-validation_rank(bind_rows_fill(data),names(data),cfg$selection_min_coverage)
    best<-if(any(is.finite(ranks$MSE)))which.min(ranks$MSE)else which(ranks$model_id=='baseline')
    r<-ranks[best,]
    rows[[length(rows)+1L]]<-data.frame(dataset=ds,model_id=id,selected_scenario=r$model_id,
      validation_MSE=r$MSE,n_common=r$n_common,coverage=r$coverage)
    ranks$dataset<-ds;ranks$pipeline<-id;details[[length(details)+1L]]<-ranks
  }
  choices<-bind_rows_fill(rows);write_table(choices,file.path(run,'frozen_parameter_choices.csv'))
  write_table(bind_rows_fill(details),file.path(run,'parameter_validation_scores.csv'))
  saveRDS(list(choices=choices,frozen_at=Sys.time(),source_period='2010-2011 validation only'),file.path(run,'frozen_parameter_choices.rds'))
}

later_jobs <- function(root,run,cfg) {
  manifest<-read.csv(file.path(root,'data/manifest.csv'))
  jobs<-list()
  for(id in manifest$dataset[manifest$type=='stock'])for(scenario in c('baseline',sensitivity_plan()$scenario)) {
    out<-dataset_directory(run,id,scenario);stopifnot(file.exists(file.path(out,'COMPLETE.rds')))
    plan<-readRDS(file.path(out,'frozen_plan.rds'))
    count<-if(scenario=='baseline')4L else 1L
    groups<-split(seq_len(nrow(plan$registry)),rep(seq_len(count),length.out=nrow(plan$registry)))
    for(g in seq_along(groups))jobs[[length(jobs)+1L]]<-list(dataset=id,scenario=scenario,group=g,rows=groups[[g]])
  }
  jobs
}
run_later_job <- function(job,root,run,cfg) {
  id<-job$dataset;scenario<-job$scenario
  out<-file.path(run,'later',scenario,id,paste0('group',job$group));ensure_dir(out)
  done<-file.path(out,'COMPLETE.rds');if(file.exists(done))return(readRDS(done))
  tryCatch({
    history<-dataset_directory(run,id,scenario);plan<-readRDS(file.path(history,'frozen_plan.rds'))
    local<-plan$cfg;series<-make_targets(load_prices(root,id),local$mean_window);split<-calendar_split(series,local)
    checkpoint<-readRDS(file.path(history,'test/checkpoint.rds'))
    stopifnot(checkpoint$last_index==max(split$test_indices),plan$validation_end<'2012-01-01')
    registry<-plan$registry[job$rows,,drop=FALSE]
    # No order, model, weight, hyperparameter or threshold selection occurs here.
    result<-run_forecasts(split$series,split$later_indices,registry,local,id,'later',checkpoint$states,out)
    write_table(registry,file.path(out,'frozen_registry.csv'))
    status<-data.frame(dataset=id,scenario=scenario,group=job$group,phase='later',status='finished',n_dates=length(split$later_indices),message='')
    saveRDS(status,done);status
  },error=function(e){writeLines(conditionMessage(e),file.path(out,'ERROR.txt'));
    data.frame(dataset=id,scenario=scenario,group=job$group,phase='later',status='failed',n_dates=0,message=conditionMessage(e))})
}
combine_later <- function(root,run,cfg) {
  manifest<-read.csv(file.path(root,'data/manifest.csv'));metrics<-list()
  for(id in manifest$dataset[manifest$type=='stock'])for(scenario in c('baseline',sensitivity_plan()$scenario)) {
    out<-file.path(run,'later',scenario,id)
    files<-list.files(out,'^forecasts.csv$',recursive=TRUE,full.names=TRUE)
    fc<-bind_rows_fill(lapply(files,read.csv));stopifnot(nrow(fc)>0)
    plan<-readRDS(file.path(dataset_directory(run,id,scenario),'frozen_plan.rds'))
    if(scenario=='baseline')fc<-add_ensembles(fc,plan$members)
    write_table(fc,file.path(out,'test_forecasts.csv'))
    score<-calculate_metrics(fc);score$scenario<-scenario;metrics[[length(metrics)+1L]]<-score
    write_table(score,file.path(out,'metrics.csv'))
  }
  write_table(bind_rows_fill(metrics),file.path(run,'later_all_metrics.csv'))
}
