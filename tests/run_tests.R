script<-sub('^--file=','',grep('^--file=',commandArgs(),value=TRUE)[1]);root<-dirname(dirname(normalizePath(script,winslash='/')))
for(f in list.files(file.path(root,'R'),pattern='\\.R$',full.names=TRUE))source(f)
source(file.path(root,'config/experiment.R'));cfg<-experiment_config()
set.seed(719)
for(n in c(63,101,500))for(method in c('dwt','modwt'))for(filter in cfg$filters)for(J in 1:2) {
  x<-rnorm(n);c<-decompose_prefix(x,method,filter,J);stopifnot(max(abs(x-Reduce('+',c)))<1e-9)
}
x<-as.numeric(arima.sim(list(ar=.5,ma=.2),700))*.01
m<-fit_mean(x,1,1);p<-filter_mean(m,x)
stopifnot(abs(p$mu-as.numeric(predict(m$fit)$pred)*m$scale)<1e-10)
near<-diff(rnorm(1024,sd=.01))/2;m<-fit_mean(near,0,1);m$coef['ma1']<--.999999
ref<-arima(near/m$scale,order=c(0,0,1),fixed=m$coef,transform.pars=FALSE,method='ML')
stopifnot(abs(filter_mean(m,near)$mu-as.numeric(predict(ref)$pred)*m$scale)<1e-12)
e<-rt(1000,5)*sqrt(3/5)*.01;t<-fit_garch11_t(e);t100<-fit_garch11_t(100*e)
stopifnot(t$nu>2,sum(t$par[c('alpha','beta')])<1,
  abs(forecast_garch11(t100,100*e)/(1e4*forecast_garch11(t,e))-1)<.001)
z<-embed(e,13);ref<-summary(lm(z[,1]~z[,-1]))$fstatistic
stopifnot(abs(residual_lag_test(e)$F-unname(ref[1]))<1e-9,
  residual_lag_test(rep(0,100))$decision=='Not testable')
r<-rnorm(230,sd=.01);y<-c(rep(NA_real_,20),vapply(21:230,function(i)(r[i]-mean(r[(i-20):(i-1)]))^2,numeric(1)))
s<-data.frame(Date=as.Date('2004-01-01')+1:230,r=r,y=y)
local<-cfg;local$max_pq<-0L;local$mape_threshold<-1e-12;local$checkpoint_every<-100L
reg<-model_registry(local);reg<-reg[reg$model_id %in% c('raw_garch','dwt_garch','modwt_garch'),]
init<-initialize_models(s[1:200,],reg,local)
tmp<-tempfile();dir.create(tmp)
a<-run_forecasts(s,201:202,reg,local,'synthetic','test',init$states,file.path(tmp,'a'))
changed<-s;changed$r[201:230]<-10;changed$y[201:230]<-100
b<-run_forecasts(changed,201,reg,local,'synthetic','test',init$states,file.path(tmp,'b'))
stopifnot(max(abs(a$forecasts$prediction[1:3]-b$forecasts$prediction))<1e-12,
  nrow(a$diagnostics)==4,all(a$forecasts$fit_status=='ok'))  # raw x, DWT x+a, MODWT x
ens<-make_ensemble(a$forecasts,c('raw_garch','dwt_garch'),'ensemble')
stopifnot(nrow(ens)==2,all(ens$fit_status=='ok'))
broken<-a$forecasts;broken$fit_status[broken$model_id=='dwt_garch']<-'failed'
stopifnot(all(make_ensemble(broken,c('raw_garch','dwt_garch'),'ensemble')$fit_status=='missing_member'))
for(id in cfg$dataset_ids) {
  p<-load_prices(root,id);split<-calendar_split(make_targets(p),cfg)
  stopifnot(split$dates$train_end<as.Date('2010-01-01'),split$dates$validation_end<as.Date('2012-01-01'),
    split$dates$test_start>=as.Date('2012-01-01'),split$dates$test_end<=as.Date('2014-12-31'))
  if(id %in% c('india_infosys','usa_ibm','google_class_a'))stopifnot(length(split$later_indices)>2500)
}
stopifnot(nrow(model_registry(cfg))==38,!anyDuplicated(model_registry(cfg)$model_id),
  !any(grepl('fast|refit10|window512',model_registry(cfg)$model_id)),length(cfg$dataset_ids)==6)

