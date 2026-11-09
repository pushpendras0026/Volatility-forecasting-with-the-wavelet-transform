script<-sub('^--file=','',grep('^--file=',commandArgs(),value=TRUE)[1]);root<-dirname(dirname(normalizePath(script,winslash='/')))
for(f in list.files(file.path(root,'R'),pattern='\\.R$',full.names=TRUE))source(f)
source(file.path(root,'config/experiment.R'));cfg<-experiment_config()
run<-file.path(root,'results',basename(trimws(readLines(file.path(root,'results/LATEST.txt')))));tab<-file.path(run,'tables');out<-file.path(run,'figures');ensure_dir(out)
manifest<-read.csv(file.path(root,'data/manifest.csv'));labels<-setNames(manifest$label,manifest$dataset)
core<-read.csv(file.path(tab,'core_scores.csv'));pairs<-read.csv(file.path(tab,'extension_comparisons.csv'))
effects<-read.csv(file.path(tab,'parameter_effects.csv'));wave<-read.csv(file.path(tab,'wavelet_effects.csv'))
likelihood<-read.csv(file.path(tab,'likelihood_order_effects.csv'));neural<-read.csv(file.path(tab,'mlp_validation_effects.csv'))
colors<-c(raw='#2463A6',dwt='#D47A20',modwt='#15846B',component='#678A35',ensemble='#65358D',mlp='#C84D57',actual='#555555')
device<-function(name,width=2000,height=1250,pointsize=18) {
  png(file.path(out,paste0(name,'.png')),width=width,height=height,res=200,pointsize=pointsize)
  par(family='sans',col.axis='#344250',col.lab='#263442',col.main='#17344B',mgp=c(2.4,.65,0),las=1,bty='l')
}
geomean<-function(x)exp(mean(log(x[is.finite(x)&x>0])))
heatmap_plot<-function(name,mat,rowlabels,collabels,title,center=0,digits=1,lower_better=FALSE,color_limit=NULL) {
  device(name,2000,1250,18);par(mar=c(5,10,4,1))
  bound<-max(abs(mat-center),na.rm=TRUE);if(!is.finite(bound)||bound==0)bound<-1
  if(!is.null(color_limit))bound<-min(bound,color_limit)
  palette<-colorRampPalette(if(lower_better)c('#15846B','#FFFFFF','#BC5858')else c('#BC5858','#FFFFFF','#15846B'))(101)
  fill<-mat;fill[]<-pmax(center-bound,pmin(center+bound,mat))
  image(seq_len(ncol(mat)),seq_len(nrow(mat)),t(fill[nrow(mat):1,,drop=FALSE]),
    col=palette,zlim=c(center-bound,center+bound),axes=FALSE,xlab='',ylab='',main=title,cex.main=.95)
  axis(1,seq_len(ncol(mat)),collabels,tick=FALSE,cex.axis=.82)
  axis(2,seq_len(nrow(mat)),rev(rowlabels),tick=FALSE,cex.axis=.78)
  for(i in seq_len(nrow(mat)))for(j in seq_len(ncol(mat)))if(is.finite(mat[i,j]))
    text(j,nrow(mat)-i+1,sprintf(paste0('%.',digits,'f'),mat[i,j]),cex=.85,
      col=if(abs(mat[i,j]-center)/bound>.65)'white'else'#1C2530')else text(j,nrow(mat)-i+1,'--',cex=.85,col='#445260')
  if(!is.null(color_limit))mtext(paste0('Color saturates at +/-',color_limit,'; labels retain full values.'),side=1,line=3,cex=.65)
  box();dev.off()
}
ratio<-sapply(cfg$dataset_ids,function(ds) {
  z<-core[core$dataset==ds&core$profile=='test',];z$RMSE[match(c('raw_garch','dwt_garch','modwt_garch'),z$model_id)]/z$RMSE[z$model_id=='raw_garch']
})
device('core_comparison',2000,1150,18);par(mar=c(4,4.5,3.5,1))
x<-barplot(ratio,beside=TRUE,col=colors[c('raw','dwt','modwt')],border=NA,names.arg=unname(labels[cfg$dataset_ids]),
  ylab='RMSE / raw GARCH RMSE',ylim=c(0,max(ratio,na.rm=TRUE)*1.25),cex.names=.85,main='Historical test: 2012-2014')
