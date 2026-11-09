# Read only the isolated experiment's CSVs; write only inside Distribution.
script <- sub('^--file=', '', grep('^--file=', commandArgs(), value=TRUE)[1])
experiment <- dirname(normalizePath(script, winslash='/'))
# LATEST.txt holds 'results/<id>' relative to Distribution/; only the id is used,
# so the report works after the folder is moved or copied.
output <- file.path(experiment, 'results', basename(trimws(readLines(file.path(experiment, 'LATEST.txt'))[1])))
if (!file.exists(file.path(output, 'COMPLETE.txt'))) stop('A verified complete run is required')
x <- read.csv(file.path(output, 'innovation_distribution_comparison.csv'))
x <- x[x$split != 'validation', ]
labels <- c(gaussian='Gaussian', student_t='Student-t', ged='GED')
groups <- split(x, paste(x$split, x$dataset, x$pipeline, sep=' / '))
winners <- do.call(rbind, lapply(groups, function(g) {
  stopifnot(nrow(g)==3L, length(unique(g$n_common))==1L)
  base <- g$MSE[g$distribution=='gaussian']
  data.frame(dataset=g$dataset[1], pipeline=g$pipeline[1], period=g$split[1],
    best_MSE=g$distribution[which.min(g$MSE)], best_MAE=g$distribution[which.min(g$MAE)],
    student_t_MSE_change_pct=100*(g$MSE[g$distribution=='student_t']/base-1),
    GED_MSE_change_pct=100*(g$MSE[g$distribution=='ged']/base-1))
}))
write.csv(winners, file.path(output, 'heldout_winners.csv'), row.names=FALSE)
# Sample reconciliation: the Gaussian rows here are matched within the
# distribution trio {Gaussian, Student-t, GED} of one pipeline, whereas the main
# run's core table is matched within {raw, DWT, MODWT} GARCH. Same forecasts,
# different date sets, hence slightly different MSE.
root <- dirname(experiment)
main_run <- file.path(root, 'results', basename(trimws(readLines(file.path(output, 'baseline_source.txt'))[1])))
core <- read.csv(file.path(main_run, 'tables', 'core_scores.csv'))
g <- x[x$distribution == 'gaussian', ]
recon <- do.call(rbind, lapply(seq_len(nrow(g)), function(i) {
  c0 <- core[core$dataset == g$dataset[i] & core$profile == g$split[i] & core$model_id == g$pipeline[i], ]
  data.frame(dataset=g$dataset[i], pipeline=g$pipeline[i], period=g$split[i],
    distribution_trio_n=g$n_common[i], distribution_trio_MSE=g$MSE[i],
    core_trio_n=c0$n, core_trio_MSE=c0$MSE, own_n=g$independent_n[i], own_MSE=g$independent_MSE[i],
    MSE_difference_pct=100*(g$MSE[i]/c0$MSE-1),
    sample_rule_distribution='dates on which the Gaussian, Student-t and GED versions of this pipeline all succeeded',
    sample_rule_core='dates on which raw_garch, dwt_garch and modwt_garch (Gaussian) all succeeded')
}))
write.csv(recon, file.path(output, 'sample_reconciliation_distribution.csv'), row.names=FALSE)
counts <- data.frame(distribution=names(labels), MSE_wins=as.integer(table(factor(winners$best_MSE,levels=names(labels)))),
  MAE_wins=as.integer(table(factor(winners$best_MAE,levels=names(labels)))))
write.csv(counts, file.path(output, 'heldout_win_counts.csv'), row.names=FALSE)
attempt_files <- list.files(output, '^fit_attempts.csv$', recursive=TRUE, full.names=TRUE)
attempts <- do.call(rbind, lapply(attempt_files, read.csv))
write.csv(aggregate(cbind(attempts=rep(1L,nrow(attempts)), failures=as.integer(!attempts$converged),
  guard_flags=as.integer(attempts$shape_near_guard)) ~ distribution, attempts, sum),
  file.path(output, 'fit_status_summary.csv'), row.names=FALSE)
lines <- c('# Innovation distribution sensitivity results', '',
  'The primary Gaussian pipeline is unchanged. These are descriptive robustness results.', '',
  sprintf('The held-out comparison contains %d dataset/pipeline/period groups (%d distribution rows).',nrow(winners),nrow(x)),
  'Historical test: 2012–2014 for six series; later evaluation: 2015–2025 for three stocks.',
  'All three distributions in a group use common successful dates (the distribution-trio sample) and the existing project metrics.',
  'The main run core table matches raw/DWT/MODWT instead, so Gaussian MSEs can differ slightly from it; sample_reconciliation_distribution.csv lists both samples and n.', '',
  '| Distribution | Lowest MSE groups | Lowest MAE groups |', '|---|---:|---:|')
