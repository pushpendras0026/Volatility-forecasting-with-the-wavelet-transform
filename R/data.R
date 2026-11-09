# Runtime needs only the six prepared, audited CSVs. No downloads or discovery.
load_prices <- function(root,id) {
  manifest<-read.csv(file.path(root,'data/manifest.csv'),stringsAsFactors=FALSE)
  row<-manifest[manifest$dataset==id,];stopifnot(nrow(row)==1)
  file<-file.path(root,'data',row$file)
  # Content hash with CR bytes removed, so line-ending conversion is harmless (audit m1).
  if (normalized_md5(file) != row$content_md5_lf)
    stop('Data checksum mismatch for ', row$file, ': the prepared CSV content differs from data/manifest.csv')
  p<-read.csv(file,stringsAsFactors=FALSE);p$Date<-as.Date(p$Date)
  stopifnot(all(c('Date','Price') %in% names(p)),!anyNA(p),!anyDuplicated(p$Date),
    all(diff(p$Date)>0),all(is.finite(p$Price)),all(p$Price>0))
  p
}
make_targets <- function(prices,mean_window=20L) {
  r<-diff(log(prices$Price));n<-length(r);mu<-y<-rep(NA_real_,n)
  for(i in seq.int(mean_window+1L,n)) {mu[i]<-mean(r[(i-mean_window):(i-1L)]);y[i]<-(r[i]-mu[i])^2}
  data.frame(Date=prices$Date[-1],r=r,moving_mean_for_target=mu,y=y)
}
calendar_split <- function(series,cfg) {
  series<-series[series$Date>=as.Date(cfg$training[1])&series$Date<=as.Date(cfg$later[2]),]
  idx<-function(bounds) which(series$Date>=as.Date(bounds[1])&series$Date<=as.Date(bounds[2])&is.finite(series$y))
  train<-which(series$Date<=as.Date(cfg$training[2]));val<-idx(cfg$validation);test<-idx(cfg$test);later<-idx(cfg$later)
  stopifnot(length(train)>150,length(val)>60,length(test)>252,max(train)<min(val),max(val)<min(test))
  if(length(later))stopifnot(max(test)<min(later))
  list(series=series,train_end_index=max(train),validation_indices=val,test_indices=test,later_indices=later,
    dates=data.frame(train_start=min(series$Date[train]),train_end=max(series$Date[train]),
      validation_start=min(series$Date[val]),validation_end=max(series$Date[val]),
      test_start=min(series$Date[test]),test_end=max(series$Date[test]),n_train=length(train),
      n_validation=length(val),n_test=length(test),n_later=length(later)))
}
