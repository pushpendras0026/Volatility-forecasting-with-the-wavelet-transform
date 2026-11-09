# Validation of tools/stat_tests.R (base R) against
#  (1) closed forms and published tables, and
#  (2) independent statsmodels 0.15.0 / scipy 1.18.1 values on the six real return
#      series (tests/reference/stat_tests_reference.csv, made by make_reference.py).
script<-sub('^--file=','',grep('^--file=',commandArgs(),value=TRUE)[1]);root<-dirname(dirname(normalizePath(script,winslash='/')))
for(f in list.files(file.path(root,'R'),pattern='[.]R$',full.names=TRUE))source(f)
source(file.path(root,'tools/stat_tests.R'))
# (1) Closed forms and published values.
x<-c(-2,-1,0,1,2,10)  # hand computation: n=6
d<-x-mean(x);S<-mean(d^3)/mean(d^2)^1.5;K<-mean(d^4)/mean(d^2)^2
stopifnot(abs(jarque_bera(x)$statistic-6/6*(S^2+(K-3)^2/4))<1e-12,
  abs(jarque_bera(x)$p.value-exp(-jarque_bera(x)$statistic/2))<1e-14)            # chi2(2) survival = exp(-x/2)
stopifnot(max(abs(mackinnon_crit_c(Inf)-c(-3.43035,-2.86154,-2.56677)))<1e-12)     # MacKinnon (2010) asymptotic
stopifnot(abs(mackinnon_p_c(-2.86154)-.05)<.003,abs(mackinnon_p_c(-3.43035)-.01)<.002,abs(mackinnon_p_c(-2.56677)-.10)<.005)
stopifnot(abs(kpss_test(rnorm(500))$critical[['5%']]-.463)<1e-12)                  # KPSS (1992) Table 1
set.seed(1);z<-rnorm(2000)
stopifnot(abs(shapiro_wilk(z)$p.value-shapiro.test(z)$p.value)<1e-15,
  adf_test(cumsum(z))$p.value>.05, adf_test(z)$p.value<.01,                         # random walk vs white noise
  kpss_test(cumsum(z))$p.value==.01, kpss_test(z)$p.value>.05)
# (2) Independent implementations on real data.
ref<-read.csv(file.path(root,'tests/reference/stat_tests_reference.csv'),stringsAsFactors=FALSE)
manifest<-read.csv(file.path(root,'data/manifest.csv'),stringsAsFactors=FALSE)
worst<-list()
for(ds in manifest$dataset)for(sample in c('training','full')) {
  p<-load_prices(root,ds);lp<-log(p$Price);r<-diff(lp);dt<-p$Date[-1]
  keep<-if(sample=='training')dt<=as.Date('2009-12-31')else rep(TRUE,length(r))
  x<-r[keep];l<-lp[-1][keep]
  a<-adf_test(x);k<-kpss_test(x)
  mine<-c(JB=jarque_bera(x)$statistic,skew_z=skewness_test(x)$statistic,kurt_z=kurtosis_test(x)$statistic,
    K2=dagostino_k2(x)$statistic,AD=anderson_darling(x)$statistic,SW=shapiro_wilk(x)$statistic,SW_p=shapiro_wilk(x)$p.value,
    ADF_tau=a$statistic,ADF_p=a$p.value,ADF_lag=a$lag,ADF_nobs=a$nobs,ADF_crit_5=a$critical[['5%']],
    KPSS=k$statistic,KPSS_lag=k$lag,KPSS_p=k$p.value,Q24=ljung_box(x)$statistic,ARCH_LM12=arch_lm(x)$statistic,
    logprice_ADF_tau=adf_test(l)$statistic,logprice_ADF_p=adf_test(l)$p.value,logprice_KPSS=kpss_test(l)$statistic)
  if(sample=='training'){b<-bds_test(x);mine<-c(mine,setNames(b$statistic,paste0('BDS_m',b$dim)))}
  rr<-ref[ref$series==ds&ref$sample==sample,]
  for(i in seq_len(nrow(rr))) {
    q<-rr$quantity[i];v<-unname(mine[q]);if(is.na(v))stop('missing ',q)
    rel<-abs(v-rr$value[i])/max(1e-300,abs(rr$value[i]))
    worst[[length(worst)+1L]]<-data.frame(series=ds,sample=sample,quantity=q,R=v,reference=rr$value[i],abs_diff=abs(v-rr$value[i]),rel_diff=rel)
  }
}
w<-do.call(rbind,worst)
# Integer lags must match exactly; continuous statistics to 1e-8 relative
# (Shapiro-Wilk: different algorithms for the W coefficients, 1e-4).
tol<-ifelse(w$quantity %in% c('SW','SW_p'),1e-4,1e-8)
bad<-w[w$rel_diff>tol,]
if(nrow(bad)){print(bad);stop('Statistical tests disagree with the reference implementation')}
agg<-aggregate(rel_diff~quantity,w,max);print(agg,row.names=FALSE)
out<-file.path(tempdir(),'stat_test_validation.csv');write.csv(w,out,row.names=FALSE)
cat(sprintf('PASS: %d statistic comparisons with statsmodels/scipy (max rel diff %.2g); closed forms; MacKinnon/KPSS tables.\n',nrow(w),max(w$rel_diff)))
