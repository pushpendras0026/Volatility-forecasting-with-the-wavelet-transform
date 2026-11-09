# Write FILE_SHA256SUMS.csv for every file in this folder (base R; replaces the
# former Python package.py). Run last, after all results and reports exist.
# Optional: --zip <path> also writes a ZIP of the folder (needs a 'zip' program on
# PATH, or PowerShell's Compress-Archive on Windows).
script<-sub('^--file=','',grep('^--file=',commandArgs(),value=TRUE)[1]);root<-dirname(dirname(normalizePath(script,winslash='/')))
run<-file.path(root,'results',basename(trimws(readLines(file.path(root,'results/LATEST.txt'))[1])))
stopifnot(file.exists(file.path(run,'VERIFIED.txt')))
files<-list.files(root,recursive=TRUE,all.files=TRUE,full.names=TRUE,no..=TRUE)
rel<-substring(normalizePath(files,winslash='/'),nchar(normalizePath(root,winslash='/'))+2L)
keep<-rel!='FILE_SHA256SUMS.csv'&!grepl('(^|/)(__pycache__|\\.Rhistory)(/|$)',rel)
files<-files[keep];rel<-rel[keep];o<-order(rel)
sums<-data.frame(file=rel[o],bytes=file.size(files[o]),sha256=unname(tools::sha256sum(files[o])))
write.csv(sums,file.path(root,'FILE_SHA256SUMS.csv'),row.names=FALSE)
cat('FILE_SHA256SUMS.csv:',nrow(sums),'files,',sprintf('%.1f MiB',sum(sums$bytes)/2^20),'\n')
args<-commandArgs(trailingOnly=TRUE)
if(length(args)==2&&args[1]=='--zip') {
  dest<-normalizePath(args[2],winslash='/',mustWork=FALSE)
  if(nzchar(Sys.which('zip'))){owd<-setwd(dirname(root));on.exit(setwd(owd))
    utils::zip(dest,basename(root),flags='-r9Xq')}else
    system2('powershell',c('-NoProfile','-Command',shQuote(sprintf("Compress-Archive -Path '%s' -DestinationPath '%s' -Force",root,dest))))
  stopifnot(file.exists(dest));cat('ZIP:',dest,'\n')
}
