# Deterministic reporting. No fitting or model selection on test/later scores.
script<-sub('^--file=','',grep('^--file=',commandArgs(),value=TRUE)[1]);root<-dirname(dirname(normalizePath(script,winslash='/')))
for(f in list.files(file.path(root,'R'),pattern='\\.R$',full.names=TRUE))source(f)
source(file.path(root,'config/experiment.R'));cfg<-experiment_config()
run<-file.path(root,'results',basename(trimws(readLines(file.path(root,'results/LATEST.txt')))))
stopifnot(file.exists(file.path(run,'RUN_COMPLETE.txt')))
tables<-file.path(run,'tables');ensure_dir(tables)
manifest<-read.csv(file.path(root,'data/manifest.csv'),stringsAsFactors=FALSE)
# The run's code/data checksums (root-relative paths, CR-stripped MD5) must match
# the files now present: the reported tables come from exactly this code and data.
original_hash<-read.csv(file.path(run,'code_data_checksums.csv'),stringsAsFactors=FALSE)
stopifnot(all(normalized_md5(file.path(root,original_hash$file))==original_hash$md5_lf))
historical_status<-read.csv(file.path(run,'historical_status.csv'));later_status<-read.csv(file.path(run,'later_status.csv'))
stopifnot(nrow(historical_status)==42,all(historical_status$status=='finished'),nrow(later_status)==30,all(later_status$status=='finished'))
case_data<-list();plans<-list();core_scores<-pairwise<-coverage<-data_dates<-diagnostics<-candidate_grids<-selection<-list()
effects<-wavelet_effects<-likelihood_effects<-mlp_effects<-all_metrics<-list()
mlp_seed_effects<-list()
model_slots<-function(plan)c(dwt_garch='dwt_garch',modwt_garch='modwt_garch',selected_modwt=plan$selected_modwt,
  component=plan$selected_component,ensemble_base='ensemble_base_only',ensemble_all='ensemble_all',ensemble_modwt='ensemble_modwt',mlp='mlp')
