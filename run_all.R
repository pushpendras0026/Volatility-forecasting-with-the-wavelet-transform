# Cross-platform end-to-end reproduction (base R + nnet only):
#   Rscript run_all.R [--workers 16]
# 1 unit tests, 2 statistical-test validation, 3 main experiment (run.R),
# 4 tables/SUMMARY (analyze.R), 5 figures, 6-8 Distribution tests, experiment and
# report, 9 FILE_SHA256SUMS.csv. Each step runs in a fresh Rscript process and the
# script stops at the first failure. Completed jobs of an identical run are reused.
script<-normalizePath(sub('^--file=','',grep('^--file=',commandArgs(),value=TRUE)[1]),winslash='/')
root<-dirname(script);args<-commandArgs(trailingOnly=TRUE)
workers<-if(length(args)>=2&&args[1]=='--workers')args[2]else'16'
rscript<-file.path(R.home('bin'),if(.Platform$OS.type=='windows')'Rscript.exe'else'Rscript')
steps<-list(
  c('tests/run_tests.R'),c('tests/test_stat_tests.R'),c('run.R','--workers',workers),
  c('tools/analyze.R'),c('tools/figures.R'),c('Distribution/tests.R'),
  c('Distribution/innovation_distribution_robustness.R','--workers',workers),
  c('Distribution/report.R'),c('tools/package.R'))
for(s in steps) {
  t0<-Sys.time();message('== ',paste(s,collapse=' '))
  status<-system2(rscript,c(shQuote(file.path(root,s[1])),s[-1]))
  if(status!=0)stop('Step failed: ',s[1],' (exit ',status,')')
  message(sprintf('   done in %.1f min',as.numeric(difftime(Sys.time(),t0,units='mins'))))
}
message('All steps completed. Results: ',readLines(file.path(root,'results/LATEST.txt')))
