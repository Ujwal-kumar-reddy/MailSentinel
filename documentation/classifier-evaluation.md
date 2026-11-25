# MailSentinel classifier investigation

## Reproduction and diagnosis

The original release returns 0.75942589 spam probability for the supplied meeting. Its class order is [0, 1], with 1 meaning spam. The corpus parser and both prediction routes combine subject and body in the same order and the fitted vectorizer normalizes the combined text. The UI displays the API's probability. The old SVM's raw margin was only +0.0924. The fitted sigmoid converted it to the displayed probability. The largest positive word contributions included 'your' (+0.163), 'our' (+0.120) and 'please' (+0.115).

Transport headers, attachment parts, filenames and folder labels were already excluded from features. Source-specific text still appeared inside bodies. Quoted lines occurred in 2,176/4,107 legitimate vs 57/1,786 spam messages. Reply or footer markers appeared in 2,537 vs 372. Embedded routing fields appeared in 45 vs 20. The strongest SVM features favoring legitimate mail included 're', '2002', 'wrote', 'date' and 'razor'. These observations point to domain mismatch and shortcuts. They do not establish a single causal feature.

## Training and selection

The original five SpamAssassin archives contained 5,893 distinct normalized emails, 30.3% spam. Both releases use the same stratified archive test (616 legitimate and 268 spam). The original selected SVM was evaluated directly from its shipped artifact. The other original candidates were reconstructed using the same original development split, hyperparameters and three-fold training procedure as the shipped winner. Their original validation-only fits had fewer training examples. Run `python -m ml.compare_baseline` to recreate the baseline comparison.

The new pipeline removes quoted lines, recognized routing fields and common reply/signature boundaries, and limits features to the first 160 normalized words. Its training pool includes 30 independently authored legitimate and 10 spam examples covering workplace and personal messages. A separate authored validation panel has eight of each class. A second deduplication pass reserves exact cleaned feature strings for the archive test, short-message validation and challenge before admitting training rows. Thread- or campaign-level near-duplicates may remain. Counts in metrics.json distinguish the archive inventory from the actual fit and validation partitions.

All four candidates use three-fold out-of-fold sigmoid calibration with fold-local TF-IDF. Class balance is stratified in the archive. Probability estimation uses the natural fit mix, without oversampling. For each candidate the trainer searches cutoffs 0.05 to 0.95 in 0.05 steps, minimizing the average of (4 × legitimate false-positive rate + spam miss rate) across archive and short-message validation. The 4:1 weighting and equal panel weights are engineering choices. Ties prefer the cutoff closest to 0.5. The model with the lowest validation cost wins, with archive validation F1 breaking ties. The calibrated fit is frozen through threshold selection and deployment.

| Candidate | Selected cutoff | Validation cost | Train F1 | Archive validation F1 | Short validation FP / FN |
| --- | ---: | ---: | ---: | ---: | ---: |
| Multinomial Naive Bayes | 0.45 | 0.0361 | 98.62% | 96.74% | 0 / 0 |
| Logistic Regression | 0.55 | 0.1530 | 99.68% | 97.73% | 0 / 2 |
| Linear SVM | 0.50 | 0.1544 | 99.96% | 97.74% | 0 / 2 |
| Random Forest | 0.35 | 0.2369 | 99.96% | 96.44% | 0 / 3 |

## Same-message before → after comparisons

### Historical archive, 884 emails

| Model | False positives | Missed spam | Spam precision | Spam recall | Spam F1 | Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Multinomial Naive Bayes | 6 → 9 | 13 → 16 | 97.70% → 96.55% | 95.15% → 94.03% | 96.41% → 95.27% | 0.0171 → 0.0237 |
| Logistic Regression | 5 → 11 | 12 → 15 | 98.08% → 95.83% | 95.52% → 94.40% | 96.79% → 95.11% | 0.0133 → 0.0202 |
| Linear SVM | 3 → 8 | 8 → 12 | 98.86% → 96.97% | 97.01% → 95.52% | 97.93% → 96.24% | 0.0106 → 0.0164 |
| Random Forest | 5 → 14 | 14 → 16 | 98.07% → 94.74% | 94.78% → 94.03% | 96.39% → 94.38% | 0.0171 → 0.0240 |

### Short-email challenge, 32 emails

These manually authored cases include refunds, account security, work and school, an appointment, credential theft, gift cards, delivery fraud and unsolicited advertising. This panel was fixed before retraining. Neither screenshot example is in it. With only 16 legitimate emails, each false alarm moves the false-positive rate by 6.25 percentage points.

| Model | False positives | Missed spam | Spam precision | Spam recall | Spam F1 | Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Multinomial Naive Bayes | 4 → 3 | 0 → 0 | 80.00% → 84.21% | 100.00% → 100.00% | 88.89% → 91.43% | 0.1153 → 0.0894 |
| Logistic Regression | 5 → 4 | 0 → 0 | 76.19% → 80.00% | 100.00% → 100.00% | 86.49% → 88.89% | 0.1394 → 0.1043 |
| Linear SVM | 4 → 2 | 0 → 1 | 80.00% → 88.24% | 100.00% → 93.75% | 88.89% → 90.91% | 0.1264 → 0.0689 |
| Random Forest | 2 → 1 | 6 → 7 | 83.33% → 90.00% | 62.50% → 56.25% | 71.43% → 69.23% | 0.1556 → 0.1948 |

## Release decision and limits

The release selects Multinomial Naive Bayes at 0.45. The short panel's remaining false positives were: Replacement debit card, Refund issued, Receipt for annual membership. The old deployed SVM made four false alarms there. Both releases detected all 16 spam cases. On the historical archive, false alarms rose from 3 to 9 and misses from 8 to 16. Calibration also varied by domain: deployed-model Brier error improved from 0.1264 to 0.0894 on the short challenge and worsened from 0.0106 to 0.0237 on the archive. Brier measures overall probability error, including both discrimination and calibration.

The new winner scored 98.62% training F1 versus 95.27% archive test F1. The training advantage and the larger short-message error show why training scores cannot describe inbox performance. Historical archives plus a small authored supplement still leave contemporary correspondence, languages, and inbox-specific spam prevalence underrepresented. A contemporaneous, consented mailbox evaluation split by thread and time would be needed to quantify those effects. No large contemporary inbox corpus was available for this release.

## Screenshot regressions

Scores below are native calibrated spam probabilities for the supplied meeting and prize emails. The API compares each probability with the model's selected cutoff. Literal warning indicators are separate.

| Model | Meeting, old | Meeting, new | Prize, new |
| --- | ---: | ---: | ---: |
| Multinomial Naive Bayes | 28.35% | 9.71% | 99.38% |
| Logistic Regression | 86.70% | 72.35% | 99.94% |
| Linear SVM | 75.94% | 54.34% | 99.93% |
| Random Forest | 78.93% | 29.72% | 98.70% |
