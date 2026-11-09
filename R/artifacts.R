# Small, dependency-free helpers for readable, reproducible artifacts.
ensure_dir <- function(path) { dir.create(path, recursive=TRUE, showWarnings=FALSE); invisible(path) }
write_table <- function(x, path) {
  ensure_dir(dirname(path)); utils::write.csv(x,path,row.names=FALSE,na="")
  invisible(path)
}
bind_rows_fill <- function(xs) {
  xs <- Filter(function(x) is.data.frame(x) && nrow(x)>0L,xs)
  if (!length(xs)) return(data.frame())
  columns <- unique(unlist(lapply(xs,names)))
  xs <- lapply(xs,function(x) { for(n in setdiff(columns,names(x))) x[[n]] <- NA; x[,columns,drop=FALSE] })
  do.call(rbind,xs)
}
safe_message <- function(..., log_file=NULL) {
  line <- paste(format(Sys.time(),"%H:%M:%S"),paste(...,collapse=" "))
  message(line)
  if(!is.null(log_file)) cat(line,"\n",file=log_file,append=TRUE)
}
# MD5 of file content with every CR byte removed, so a checkout that converts
# line endings (git autocrlf, Unix re-zip) yields the same hash (audit m1).
normalized_md5 <- function(files) {
  vapply(files, function(f) {
    bytes <- readBin(f, "raw", n = file.size(f))
    tmp <- tempfile(); on.exit(unlink(tmp), add = TRUE)
    writeBin(bytes[bytes != as.raw(13L)], tmp)
    unname(tools::md5sum(tmp))
  }, character(1), USE.NAMES = FALSE)
}
# Paths relative to root, with forward slashes; never absolute (audit M2/M3).
relative_path <- function(files, root) {
  f <- normalizePath(files, winslash = "/", mustWork = TRUE)
  r <- normalizePath(root, winslash = "/", mustWork = TRUE)
  stopifnot(all(startsWith(f, paste0(r, "/"))))
  substring(f, nchar(r) + 2L)
}
config_fingerprint <- function(cfg, files, root) {
  # Hash scientific configuration plus code/data content keyed by root-relative
  # path. The run id is therefore identical wherever the folder is copied, however
  # the script is invoked, and after CRLF/LF conversion (audit M2, m1, m4).
  cfg$rebuild <- NULL; cfg$workers <- NULL; cfg$deadline <- NULL
  cfg$historical_only <- NULL; cfg$baseline_only <- NULL
  files <- files[file.exists(files)]
  rel <- relative_path(files, root); o <- order(rel)
  checksum <- setNames(normalized_md5(files[o]), rel[o])
  tmp <- tempfile(fileext=".rds"); on.exit(unlink(tmp),add=TRUE)
  saveRDS(list(cfg=cfg,files=checksum),tmp,version=2)
  substr(unname(tools::md5sum(tmp)),1,12)
}
write_run_metadata <- function(cfg, directory, manifest=NULL) {
  ensure_dir(directory); saveRDS(cfg,file.path(directory,"config.rds"))
  capture.output(dput(cfg),file=file.path(directory,"config.txt"))
  capture.output(sessionInfo(),file=file.path(directory,"sessionInfo.txt"))
  if(!is.null(manifest)) write_table(manifest,file.path(directory,"manifest.csv"))
}
