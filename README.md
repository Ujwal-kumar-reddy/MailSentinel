# MailSentinel — Intelligent Email Spam Detection System

MailSentinel classifies email subjects and bodies using a trained, sigmoid-calibrated Multinomial Naive Bayes model. The release includes the fitted TF-IDF vocabulary, preprocessing function, classifier, calibration mapping and evaluation report. The frontend submits requests to FastAPI and reads the dashboard from the same release used for inference.

## Run on Windows

Install 64-bit Python 3.13 and Node.js 22. Open the project folder in VS Code. Run these commands in a PowerShell terminal at the project root:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In a second terminal at the root:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

Open **http://localhost:5173**. The API schema and interactive test form are at **http://127.0.0.1:8000/docs**. Both terminals must keep running. The included model works immediately after dependency installation. Training is optional.

On macOS or Linux use `python3.13 -m venv .venv`, replace `.\.venv\Scripts\python.exe` with `./.venv/bin/python`, and use `npm` in place of `npm.cmd`. Default local origins work without configuration. For different origins, set `CORS_ORIGINS` in the API process environment and set `VITE_API_URL` in `frontend/.env.local` before starting or building Vite. The root `.env.example` lists both values.

## Use the application

- **Email analyzer** accepts a subject, a body, or both. Load either example or enter your own content and click **Analyze email**. Editing the message clears the previous result.
- **Batch analysis** accepts UTF-8 CSV with exactly `subject` and `body` headers, in either order. Quoted commas, double quotes and multiline bodies are supported. Import checks the file locally. Analyze sends the parsed records. Export produces `record,label,spam_probability` in input order.
- **Model performance** displays validation scores for all four candidates, confusion matrices, cleaned class counts and the winner’s separate held-out test results.
- **About the technology** explains feature extraction, calibration, warning indicators and limitations.

Predictions are probabilistic. A legitimate classification cannot guarantee the safety of an email. The system does not authenticate senders, inspect attachments or contact URLs.

## Architecture

| Directory | Responsibility |
| --- | --- |
| frontend/ | React and TypeScript, Vite, Tailwind CSS, Recharts, CSV parsing and export |
| backend/ | FastAPI startup loader, request limits, validation, inference and heuristic checks |
| ml/ | Corpus reader, shared preprocessing, stratified model selection and notebook |
| ml/artifacts/ | Trained Joblib bundle and readable metrics JSON |
| tests/ | API contract, input validation, batch consistency and release integration |
| documentation/ | Deployment guide and interview explanations |

The browser sends email text to the API only when analysis is requested. FastAPI loads one trusted local Joblib release per worker at startup. Single and batch requests use the same vectorized inference path. A separate rule pass flags literal patterns. No application database, email logging or browser persistence is configured. Results disappear when the page is closed. Do not replace the operator-controlled Joblib file with a user upload.

## Data and reproducibility

Source: [Apache SpamAssassin public email corpus](https://spamassassin.apache.org/old/publiccorpus/) and [corpus terms and history](https://spamassassin.apache.org/old/publiccorpus/readme.html). The maintainer makes the corpus available for spam-filter development and testing. Copyright in message text remains with the original senders. No blanket Apache software licence is stated for the messages. Raw email content is excluded from the project package.

Four archives use the 20030228 snapshot (easy_ham, easy_ham_2, hard_ham and spam). The fifth uses the corrected 20050311 spam_2 snapshot. The publisher’s historical overview says 6,047 messages. The selected files contain **6,046** matching email records. The March 2005 revision removed one incorrectly labelled message. The exact input archive names and SHA-256 hashes are in `ml/artifacts/metrics.json`.

| Stage | Legitimate | Spam | Total |
| --- | ---: | ---: | ---: |
| Parsed | 4,150 | 1,896 | 6,046 |
| After cleaning | 4,107 | 1,786 | 5,893 |

The fitted release uses Multinomial Naive Bayes and a validation-selected spam cutoff of 0.45. The archived test set contains 884 emails. A separate, authored challenge contains 32 short messages. The reported meeting and cash-prize messages are regression cases outside those benchmarks.

See [the classifier investigation](documentation/classifier-evaluation.md) for before-and-after results for every candidate, leakage and calibration findings, the split protocol and remaining false positives. Detailed machine-readable measurements are in `ml/artifacts/metrics.json` and `ml/artifacts/baseline.json`.

### Rebuild the release or open the notebook

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m ml.train
.\.venv\Scripts\python.exe -m pip install jupyterlab
.\.venv\Scripts\python.exe -m jupyterlab ml/MailSentinel.ipynb
```

Training downloads missing archives to `ml/data/`. For offline training, put the five original compressed archives there first. The command writes `ml/artifacts/release.joblib` and `metrics.json`. Restart the API after retraining. The notebook audits missing fields, duplicates, class distribution and text lengths, then displays each model’s results. Set its retraining flag to rerun the experiment.

## API

| Method and route | Input | Output |
| --- | --- | --- |
| POST /predict | JSON object with subject and/or body | Label, spam probability, model name and heuristic indicators |
| POST /predict-batch | Object with an emails array of 1–100 records | Ordered results array |
| GET /metrics | None | Data audit, split counts, validation and test metrics |
| GET /models | None | Candidate names and the selected model |
| GET /health | None | Ready status and loaded model name |

The subject limit is 500 characters and the body limit is 50,000. Requests above 2,000,000 bytes return HTTP 413. Invalid schema, blank messages or out-of-range batches return HTTP 422. Validation errors omit submitted email content.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/predict -Method Post -ContentType 'application/json' -Body '{"subject":"Meeting notes","body":"Please review the attached agenda before Thursday."}'
```

## Tests and build

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm.cmd ci
npm.cmd test
npm.cmd run build
npm.cmd run preview -- --port 5173
```

The production output is `frontend/dist/`. The CI workflow checks the trained release, API tests, CSV tests and frontend build. A missing artifact fails the release check in CI.

## Deployment and interview preparation

Follow [the Vercel and Render deployment guide](documentation/deployment.md). The configuration is ready for an account owner to connect the repository. See [technical interview explanations](documentation/interview.md) for leakage, sparse features, model selection, calibration and false-positive trade-offs.

### Resume bullets

- Built MailSentinel, a React and FastAPI email classification application supporting single-message predictions, CSV batch inference and an interactive model evaluation dashboard.
- Compared four calibrated text classifiers on historical and short-email benchmarks, investigating false positives and tuning deployment thresholds on separate validation data.