abline(h=1,lty=2,col='#777777');text(x,ratio,sprintf('%.3f',ratio),pos=3,cex=.72)
legend('top',c('Raw GARCH','DWT-GARCH','MODWT-GARCH'),fill=colors[c('raw','dwt','modwt')],horiz=TRUE,bty='n',cex=.85)
dev.off();write_table(data.frame(model=rep(c('raw_garch','dwt_garch','modwt_garch'),6),dataset=rep(cfg$dataset_ids,each=3),RMSE_ratio=as.vector(ratio)),file.path(out,'core_comparison.csv'))

slots<-c('selected_modwt','component','ensemble_base','ensemble_all','ensemble_modwt','mlp')
slot_labels<-c('Selected MODWT','Selected component','Base ensemble','Combined ensemble','MODWT ensemble','MLP (seed 101)')
mat<-matrix(NA_real_,length(slots),6)
for(i in seq_along(slots))for(j in seq_along(cfg$dataset_ids)) {
  z<-pairs[pairs$period=='test'&pairs$dataset==cfg$dataset_ids[j]&pairs$slot==slots[i],]
  if(nrow(z))mat[i,j]<-z$improvement_pct
}
heatmap_plot('historical_extension_gains',mat,slot_labels,unname(labels[cfg$dataset_ids]),'MSE reduction versus raw GARCH (%)',digits=1,color_limit=30)

# Core and extension forecasts use the same visible range within each market.
for(ds in cfg$dataset_ids)for(period in c('test',if(ds %in% manifest$dataset[manifest$type=='stock'])'later')) {
  history<-dataset_directory(run,ds,'baseline');plan<-readRDS(file.path(history,'frozen_plan.rds'))
  folder<-if(period=='test')history else file.path(run,'later/baseline',ds)
  fc<-read.csv(file.path(folder,'test_forecasts.csv'))
  for(group in c('core','extensions')) {
    ids<-if(group=='core')c('raw_garch','dwt_garch','modwt_garch',plan$selected_modwt)else
      c(plan$selected_component,'ensemble_all','ensemble_modwt','mlp')
    titles<-if(group=='core')c('Raw GARCH','DWT-GARCH','Original MODWT-GARCH','Validation-selected MODWT')else
      c('Validation-selected component','Combined ensemble','MODWT ensemble','MLP (seed 101)')
    cols<-if(group=='core')colors[c('raw','dwt','modwt','ensemble')]else colors[c('component','ensemble','modwt','mlp')]
    data<-fc[fc$model_id %in% ids,]
    data$prediction[!.valid_forecasts(data)]<-NA_real_
    range_y<-c(0,max(data$actual,data$prediction,na.rm=TRUE)*1.05e4)
    name<-paste(ds,period,group,sep='_');device(name,2200,1500,18)
    par(mfrow=c(2,2),mar=c(3.1,4,2.4,.6),oma=c(0,0,2,0))
    bounds<-if(period=='test')as.Date(cfg$test)else as.Date(cfg$later)
    ticks<-as.Date(paste0(if(period=='test')2012:2014 else c(2015,2018,2021,2024),'-01-01'))
    for(i in 1:4) {
      z<-data[data$model_id==ids[i],];z<-z[order(z$target_date),]
      plot(as.Date(z$target_date),z$actual*1e4,type='l',col=colors['actual'],lwd=.7,ylim=range_y,
        xlim=bounds,xaxs='i',xaxt='n',xlab='',ylab='Target x 10^4',main=titles[i],cex.main=.95)
      axis.Date(1,at=ticks,format='%Y');lines(as.Date(z$target_date),z$prediction*1e4,col=cols[i],lwd=1.3)
      if(i==1)legend('topright',c('Observed target','One-step forecast'),col=c(colors['actual'],cols[i]),lty=1,bty='n',cex=.7)
    }
    mtext(paste(labels[ds],if(period=='test')'| 2012-2014'else'| 2015-2025'),outer=TRUE,side=3,cex=1.1)
    dev.off();write_table(data,file.path(out,paste0(name,'.csv')))
  }
}