for (i in seq_len(nrow(counts))) lines <- c(lines, sprintf('| %s | %d | %d |',labels[counts$distribution[i]],counts$MSE_wins[i],counts$MAE_wins[i]))
lines <- c(lines, '',
  'Wins count groups equally and are descriptive; they do not measure statistical significance or the size of an improvement.',
  'The full CSV also reports RMSE, predictive R2, MAPE, masked MAPE, independent coverage and parameters.',
  'No single distribution is assumed to replace the Gaussian baseline. Inspect both metrics and improvement sizes below.', '',
  sprintf('Across all replayed periods (including validation): %d fit attempts, %d failed attempts, %d GED shape-guard flags.',
    nrow(attempts),sum(!attempts$converged),sum(attempts$shape_near_guard)),
  sprintf('Held-out forecasts: %d failed rows out of %d requested rows.',sum(x$forecast_failures),sum(x$requested)), '',
  'LogLik/AIC/BIC below describe the first successful refit within each period, conditional on fixed ARMA residuals. They are not joint ARMA-GARCH criteria.',
  'The fitting origin and residual sample size are shown. Lower AIC/BIC and higher LogLik describe that fit; lower MSE/MAE describe held-out forecasts.',
  'MAPE is undefined when the target crosses the existing threshold; the CSV retains the project\'s masked MAPE and exclusion counts.', '')
fmt <- function(z, digits=6L) ifelse(is.finite(z), formatC(z,digits=digits,format='g'), 'NA')
for (name in names(groups)) {
  g <- groups[[name]]; g <- g[match(names(labels),g$distribution), ]
  lines <- c(lines, paste0('## ',name), '',
    sprintf('ARMA(%d,%d), GARCH(1,1). Common held-out dates: %d. Fit origin(s): %s; fit n: %s.',
      g$p[1],g$q[1],g$n_common[1],paste(unique(g$fit_snapshot_origin),collapse=', '),paste(unique(g$fit_n),collapse=', ')), '',
    '| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |',
    '|---|---:|---:|---:|---:|---:|---:|---|')
  for (i in 1:3) lines <- c(lines, sprintf('| %s | %s | %s | %s | %s | %s | %.2f | %s |',
    labels[g$distribution[i]],fmt(g$loglik[i]),fmt(g$AIC[i]),fmt(g$BIC[i]),fmt(g$MSE[i]),fmt(g$MAE[i]),g$coverage_pct[i],if(g$converged[i])'Yes'else'No'))
  base <- g$MSE[g$distribution=='gaussian']
  lines <- c(lines,'',sprintf('MSE change relative to Gaussian: Student-t %+.3f%%; GED %+.3f%%. Lowest MSE: %s; lowest MAE: %s.',
    100*(g$MSE[g$distribution=='student_t']/base-1),100*(g$MSE[g$distribution=='ged']/base-1),
    labels[g$distribution[which.min(g$MSE)]],labels[g$distribution[which.min(g$MAE)]]),'')
}
lines <- c(lines,'## Interpretation and limitations','',
  sprintf('GED has the lowest MSE in %d of %d groups and the lowest MAE in %d; Student-t has the lowest MSE in %d and the lowest MAE in %d; Gaussian has the lowest MSE in %d and the lowest MAE in %d.',
    counts$MSE_wins[counts$distribution=='ged'],nrow(winners),counts$MAE_wins[counts$distribution=='ged'],
    counts$MSE_wins[counts$distribution=='student_t'],counts$MAE_wins[counts$distribution=='student_t'],
    counts$MSE_wins[counts$distribution=='gaussian'],counts$MAE_wins[counts$distribution=='gaussian']),
  'Alternative innovations can improve fit and/or forecasting performance for individual series and specifications. Fit rankings and forecasting rankings can differ, and MSE and MAE can favor different distributions.',
  'These point comparisons establish neither significance nor a universal winner. The Gaussian specification remains the primary baseline. The two-step Gaussian mean, optimizer starts, numerical guards and retrospective status of the later period are documented in ../../README.md.',
  'baseline_reproduction.csv verifies the existing Gaussian and Student-t forecast paths; baseline_integrity.csv verifies every protected file remained unchanged.')
failed <- attempts[!attempts$converged, ]
if (nrow(failed)) lines <- c(lines,'',sprintf('%d failed refit attempts came from the ARMA mean step; %d came from other fitting errors. Inspect each pipeline\'s fit_attempts.csv for dates and messages.',
  sum(grepl('^ARMA\\(',failed$error)),sum(!grepl('^ARMA\\(',failed$error))))
writeLines(lines, file.path(output, 'COMPARISON.md'))
print(counts, row.names=FALSE)
cat('Report:',file.path(output,'COMPARISON.md'),'\n')
