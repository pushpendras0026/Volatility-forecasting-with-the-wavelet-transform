# All choices are declared here before test/later-period evaluation.
experiment_config <- function() list(
  seed=101L,workers=16L,mean_window=20L,max_window=1024L,refit_every=20L,
  max_pq=3L,component_max_pq=2L,criterion='AIC',max_origins=Inf,selection_min_coverage=.95,
  validation_stride=1L,test_stride=1L,checkpoint_every=100L,
  mlp_hidden=c(3L,5L),mlp_decay=c(.001,.01),mlp_seeds=c(101L,202L,303L),mlp_maxit=300L,
  filters=c('haar','db4','db6'),levels=c(1L,2L),
  target_id='squared_deviation_trailing20_decimal',
  training=c('2004-01-01','2009-12-31'),validation=c('2010-01-01','2011-12-31'),
  test=c('2012-01-01','2014-12-31'),later=c('2015-01-01','2025-12-31'),
  dataset_ids=c('south_africa','tunisia','nigeria','india_infosys','usa_ibm','google_class_a'))

model_registry <- function(cfg) {
  base <- data.frame(model_id=c('naive','trailing_mean','raw_arima','dwt_arima','raw_garch','dwt_garch','modwt_arima','modwt_garch','direct_y_arima'),
    stage=c('baseline','baseline',rep('core',6),'component'),kind=c('baseline','baseline',rep('stat',6),'direct'),
    transform=c('none','none','none','dwt','none','dwt','modwt','modwt','none'),filter='haar',
    allocation='none',J=1L,garch=c(FALSE,FALSE,FALSE,FALSE,TRUE,TRUE,FALSE,TRUE,FALSE),
    distribution='gaussian',order_rule='aic',stringsAsFactors=FALSE)
  variants <- base[base$model_id %in% c('raw_garch','dwt_garch','modwt_garch'),]
  variants$model_id<-paste0(variants$model_id,'_student_t');variants$distribution<-'student_t'
  structural<-base[base$model_id=='modwt_garch',];structural<-structural[c(1,1),]
  structural$model_id<-c('modwt_garch_structural','modwt_garch_structural_student_t')
  structural$distribution<-c('gaussian','student_t');structural$order_rule<-'raw_plus_one_ma'
  ext<-expand.grid(transform=c('dwt','modwt'),filter=cfg$filters,allocation=c('all_arima','mixed'),J=cfg$levels,stringsAsFactors=FALSE)
  ext$model_id<-paste('mra',ext$transform,ext$filter,ext$allocation,sep='_')
  ext$model_id[ext$J==1]<-paste0(ext$model_id[ext$J==1],'_j1')
  ext$stage<-'component';ext$kind<-'mra';ext$garch<-FALSE;ext$distribution<-'gaussian';ext$order_rule<-'aic'
  rbind(base,variants,structural,ext[,names(base)])
}

sensitivity_plan <- function() data.frame(
  scenario=c('window768','window1536','cadence40','cadence60','criterionBIC','order_cap5'),
  max_window=c(768,1536,1024,1024,1024,1024),refit_every=c(20,20,40,60,20,20),
  criterion=c('AIC','AIC','AIC','AIC','BIC','AIC'),max_pq=c(3,3,3,3,3,5),
  scope='raw_garch,dwt_garch,modwt_garch',stringsAsFactors=FALSE)