# Initial training-only multiresolution example, with exact additive reconstruction.
p<-load_prices(root,'nigeria');series<-make_targets(p);y<-series$y[series$Date<as.Date('2010-01-01')&is.finite(series$y)]
y<-tail(y,256);parts<-decompose_prefix(y,'modwt','haar',2)
device('component_example',2000,1300,18);par(mfrow=c(4,1),mar=c(1.4,4,1.5,.6),oma=c(2,0,2,0))
for(name in c('Observed y',names(parts))) {
  z<-if(name=='Observed y')y else parts[[name]]
  plot(z*1e4,type='l',col=if(name=='Observed y')colors['actual']else colors['modwt'],xlab='',ylab='',main=name,lwd=1.1)
}
mtext('Nigeria: final 256 training targets | Haar MODWT, J=2',outer=TRUE,side=3,cex=1)
dev.off();write_table(data.frame(y=y,A2=parts$A2,D2=parts$D2,D1=parts$D1),file.path(out,'component_example.csv'))

# Wavelet/filter/depth effects, normalized within each dataset first.
rowkeys<-expand.grid(filter=cfg$filters,J=cfg$levels,stringsAsFactors=FALSE)
colkeys<-expand.grid(transform=c('dwt','modwt'),allocation=c('all_arima','mixed'),stringsAsFactors=FALSE)
wm<-matrix(NA_real_,nrow(rowkeys),nrow(colkeys));wsummary<-list()
for(i in seq_len(nrow(rowkeys)))for(j in seq_len(nrow(colkeys))) {
  z<-wave[wave$period=='test'&wave$filter==rowkeys$filter[i]&wave$J==rowkeys$J[i]&
    wave$transform==colkeys$transform[j]&wave$allocation==colkeys$allocation[j],]
  wm[i,j]<-geomean(z$RMSE_ratio)
  wsummary[[length(wsummary)+1L]]<-data.frame(rowkeys[i,],colkeys[j,],n_datasets=nrow(z),geomean_RMSE_ratio=wm[i,j])
}
heatmap_plot('wavelet_parameter_effects',wm,paste(rowkeys$filter,'J=',rowkeys$J),
  paste(toupper(colkeys$transform),ifelse(colkeys$allocation=='mixed','mixed','ARMA')),
  'Component RMSE / raw GARCH\nSix-series geometric mean',center=1,digits=3,lower_better=TRUE)
write_table(bind_rows_fill(wsummary),file.path(out,'wavelet_parameter_effects.csv'))

# Window and cadence: one change at a time; equal-dataset geometric mean ratios.
device('window_cadence_effects',2200,1050,18);par(mfrow=c(1,2),mar=c(4,4.8,3,.6),oma=c(2,0,0,0))
parameter_summary<-list()
for(axis_name in c('window','cadence')) {
  xx<-if(axis_name=='window')c(768,1024,1536)else c(20,40,60)
  scenarios<-if(axis_name=='window')c('window768','baseline','window1536')else c('baseline','cadence40','cadence60')
  yy<-matrix(1,length(xx),3)
  for(j in 1:3)for(i in seq_along(xx))if(scenarios[i]!='baseline') {
    z<-effects[effects$period=='test'&effects$model_id==c('raw_garch','dwt_garch','modwt_garch')[j]&effects$scenario==scenarios[i],]
    yy[i,j]<-geomean(z$RMSE_ratio)
    parameter_summary[[length(parameter_summary)+1L]]<-data.frame(axis=axis_name,value=xx[i],pipeline=c('raw_garch','dwt_garch','modwt_garch')[j],ratio=yy[i,j],n_datasets=nrow(z))
  }
  limits<-range(c(1,yy),na.rm=TRUE);pad<-max(.01,diff(limits)*.2)
  matplot(xx,yy,type='b',pch=1:3,lty=1,col=colors[c('raw','dwt','modwt')],ylim=limits+c(-pad,pad),
    xlab=if(axis_name=='window')'Maximum fitting-window observations'else'Refit every k observations',
    ylab='RMSE / default RMSE',main=if(axis_name=='window')'Window length'else'Refit cadence',xaxt='n')
  axis(1,at=xx);abline(h=1,lty=2,col='#777777')
  if(axis_name=='window')legend('top',c('Raw','DWT','MODWT'),col=colors[c('raw','dwt','modwt')],pch=1:3,lty=1,bty='n',cex=.75,horiz=TRUE)
}
mtext('Historical test; equal-dataset geometric mean of paired RMSE ratios. Default = window 1024, cadence 20.',outer=TRUE,side=1,line=.5,cex=.78)
dev.off();write_table(bind_rows_fill(parameter_summary),file.path(out,'window_cadence_effects.csv'))