paired_score <- function(fc,id,control,slot=id,bootstrap=FALSE,seed=101L) {
  a<-fc[fc$model_id==id,];b<-fc[fc$model_id==control,]
  if(!nrow(a)||!nrow(b))return(NULL)
  z<-merge(a[.valid_forecasts(a),],b[.valid_forecasts(b),],by='target_date',suffixes=c('_model','_control'))
  z<-z[order(z$target_date),];if(!nrow(z))return(NULL)
  stopifnot(max(abs(z$actual_model-z$actual_control))<1e-14)
  la<-(z$actual_model-z$prediction_model)^2;lb<-(z$actual_control-z$prediction_control)^2
  low<-high<-NA_real_
  if(bootstrap) {
    set.seed(seed);n<-length(la);B<-500L;block<-20L
    draws<-replicate(B,{s<-sample.int(n,ceiling(n/block),replace=TRUE)
      i<-head(as.vector(outer(0:(block-1L),s-1L,'+')%%n+1L),n)
      100*(1-mean(la[i])/mean(lb[i]))})
    low<-unname(quantile(draws,.025));high<-unname(quantile(draws,.975))
  }
  data.frame(dataset=a$dataset[1],period=a$profile[1],slot=slot,model_id=id,control=control,
    requested=nrow(a),successful_model=sum(.valid_forecasts(a)),successful_control=sum(.valid_forecasts(b)),
    n_common=nrow(z),MSE=mean(la),control_MSE=mean(lb),RMSE=sqrt(mean(la)),control_RMSE=sqrt(mean(lb)),
    MAE=mean(abs(z$actual_model-z$prediction_model)),improvement_pct=100*(1-mean(la)/mean(lb)),
    RMSE_ratio=sqrt(mean(la)/mean(lb)),descriptive_CI_low=low,descriptive_CI_high=high)
}
verify_fc <- function(fc,expected,period) {
  stopifnot(nrow(fc)>0,!anyDuplicated(paste(fc$model_id,fc$target_date)),
    all(as.Date(fc$origin_date)<as.Date(fc$target_date)),all(is.finite(fc$actual)),
    !any(grepl('fast|refit10|window512',fc$model_id)))
  for(id in unique(fc$model_id))stopifnot(sum(fc$model_id==id)==expected)
  valid<-fc[.valid_forecasts(fc),];stopifnot(all(valid$prediction>=0))
  z<-valid[is.finite(valid$return_mean)&is.finite(valid$return_variance),]
  stopifnot(all(z$return_variance>=0),max(abs(z$prediction-z$return_variance-(z$return_mean-z$moving_mean)^2))<1e-12)
  if(period=='test')stopifnot(all(fc$target_date>='2012-01-01'&fc$target_date<='2014-12-31'))
  else stopifnot(all(fc$target_date>='2015-01-01'&fc$target_date<='2025-12-31'))
}
for(ds in cfg$dataset_ids) {
  history<-dataset_directory(run,ds,'baseline');plan<-readRDS(file.path(history,'frozen_plan.rds'));plans[[ds]]<-plan
  split<-read.csv(file.path(history,'split.csv'));data_dates[[ds]]<-cbind(dataset=ds,split)
  grids<-read.csv(file.path(history,'initial_aic_diagnostics.csv'));grids$dataset<-ds;candidate_grids[[ds]]<-grids
  d<-read.csv(file.path(history,'validation/diagnostics.csv'));d<-d[d$origin_date==split$train_end,];diagnostics[[ds]]<-d
  selection[[ds]]<-data.frame(dataset=ds,selected_modwt=plan$selected_modwt,selected_component=plan$selected_component,
    mlp_hidden=plan$mlp$selected$hidden,mlp_decay=plan$mlp$selected$decay,mlp_fallback=plan$mlp$fallback,
    members_base=paste(plan$members$base,collapse=';'),members_combined=paste(plan$members$all,collapse=';'),
    members_modwt=paste(plan$members$modwt,collapse=';'))
  for(period in c('test',if(ds %in% manifest$dataset[manifest$type=='stock'])'later')) {
    folder<-if(period=='test')history else file.path(run,'later/baseline',ds)
    fc<-read.csv(file.path(folder,'test_forecasts.csv'));expected<-if(period=='test')split$n_test else split$n_later
    verify_fc(fc,expected,period);case_data[[paste(ds,period,sep='|')]]<-fc
    core<-fc[fc$model_id %in% c('raw_garch','dwt_garch','modwt_garch'),]
    core_scores[[length(core_scores)+1L]]<-calculate_metrics(core)
    all_metrics[[length(all_metrics)+1L]]<-calculate_metrics(fc)
    for(id in unique(fc$model_id)) {
      z<-fc[fc$model_id==id,]
      coverage[[length(coverage)+1L]]<-data.frame(dataset=ds,period=period,model_id=id,requested=nrow(z),
        successful=sum(.valid_forecasts(z)),coverage_pct=100*mean(.valid_forecasts(z)))
    }
    for(ens in c('ensemble_base_only','ensemble_all','ensemble_modwt')) {
      members<-switch(ens,ensemble_base_only=plan$members$base,ensemble_all=plan$members$all,ensemble_modwt=plan$members$modwt)
      expected_fc<-make_ensemble(fc,members,ens);actual_fc<-fc[fc$model_id==ens,]
      join<-merge(expected_fc,actual_fc,by='target_date',suffixes=c('_expected','_actual'))
      ok<-is.finite(join$prediction_expected)
      stopifnot(nrow(join)==expected,all(join$fit_status_expected==join$fit_status_actual))
      if(any(ok))stopifnot(max(abs(join$prediction_expected[ok]-join$prediction_actual[ok]))<1e-12)
    }
    slots<-model_slots(plan)
    for(slot in names(slots)) {
      z<-paired_score(fc,slots[[slot]],'raw_garch',slot,bootstrap=TRUE,seed=101L+length(pairwise))
      if(!is.null(z))pairwise[[length(pairwise)+1L]]<-z
    }
    # Every MRA and distribution variant, not only the test winners.
    for(id in unique(fc$model_id)[grepl('^mra_',unique(fc$model_id))]) {
      z<-paired_score(fc,id,'raw_garch');if(is.null(z))next
      spec<-plan$registry[plan$registry$model_id==id,]
      wavelet_effects[[length(wavelet_effects)+1L]]<-cbind(z,spec[,c('transform','filter','J','allocation')])
    }
    for(id in c('raw_garch_student_t','dwt_garch_student_t','modwt_garch_student_t','modwt_garch_structural','modwt_garch_structural_student_t')) {
      control<-if(grepl('structural',id))'modwt_garch'else sub('_student_t$','',id)
      z<-paired_score(fc,id,control);if(!is.null(z))likelihood_effects[[length(likelihood_effects)+1L]]<-z
    }
    for(id in c('mlp','mlp_seed202','mlp_seed303')) {
      z<-paired_score(fc,id,'raw_garch');if(!is.null(z))mlp_seed_effects[[length(mlp_seed_effects)+1L]]<-z
    }
  }
  # MLP candidate effects use validation forecasts only, on matched dates.
  val<-read.csv(file.path(history,'validation/forecasts.csv'));reg<-mlp_registry(cfg)
  for(i in seq_len(nrow(reg))) {
    z<-paired_score(val,reg$model_id[i],'raw_garch');if(is.null(z))next
    mlp_effects[[length(mlp_effects)+1L]]<-cbind(z,reg[i,c('hidden','decay','seed')])
  }
}
frozen_params<-read.csv(file.path(run,'frozen_parameter_choices.csv'))
for(ds in cfg$dataset_ids)for(period in c('test',if(ds %in% manifest$dataset[manifest$type=='stock'])'later')) {
  base<-case_data[[paste(ds,period,sep='|')]]
  for(scenario in sensitivity_plan()$scenario) {
    path<-if(period=='test')file.path(dataset_directory(run,ds,scenario),'test_forecasts.csv')else file.path(run,'later',scenario,ds,'test_forecasts.csv')
    fc<-read.csv(path);verify_fc(fc,length(unique(base$target_date)),period)
    for(id in c('raw_garch','dwt_garch','modwt_garch')) {
      a<-fc[fc$model_id==id,];b<-base[base$model_id==id,];b$model_id<-paste0(id,'_default')
      z<-paired_score(bind_rows_fill(list(a,b)),id,paste0(id,'_default'))
      if(is.null(z))next
      setting<-sensitivity_plan();setting<-setting[setting$scenario==scenario,]
      selected<-frozen_params$selected_scenario[frozen_params$dataset==ds&frozen_params$model_id==id]
      effects[[length(effects)+1L]]<-cbind(z,setting[,c('scenario','max_window','refit_every','criterion','max_pq')],selected_on_validation=scenario==selected)
    }
  }
}
# Every score table states its matched-date sample: n_common/n plus a
# sample_rule column. Different rules give the same model different numbers.
RULE<-list(
  core='intersection of dates on which raw_garch, dwt_garch and modwt_garch all succeeded (per dataset/period)',
  all='intersection of dates on which every model with >=1 success in the dataset/period succeeded (44 model IDs)',
  pair='dates on which both the model and its control succeeded',
  own='all dates on which this model succeeded (independent_* columns)',
  mlp='dates on which raw_garch, mlp, mlp_seed202, mlp_seed303 and the three ensembles all succeeded',
  validation_pair='validation 2010-2011, pairwise with raw_garch')
