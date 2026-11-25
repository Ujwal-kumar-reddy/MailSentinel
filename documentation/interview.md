# Explaining MailSentinel in an interview

**What happens after clicking Analyze?** React validates the form and sends JSON to FastAPI. The API validates the text, combines the subject and body, then calls the same fitted pipeline used during evaluation. The classifier returns a spam probability. The API returns the label, probability, model name and rule matches. The browser holds results in component memory.

**Why a separate validation and test set?** Trying four classifiers and picking the best is itself a learning decision. Choosing with the test labels would bias the final score upward. A stratified split preserves the spam proportion in each partition. The release keeps the calibrated fit fixed while selecting its threshold, then evaluates all four candidates on held-out emails.

**What exactly does TF-IDF learn?** The vocabulary determines which unigrams and bigrams are columns. Inverse document frequency reduces the influence of terms that occur in many training messages. The pipeline fits both using training examples. Serving calls transform with this frozen vocabulary. New terms have no learned weight.

**Why compare these four models?** Multinomial Naive Bayes models class-dependent term frequencies under a conditional independence assumption. Logistic Regression learns a linear decision boundary with log-odds weights. Linear SVM maximizes the separation margin. Random Forest combines decision trees, offering a nonlinear comparison on sparse text.

**How does calibration work?** For each training example a model fitted on other folds produces a score. A sigmoid maps the collected out-of-fold scores to observed labels. The base estimator then learns from the whole fitting partition. The final model and calibration map are saved together. The Brier score measures average squared probability error. Calibration quality can shift as the mix of email changes.

**Why measure spam F1?** Precision asks what fraction of flagged messages really are spam. Recall asks what fraction of spam was caught. F1 is their harmonic mean. If a product automatically quarantines messages, false positives may carry greater cost. This release selects cutoffs using a fourfold penalty on the legitimate false-positive rate and measures the resulting trade-off on two held-out panels.

**Where could leakage or optimistic scores remain?** Ignoring transport headers and filenames removes easy label shortcuts. Normalized exact deduplication eliminates repeated content and conflicting labels. Related threads, paraphrased campaigns and sender-specific writing can still cross partitions. A later corpus evaluated chronologically or by campaign would give better evidence of real-world generalization.

**Why separate heuristic indicators?** Rules can flag a URL even in a legitimate meeting invite. A displayed match identifies a literal pattern. The trained model considers many term weights. The interface labels those outputs separately.

**What data is retained?** There is no database, inbox integration, analytics collector or request-body logging in the application. The API returns only the result fields. CSV exports contain record position and outcome so they can be joined locally. Hosting providers can retain ordinary request metadata under their own settings.
