''' R template function '''

def train_r():
    ''' Default train module template '''

    res = """#!/usr/bin/env Rscript
library(jsonlite)
library(ModelMetrics)
library(braveml)

args = commandArgs(trailingOnly=TRUE)
experiment <- fromJSON(args[1])

method <- experiment$method
predictors <- experiment$x
response <- experiment$y
options <- experiment$options
output <- experiment$results
seed <- experiment$seed

data <- read.csv(experiment$data, header = TRUE, check.names = FALSE)

# Any data transformations need to go here
##

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

# Training Procedure
set.seed(seed)
  
## Train-Validate-Test splits
trainIndex <- train_test_split(data[, response], p = 0.75, stratified = TRUE, seed = seed)

x_train <- data[trainIndex, predictors]
x_test <- data[-trainIndex, predictors]
y_train <- data[trainIndex, response]
y_test <- data[-trainIndex, response]
  
estimator <- model(X = x_train, Y = y_train, method = method)

Rand_Res <- RandomizedSearchCV(estimator, param_distributions = experiment$options,
                        scoring = auc,
                        init_points = 100,
                        n_iter = 5,
                        cv = 10,
                        seed = seed)
  
best_par <- Rand_Res$Best_Par[[which.max(Rand_Res$Best_Score)]]
xgb <- model(X = x_train, Y = y_train, method = method)
do.call(xgb$fit, best_par)
yh <- xgb$predict(x_test)
lbl <- factor(colnames(yh)[apply(yh, 1, which.max)], levels = levels(y_train))


result <- list()
result$ewd <- experiment["ewd"]
result$parameters <- best_par
result$performance <- performance(y_test, lbl)
  
resultsdir <- dir.create(file.path(experiment["ewd"], output), showWarnings = FALSE)
fname <- file.path(experiment["ewd"], output, paste0(make.names(Sys.time()), "_model.rds"))
xgb$save_model(fname)
  
json <- toJSON(result, auto_unbox = TRUE, pretty = TRUE)
write(json, file.path(experiment["ewd"], output, paste0(make.names(Sys.time()), "_results.json")))
}"""

    return res
