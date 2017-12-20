''' R template function '''

def train_r():
    ''' Default train module template '''

    res = """#!/usr/bin/env Rscript
library(jsonlite)
library(braveml)

args = commandArgs(trailingOnly=TRUE)
experiment <- fromJSON(args[1])

method <- experiment$method
predictors <- experiment$x
response <- experiment$y
seed <- experiment$seed
metric <- experiment$RandomSearchCV$optimise
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
scoring <- function(actual, predicted){
  perf <- performance(actual, predicted)
  perf[[metric]]
}

# Training Procedure
for (iteration in 1:length(seed)){
  cat("Training iteration", iteration, "of", length(seed), "
")

  set.seed(seed[iteration])
  
  ## Train-Validate-Test splits
  train_fraction <- experiment$train
  
  trainIndex <- sample(1:nrow(data), round(train_fraction * nrow(data)),
                       replace = FALSE)

  x_train <- data[trainIndex, predictors]
  x_test <- data[-trainIndex, predictors]
  y_train <- data[trainIndex, response]
  y_test <- data[-trainIndex, response]
  
  estimator <- model(X = x_train, Y = y_train, method = method)

  s <- RandomizedSearchCV(estimator, param_distributions = experiment$options,
                          scoring = scoring,
                          n_iter = experiment$RandomSearchCV$n_iter,
                          cv = experiment$RandomSearchCV$cv,
                          seed = seed[iteration])
  
  ifelse(as.logical(experiment$RandomSearchCV$maximise),
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

    return res