# Wall-clock columns differ on every re-run; they go to timing.csv only, so all
# published score tables are bit-identical across re-runs and worker counts.
timing_cols<-c('median_seconds','total_seconds')
label<-function(x,rule){x<-bind_rows_fill(x);if(nrow(x)){x$sample_rule<-rule;x<-x[,setdiff(names(x),timing_cols),drop=FALSE]};x}
timing<-bind_rows_fill(all_metrics);write_table(timing[,intersect(c('dataset','profile','split','model_id',timing_cols),names(timing))],file.path(tables,'timing.csv'))
core<-label(core_scores,RULE$core);pairs<-label(pairwise,RULE$pair);cov<-bind_rows_fill(coverage)
write_table(core,file.path(tables,'core_scores.csv'));write_table(pairs,file.path(tables,'extension_comparisons.csv'))
write_table(cov,file.path(tables,'coverage.csv'));write_table(bind_rows_fill(data_dates),file.path(tables,'splits.csv'))
write_table(bind_rows_fill(diagnostics),file.path(tables,'initial_diagnostics.csv'))
write_table(bind_rows_fill(candidate_grids),file.path(tables,'aic_candidate_grids.csv'))
write_table(bind_rows_fill(selection),file.path(tables,'frozen_selections.csv'))
write_table(label(effects,'pairwise: scenario forecast and default forecast of the same pipeline both succeeded'),file.path(tables,'parameter_effects.csv'))
write_table(label(wavelet_effects,RULE$pair),file.path(tables,'wavelet_effects.csv'))
write_table(label(likelihood_effects,RULE$pair),file.path(tables,'likelihood_order_effects.csv'))
write_table(label(mlp_effects,RULE$validation_pair),file.path(tables,'mlp_validation_effects.csv'))
write_table(label(mlp_seed_effects,RULE$pair),file.path(tables,'mlp_test_seed_effects.csv'))
all_scores<-label(all_metrics,RULE$all);write_table(all_scores,file.path(tables,'all_model_scores.csv'))

