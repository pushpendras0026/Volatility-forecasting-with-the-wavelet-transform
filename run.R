# One entry point. From any directory: Rscript code_submission/run.R --workers 16
# Output folder results/<id>: id = hash of config + root-relative code/data content,
# so it is identical for any install location or invocation (see README).
script<-normalizePath(sub('^--file=','',grep('^--file=',commandArgs(),value=TRUE)[1]),winslash='/')
root<-dirname(script)
for(f in list.files(file.path(root,'R'),pattern='\\.R$',full.names=TRUE))source(f)
source(file.path(root,'config/experiment.R'))
cfg<-experiment_config();args<-commandArgs(trailingOnly=TRUE)
# Execution options are kept OUT of cfg: cfg is saved into every job's frozen plan,
# so worker count or CLI flags must not change any output file (audit B1/m4).
requested_workers<-cfg$workers;cfg$workers<-NULL;historical_only<-baseline_only<-FALSE
for(i in seq_along(args)) {
  if(args[i]=='--workers')requested_workers<-as.integer(args[i+1])
  else if(args[i]=='--historical-only')historical_only<-TRUE
  else if(args[i]=='--baseline-only')baseline_only<-TRUE
}
stopifnot(requireNamespace('nnet',quietly=TRUE),is.finite(requested_workers),requested_workers>=1)
Sys.setenv(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
manifest<-read.csv(file.path(root,'data/manifest.csv'));stopifnot(setequal(manifest$dataset,cfg$dataset_ids),nrow(manifest)==6)
files<-c(list.files(file.path(root,'R'),full.names=TRUE),file.path(root,'config/experiment.R'),script,
  file.path(root,'data/manifest.csv'),file.path(root,'data',manifest$file))
id<-config_fingerprint(cfg,files,root);run<-file.path(root,'results',id);ensure_dir(run)
# LATEST.txt is written only after completion, as a root-relative path; while a
# run is in progress RUNNING.txt names it (read by tools/progress.R).
write_run_metadata(cfg,run,manifest);writeLines(file.path('results',id),file.path(root,'results/RUNNING.txt'))
write_table(sensitivity_plan(),file.path(run,'sensitivity_plan.csv'))
write_table(data.frame(file=relative_path(files,root),md5_lf=normalized_md5(files)),file.path(run,'code_data_checksums.csv'))
capture.output(sessionInfo(),file=file.path(run,'sessionInfo.txt'))
scenarios<-if(baseline_only)'baseline'else c('baseline',sensitivity_plan()$scenario)
jobs<-list()
for(scenario in scenarios)for(ds in cfg$dataset_ids)jobs[[length(jobs)+1L]]<-list(dataset=ds,scenario=scenario)
workers<-min(requested_workers,max(1L,parallel::detectCores()-2L),length(jobs))
message('Output: ',run,' | workers: ',workers,' | historical jobs: ',length(jobs))
cl<-parallel::makePSOCKcluster(workers)
exports<-setdiff(ls(envir=.GlobalEnv,all.names=TRUE),c('cl'))
parallel::clusterExport(cl,exports,envir=.GlobalEnv)
historical<-tryCatch(parallel::parLapplyLB(cl,jobs,run_historical_job,root=root,run=run,cfg=cfg),finally=parallel::stopCluster(cl))
status<-bind_rows_fill(historical);write_table(status,file.path(run,'historical_status.csv'))
if(any(status$status!='finished'))stop('Historical jobs failed; inspect ERROR.txt. Re-run to reuse completed jobs.')
if(!baseline_only)freeze_sensitivity_choices(run,cfg)
if(!historical_only&&!baseline_only) {
  jobs_later<-later_jobs(root,run,cfg)
  cl<-parallel::makePSOCKcluster(min(workers,length(jobs_later)))
  parallel::clusterExport(cl,setdiff(ls(envir=.GlobalEnv,all.names=TRUE),'cl'),envir=.GlobalEnv)
  later<-tryCatch(parallel::parLapplyLB(cl,jobs_later,run_later_job,root=root,run=run,cfg=cfg),finally=parallel::stopCluster(cl))
  later_status<-bind_rows_fill(later);write_table(later_status,file.path(run,'later_status.csv'))
  if(any(later_status$status!='finished'))stop('Later-period jobs failed; inspect ERROR.txt. Completed jobs are retained.')
  combine_later(root,run,cfg)
}
writeLines('All requested model jobs completed. Fit coverage must still be inspected.',file.path(run,'RUN_COMPLETE.txt'))
if(!historical_only&&!baseline_only)writeLines(file.path('results',id),file.path(root,'results/LATEST.txt'))
unlink(file.path(root,'results/RUNNING.txt'))
message('Finished: ',run)
