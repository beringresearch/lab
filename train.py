def train_r():
    res="""#!/usr/bin/env Rscript
library(jsonlite)
library(braveml)
library(RandomParameterSearch)

args = commandArgs(trailingOnly=TRUE)
experiment <- fromJSON(args[1])

method <- experiment$method
predictors <- experiment$x
response <- experiment$y
seed <- experiment$seed
metric <- experiment$search$optimise
options <- experiment$options
output <- experiment$results

data <- read.csv(experiment$data, header = TRUE, check.names = FALSE)

performance <- function(actual, predicted){
	cm = as.matrix(table(Actual = actual, Predicted = predicted))
	n = sum(cm) # number of instances
	nc = nrow(cm) # number of classes
	diag = diag(cm) # number of correctly classified instances per class 
	rowsums = apply(cm, 1, sum) # number of instances per class
	colsums = apply(cm, 2, sum) # number of predictions per class
	p = rowsums / n # distribution of instances over the actual classes
	q = colsums / n # distribution of instances over the predicted classes
	
	accuracy = sum(diag) / n
	precision = diag / colsums 
	recall = diag / rowsums

  recall[is.na(recall)] <- 0
  precision[is.na(precision)] <- 0
	
  f1 = 2 * precision * recall / (precision + recall)
  f1[is.na(f1)] <- 0
	
	macroPrecision = mean(precision)
	macroRecall = mean(recall)
	macroF1 = mean(f1)
	
	list(accuracy = accuracy, precision = precision, recall = recall, f1 = f1,
		macroPrecision = macroPrecision, macroRecall = macroRecall, macroF1 = macroF1)
}

# Prameter Optimisation Function
func <- function(...){
  m <- model(X = x_train, Y = y_train, method = method)
  m$fit(...)
  
  yh <- m$predict(x_validate)
  lbl <- factor(colnames(yh)[apply(yh, 1, which.max)], levels = levels(y_validate))  
  
  perf <- performance(y_validate, lbl)
  perf[[metric]]
}

# Training Procedure
for (iteration in 1:length(seed)){
  cat("Training iteration", iteration, "of", length(seed), "
")

  set.seed(seed[iteration])
  
  ## Train-Validate-Test splits
  train_fraction <- experiment$train
  validation_fraction <- experiment$validate
  testing_fraction <- experiment$test

  spec <- c(train = train_fraction,
            test = testing_fraction,
            validate = validation_fraction)
  g <- sample(cut(seq(nrow(data)),
              nrow(data)*cumsum(c(0, spec)),
              labels = names(spec)))
  res <- split(data, g)

  x_train <- res$train[, predictors]
  y_train <- res$train[, response]
  x_validate <- res$validate[, predictors]
  y_validate <- res$validate[, response]
  x_test <- res$test[, predictors]
  y_test <- res$test[, response]

  ## Random HyperparameterSearch
  grid <- create_random_grid(nrounds = experiment$search$rounds,
                             params = experiment$options, seed = seed[iteration])

  s <- random_search(grid, func)
  
  ifelse(as.logical(experiment$search$maximise),
         p <- s[which.max(s$.output),],
         p <- s[which.min(s$.output),]
  )
  
  p <- p[, !names(p) %in% ".output"]

  m <- model(X = x_train, Y = y_train, method = method)
  do.call(m$fit, as.list(p))
  yh <- m$predict(x_test)
  lbl <- colnames(yh)[apply(yh, 1, which.max)] 
  lbl <- factor(lbl, levels = levels(y_train))

  result <- list()
  result$ewd <- experiment["ewd"]
  result$parameters <- p
  result$performance <- performance(y_test, lbl)
  
  resultsdir <- dir.create(file.path(experiment["ewd"], output), showWarnings = FALSE)
  fname <- file.path(experiment["ewd"], output, paste0(seed[iteration], "_model.rds"))
  m$save_model(fname)
  
  json <- toJSON(result, auto_unbox = TRUE, pretty = TRUE)
  write(json, file.path(experiment["ewd"], output, paste0(seed[iteration], "_results.json")))
  }"""
    return(res)