# Same model under each sample definition (one reconciliation table).
score_dates<-function(fc,id,dates){z<-fc[fc$model_id==id&fc$target_date %in% dates,]
  if(!nrow(z))return(list(n=0L,MSE=NA_real_,RMSE=NA_real_,MAE=NA_real_,start=NA_character_,end=NA_character_))
  e<-z$actual-z$prediction
  list(n=nrow(z),MSE=mean(e^2),RMSE=sqrt(mean(e^2)),MAE=mean(abs(e)),start=min(z$target_date),end=max(z$target_date))}
ok_dates<-function(fc,ids)Reduce(intersect,lapply(ids,function(id){z<-fc[fc$model_id==id,];z$target_date[.valid_forecasts(z)]}))
mlp_ids<-c('raw_garch','mlp','mlp_seed202','mlp_seed303','ensemble_base_only','ensemble_all','ensemble_modwt')
recon<-list();mlp_table<-list()
for(key in names(case_data)) {
  fc<-case_data[[key]];ds<-fc$dataset[1];period<-fc$profile[1]
  active<-unique(fc$model_id[.valid_forecasts(fc)])
  samples<-list(own=NULL,core=ok_dates(fc,c('raw_garch','dwt_garch','modwt_garch')),all=ok_dates(fc,active),mlp=ok_dates(fc,mlp_ids))
  for(id in c('raw_garch','dwt_garch','modwt_garch','ensemble_modwt','mlp'))for(sn in names(samples)) {
    dates<-if(sn=='own'){z<-fc[fc$model_id==id,];z$target_date[.valid_forecasts(z)]}else samples[[sn]]
    v<-score_dates(fc,id,dates)
    recon[[length(recon)+1L]]<-data.frame(dataset=ds,period=period,model_id=id,sample=sn,sample_rule=RULE[[sn]],
      n=v$n,MSE=v$MSE,RMSE_x1e4=1e4*v$RMSE,MAE_x1e4=1e4*v$MAE,first_date=v$start,last_date=v$end)
  }
  if(period=='test'){d<-samples$mlp
    mlp_table[[ds]]<-data.frame(dataset=ds,n=length(d),raw_garch=1e4*score_dates(fc,'raw_garch',d)$RMSE,
      mlp_seed101=1e4*score_dates(fc,'mlp',d)$RMSE,mlp_seed202=1e4*score_dates(fc,'mlp_seed202',d)$RMSE,
      mlp_seed303=1e4*score_dates(fc,'mlp_seed303',d)$RMSE,sample_rule=RULE$mlp)}
}
recon<-bind_rows_fill(recon);rownames(recon)<-NULL
write_table(recon,file.path(tables,'sample_reconciliation.csv'))
mlp_table<-bind_rows_fill(mlp_table);write_table(mlp_table,file.path(tables,'mlp_seed_table.csv'))