simple_summary<-list()
for(scenario in c('criterionBIC','order_cap5'))for(model in c('raw_garch','dwt_garch','modwt_garch')) {
  z<-effects[effects$scenario==scenario&effects$model_id==model&effects$period=='test',]
  simple_summary[[length(simple_summary)+1L]]<-data.frame(scenario,model,n_datasets=nrow(z),RMSE_ratio=geomean(z$RMSE_ratio))
}
write_table(bind_rows_fill(simple_summary),file.path(out,'identification_effects.csv'))
lsummary<-list()
for(model in unique(likelihood$model_id)) {
  z<-likelihood[likelihood$model_id==model&likelihood$period=='test',]
  lsummary[[length(lsummary)+1L]]<-data.frame(model_id=model,control=z$control[1],n_datasets=nrow(z),RMSE_ratio=geomean(z$RMSE_ratio))
}
write_table(bind_rows_fill(lsummary),file.path(out,'likelihood_order_effects.csv'))

# Neural hyperparameters: show only complete three-seed validation architectures.
ngrid<-expand.grid(hidden=cfg$mlp_hidden,decay=cfg$mlp_decay);nsummary<-list()
nm<-matrix(NA_real_,length(cfg$dataset_ids),nrow(ngrid))
for(i in seq_len(nrow(ngrid))) {
  z<-neural[neural$hidden==ngrid$hidden[i]&neural$decay==ngrid$decay[i],]
  complete<-tapply(z$successful_model==z$requested,z$dataset,function(v)length(v)==3&&all(v))
  z<-z[z$dataset %in% names(complete)[complete],]
  for(j in seq_along(cfg$dataset_ids))if(cfg$dataset_ids[j] %in% z$dataset)
    nm[j,i]<-geomean(z$RMSE_ratio[z$dataset==cfg$dataset_ids[j]])
  nsummary[[i]]<-data.frame(ngrid[i,],n_datasets=length(unique(z$dataset)),ratio=if(nrow(z))geomean(z$RMSE_ratio)else NA_real_)
}
ns<-bind_rows_fill(nsummary);write_table(ns,file.path(out,'mlp_hyperparameters.csv'))
heatmap_plot('mlp_hyperparameters',nm,unname(labels[cfg$dataset_ids]),
  paste0('h',ngrid$hidden,' d',ngrid$decay),'MLP validation RMSE / raw GARCH',center=1,digits=3,lower_better=TRUE)
write_table(data.frame(dataset=rep(cfg$dataset_ids,nrow(ngrid)),hidden=rep(ngrid$hidden,each=6),
  decay=rep(ngrid$decay,each=6),RMSE_ratio=as.vector(nm)),file.path(out,'mlp_hyperparameters_by_series.csv'))

annual<-read.csv(file.path(tab,'annual_stock_effects.csv'))
device('annual_stock_trends',2200,1500,18);par(mfrow=c(3,2),mar=c(2.5,5.5,1.8,.6),oma=c(1,0,2,0),mgp=c(3.2,.7,0),cex.axis=.85)
stocks<-manifest$dataset[manifest$type=='stock'];a_slots<-c('selected_modwt','component','ensemble_all','mlp')
for(ds in stocks) {
  z<-annual[annual$dataset==ds&annual$slot %in% a_slots,]
  yy<-matrix(NA_real_,11,4)
  # Explicit assignment keeps row-order assumptions out of the plotted data.
  for(i in 1:11)for(j in 1:4){v<-z$improvement_pct[z$year==2014+i&z$slot==a_slots[j]];yy[i,j]<-if(length(v))v else NA_real_}
  matplot(2015:2025,yy[,1:3,drop=FALSE],type='l',lty=1:3,col=colors[c('modwt','component','ensemble')],
    xlab='',ylab='MSE reduction (%)',main=paste(labels[ds],'- statistical models'),cex.main=.9);abline(h=0,lty=2,col='#999999')
  if(ds==stocks[1])legend('bottomleft',c('Selected MODWT','Component','Combined ensemble'),col=colors[c('modwt','component','ensemble')],lty=1:3,bty='n',cex=.65)
  plot(2015:2025,yy[,4],type='l',lty=1,col=colors['mlp'],xlab='',ylab='MSE reduction (%)',
    main=paste(labels[ds],'- MLP'),cex.main=.9);abline(h=0,lty=2,col='#999999')
}
mtext('Annual later-period effects versus raw GARCH: separate panel scales',outer=TRUE,side=3,cex=.95)
dev.off()
file.copy(file.path(out,'core_comparison.png'),file.path(root,'results/core_comparison.png'),overwrite=TRUE)
cat('Figures: ',out,'\n')