# ---- MLP prediction in a fresh worker that has never loaded nnet ----------
yy<-abs(rnorm(300,sd=.01))^2;mfit<-fit_mlp(yy,3L,.01,101L,300L);local_pred<-predict_mlp(mfit,yy)$prediction
cl<-parallel::makePSOCKcluster(1L)
worker<-tryCatch({
  stopifnot(!parallel::clusterEvalQ(cl,'nnet'%in%loadedNamespaces())[[1]])
  parallel::clusterExport(cl,c('predict_mlp','mlp_features','mfit','yy'),envir=environment())
  parallel::clusterEvalQ(cl,predict_mlp(mfit,yy)$prediction)[[1]]
},finally=parallel::stopCluster(cl))
stopifnot(identical(worker,local_pred))

# ---- paired-DWT restoration conditions on the observed r_t ---------------
# Closed form: iid moments give back the raw-return moments.
z<-restore_paired_dwt_moments(0,4e-4,sqrt(2)*1e-3,4e-4,0.05)
stopifnot(abs(z$mu-1e-3)<1e-15,abs(z$h-4e-4)<1e-15)
# Simulation on iid N(0, 0.01^2) returns, production fitting functions, ARMA(0,0)-GARCH(1,1):
# mean target forecast / true E[y] must be ~1 for raw, DWT and MODWT; the unconditioned DWT
# mapping (r_t + sqrt2 mu_d, 2 h_d) gives ~2.8.
set.seed(42);sig<-.01;res<-NULL
for(k in 1:60) {
  r<-rnorm(1100,0,sig);w<-r[1:1024+50];last<-r[1074];m20<-mean(r[1055:1074])
  pr<-predict_stat_model(fit_stat_model(w,0,0,TRUE),w)
  comp<-paired_haar_components(w)
  pd<-predict_stat_model(fit_stat_model(comp$x,0,0,TRUE),comp$x);pa<-predict_stat_model(fit_stat_model(comp$a,0,0,TRUE),comp$a)
  new<-restore_paired_dwt_moments(pd$mu,pd$h,pa$mu,pa$h,last)
  dm<-causal_haar(w);pm<-predict_stat_model(fit_stat_model(dm,0,1,TRUE),dm);mw<-restore_haar_moments(pm$mu,pm$h,last,'modwt')
  res<-rbind(res,c(raw=return_moments_to_target(pr$mu,pr$h,m20),dwt=return_moments_to_target(new$mu,new$h,m20),
    dwt_old=return_moments_to_target(last+sqrt(2)*pd$mu,2*pd$h,m20),modwt=return_moments_to_target(mw$mu,mw$h,m20)))
}
level<-colMeans(res)/(sig^2*(1+1/20))
cat(sprintf('iid check, mean yhat / E[y]: raw %.3f, DWT conditioned %.3f, DWT unconditioned %.3f, MODWT %.3f
',level['raw'],level['dwt'],level['dwt_old'],level['modwt']))
stopifnot(abs(level['raw']-1)<.05,abs(level['dwt']-1)<.05,abs(level['dwt']/level['raw']-1)<.05,
  level['dwt_old']>2.3,abs(level['modwt']-1)<.05)

# ---- run id independent of location, invocation and line endings ------
files_of<-function(r){m<-read.csv(file.path(r,'data/manifest.csv'))
  c(list.files(file.path(r,'R'),full.names=TRUE),file.path(r,'config/experiment.R'),file.path(r,'run.R'),
    file.path(r,'data/manifest.csv'),file.path(r,'data',m$file))}
copy_tree<-function(dest){dir.create(dest,recursive=TRUE)
  for(d in c('R','config','data'))file.copy(file.path(root,d),dest,recursive=TRUE);file.copy(file.path(root,'run.R'),dest);dest}
c1<-copy_tree(file.path(tempdir(),'copy one'));c2<-copy_tree(file.path(tempdir(),'renamed_elsewhere','x'))
crlf<-file.path(c2,'R/mlp.R');txt<-readLines(crlf);con<-file(crlf,open='wb');writeLines(txt,con,sep=paste0(rawToChar(as.raw(13L)),'\n'));close(con)
stopifnot(any(readBin(crlf,'raw',file.size(crlf))==as.raw(13L)))
fp<-c(config_fingerprint(cfg,files_of(root),root),config_fingerprint(cfg,files_of(c1),c1),config_fingerprint(cfg,files_of(c2),c2))
stopifnot(length(unique(fp))==1L)
cat('PASS: data checksums, split boundaries, wavelet reconstruction, exact ARMA states, Student-t scaling, diagnostics, forecast prefix invariance, strict ensemble membership, fresh-worker MLP prediction, paired-DWT conditioning on iid returns, location/CRLF-independent run id.\n')