# Descriptive statistics, normality, stationarity and independence tests on
# decimal log returns (tools/stat_tests.R; validated in tests/test_stat_tests.R).
source(file.path(root,'tools/stat_tests.R'))
desc<-list()
for(ds in cfg$dataset_ids) {
  p<-load_prices(root,ds);r<-diff(log(p$Price));dt<-p$Date[-1]
  for(sample in c('training','full')) {
    keep<-if(sample=='training')dt<=as.Date(cfg$training[2])else rep(TRUE,length(r))
    desc[[length(desc)+1L]]<-cbind(data.frame(dataset=ds,label=manifest$label[manifest$dataset==ds],sample=sample,
      first_return=as.character(min(dt[keep])),last_return=as.character(max(dt[keep]))),describe_returns(r[keep]))
    invisible(gc())
  }
}
desc<-bind_rows_fill(desc);write_table(desc,file.path(tables,'descriptive_normality_stationarity.csv'))

trend<-list()
for(ds in manifest$dataset[manifest$type=='stock'])for(slot in unique(pairs$slot)) {
  a<-pairs[pairs$dataset==ds&pairs$period=='test'&pairs$slot==slot,]
  b<-pairs[pairs$dataset==ds&pairs$period=='later'&pairs$slot==slot,]
  if(!nrow(a)||!nrow(b))next
  trend[[length(trend)+1L]]<-data.frame(dataset=ds,slot=slot,model_id=a$model_id,
    historical_gain_pct=a$improvement_pct,later_gain_pct=b$improvement_pct,
    historical_n=a$n_common,later_n=b$n_common,same_direction=sign(a$improvement_pct)==sign(b$improvement_pct),
    historical_coverage=100*a$successful_model/a$requested,later_coverage=100*b$successful_model/b$requested)
}
trend<-label(trend,paste('each period',RULE$pair));write_table(trend,file.path(tables,'later_period_trends.csv'))

# Full all-model before/after table, using the same model IDs in both periods.
full_trend<-list()
for(ds in manifest$dataset[manifest$type=='stock']) {
  a<-case_data[[paste(ds,'test',sep='|')]];b<-case_data[[paste(ds,'later',sep='|')]]
  for(id in intersect(unique(a$model_id),unique(b$model_id))) {
    aa<-paired_score(a,id,'raw_garch');bb<-paired_score(b,id,'raw_garch')
    if(is.null(aa)||is.null(bb))next
    full_trend[[length(full_trend)+1L]]<-data.frame(dataset=ds,model_id=id,
      historical_gain_pct=aa$improvement_pct,later_gain_pct=bb$improvement_pct,
      historical_n=aa$n_common,later_n=bb$n_common,same_direction=sign(aa$improvement_pct)==sign(bb$improvement_pct))
  }
}
write_table(label(full_trend,paste('each period',RULE$pair)),file.path(tables,'all_model_later_comparison.csv'))
annual<-list()
for(ds in manifest$dataset[manifest$type=='stock']) {
  fc<-case_data[[paste(ds,'later',sep='|')]];slots<-model_slots(plans[[ds]])
  for(year in 2015:2025)for(slot in names(slots)) {
    z<-fc[substr(fc$target_date,1,4)==as.character(year),]
    score<-paired_score(z,slots[[slot]],'raw_garch',slot)
    if(!is.null(score)){score$year<-year;annual[[length(annual)+1L]]<-score}
  }
}
write_table(label(annual,paste('each calendar year',RULE$pair)),file.path(tables,'annual_stock_effects.csv'))

# Initial means identify orders; later plans must preserve those same orders.
for(ds in manifest$dataset[manifest$type=='stock'])for(scenario in c('baseline',sensitivity_plan()$scenario)) {
  base<-readRDS(file.path(dataset_directory(run,ds,scenario),'frozen_plan.rds'))
  groups<-list.dirs(file.path(run,'later',scenario,ds),recursive=FALSE,full.names=TRUE)
  for(g in groups) {
    if(!file.exists(file.path(g,'frozen_registry.csv')))next
    reg<-read.csv(file.path(g,'frozen_registry.csv'));stopifnot(all(reg$model_id %in% base$registry$model_id))
    later_states<-readRDS(file.path(g,'checkpoint.rds'))$states
    for(id in reg$model_id[reg$kind!='baseline'&reg$kind!='mlp']) {
      orig<-base$initial_orders[base$initial_orders$model_id==id,]
      for(cn in orig$component)stopifnot(all(later_states[[id]]$orders[[cn]]==c(p=orig$p[orig$component==cn],q=orig$q[orig$component==cn])))
    }
  }
}
stopifnot(readRDS(file.path(run,'frozen_parameter_choices.rds'))$source_period=='2010-2011 validation only')
writeLines('PASS: 42 historical and 30 later jobs; six datasets; original fit-code/data checksums; chronological bounds; forecast coverage and moment identities; frozen choices/orders; exact ensemble membership.',file.path(run,'VERIFIED.txt'))

md_table<-function(headers,rows)c(paste0('| ',paste(headers,collapse=' | '),' |'),paste0('| ',paste(rep('---',length(headers)),collapse=' | '),' |'),
  apply(rows,1,function(x)paste0('| ',paste(x,collapse=' | '),' |')))
display<-do.call(rbind,lapply(cfg$dataset_ids,function(ds) {
  z<-core[core$dataset==ds&core$profile=='test',]
  data.frame(Series=manifest$label[manifest$dataset==ds],n=z$n[1],first=z$common_start[1],last=z$common_end[1],
    Raw=sprintf('%.4f',z$RMSE[z$model_id=='raw_garch']*1e4),DWT=sprintf('%.4f',z$RMSE[z$model_id=='dwt_garch']*1e4),MODWT=sprintf('%.4f',z$RMSE[z$model_id=='modwt_garch']*1e4))
}))
tr<-trend[,c('dataset','slot','historical_gain_pct','historical_n','later_gain_pct','later_n','same_direction')]
tr$historical_gain_pct<-sprintf('%+.2f%%',tr$historical_gain_pct);tr$later_gain_pct<-sprintf('%+.2f%%',tr$later_gain_pct)
f4<-function(x)sprintf('%.4f',x)
rc<-recon[recon$model_id=='raw_garch',];rc<-data.frame(Series=rc$dataset,Period=rc$period,Sample=rc$sample,n=rc$n,RMSE_x1e4=f4(rc$RMSE_x1e4))
ml<-data.frame(Series=mlp_table$dataset,n=mlp_table$n,Raw=f4(mlp_table$raw_garch),Seed101=f4(mlp_table$mlp_seed101),
  Seed202=f4(mlp_table$mlp_seed202),Seed303=f4(mlp_table$mlp_seed303))
g<-function(x)formatC(x,digits=3,format='g');pv<-function(x)ifelse(x<1e-4,'<1e-4',sprintf('%.4f',x))
dd<-data.frame(Series=desc$label,Sample=paste0(desc$sample,' (',desc$first_return,'..',desc$last_return,')'),n=desc$n,
  Mean=g(desc$mean),SD=g(desc$sd),Skew=sprintf('%.3f',desc$skewness),ExcessKurt=sprintf('%.2f',desc$excess_kurtosis),
  Kurt=sprintf('%.2f',desc$kurtosis_raw),JB_p=pv(desc$JB_p),
  ADF=sprintf('%.2f (p %s, lag %d)',desc$ADF_tau,pv(desc$ADF_p),desc$ADF_lag),
  KPSS=sprintf('%.3f (%s)',desc$KPSS,desc$KPSS_p_bound),Q24_p=pv(desc$Q24_p))
writeLines(c('# Final six-series results','',
 'Training 2004-2009; validation 2010-2011; historical test 2012-2014. Later stock evaluation 2015-2025. Settings and members remain frozen; fitted parameters update on observed prefixes.','',
 '## How every number is sampled','',
 'Forecasts can fail on some dates, so each score is computed on a stated matched-date sample. The same model therefore has slightly different scores in different tables. Rules used here:','',
 paste0('- core: ',RULE$core,'.'),paste0('- all-model: ',RULE$all,'.'),paste0('- pairwise: ',RULE$pair,'.'),
 paste0('- MLP table: ',RULE$mlp,'.'),paste0('- own: ',RULE$own,'.'),
 '- Distribution/ results: dates on which the Gaussian, Student-t and GED versions of one pipeline all succeeded (Distribution/results/<id>/sample_reconciliation_distribution.csv).','',
 '`tables/sample_reconciliation.csv` reports raw/DWT/MODWT GARCH, the MODWT ensemble and the MLP under every rule.','',
 '## Core GARCH comparison','','RMSE x 10,000, historical test 2012-2014. Sample: core rule; n = number of matched dates.','',md_table(names(display),display),'',
 '## Raw GARCH under each sample rule','','RMSE x 10,000. Differences between rows come only from the dates included.','',md_table(names(rc),rc),'',
 '## MLP seeds versus raw GARCH','',paste0('RMSE x 10,000, 2012-2014. Sample: ',RULE$mlp,'.'),'',md_table(names(ml),ml),'',
 '## Same definitions on later stock data','',
 'Positive percentages mean lower MSE than raw GARCH. Each period uses pairwise matched dates (n shown). The trend column compares only the sign of the point MSE difference.','',
 md_table(names(tr),tr),'',
 '## Returns: descriptive statistics, normality and stationarity','',
 'Decimal log returns. Kurt is raw kurtosis (normal = 3); ExcessKurt = Kurt - 3. JB: Jarque-Bera, chi2(2). ADF: constant, AIC lag choice, MacKinnon p-value. KPSS: level stationarity, Bartlett kernel with Hobijn-Franses-Ooms bandwidth, p from the KPSS (1992) table (bounded to 0.01-0.10). Q24_p: Ljung-Box Q(24) on returns. Skewness/kurtosis z-tests, K2, Anderson-Darling, Shapiro-Wilk, Q(24) of squares, ARCH-LM(12) and BDS (m = 2..6) are in tables/descriptive_normality_stationarity.csv. Tunisia kurtosis is dominated by the -0.27/+0.27 returns of 15-16 Sep 2004 (data/issues.csv).','',
 md_table(names(dd),dd),'',
 '## What is included','',
 '- All 44 final model IDs per dataset, including the three ensembles and three MLP seeds; 24 wavelet component specifications.',
 '- Six sensitivity scenarios for each of the three core GARCH pipelines on all six series, and on the stocks after 2014.',
 '- Full AIC/diagnostic grids, validation selections, failed fits, raw forecasts, coverage, parameter effects, and descriptive paired block-bootstrap intervals.',
 '- Paired DWT forecasts condition on the observed first return of the forecast pair (detail and approximation models; see ARCHITECTURE.md).',
 '- These are retrospective historical comparisons. Small loss differences and unadjusted descriptive intervals do not establish universal superiority.',
 '- The MRA mixed branch sums conditional means; residual GARCH variance is not added to its point target forecast.'),file.path(run,'SUMMARY.md'))
file.copy(file.path(run,'SUMMARY.md'),file.path(root,'results/SUMMARY.md'),overwrite=TRUE)
writeLines(basename(run),file.path(root,'results/FINAL_RUN.txt'))
cat('Verified report: ',run,'\n')
