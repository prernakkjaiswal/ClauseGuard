from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from engine.rules import analyze_contract

app = FastAPI(title="ClauseGuard Offline Risk Engine", version="1.1.0")


class ContractRequest(BaseModel):
    contract_text: str = Field(..., min_length=5)


SAMPLE_CONTRACTS: Dict[str, Dict[str, str]] = {
    "predatory_loan": {
        "name": "High-Risk Digital Personal Loan",
        "text": (
            "1. Loan Facility: The Borrower agrees to repay INR 1,50,000 over 12 monthly installments.\n"
            "2. Interest & Charges: The Lender reserves the right to increase interest rate at any time without prior notice based on internal risk assessments.\n"
            "3. Repayment Mandate: The Borrower grants irrevocable authorization to debit from any bank account held by the Borrower for overdue amounts.\n"
            "4. Early Closure: Any early settlement shall attract a foreclosure penalty of 5% on the principal outstanding.\n"
            "5. Privacy & Recovery: The Company may share borrower data with third parties and recovery agents in the event of delayed payment.\n"
            "6. Cross-Default: A default under any other agreement shall constitute an immediate event of default under this facility.\n"
            "7. Dispute Resolution: All disputes shall be referred to a sole arbitrator appointed by the Lender."
        )
    },
    "fair_loan": {
        "name": "Balanced RBI-Compliant Term Loan",
        "text": (
            "1. Loan Facility: The Borrower is sanctioned INR 1,50,000 at a floating interest rate linked to the RBI Repo Rate.\n"
            "2. Rate Revisions: Any upward or downward revision in benchmark rates shall be communicated to the Borrower with 30 days prior written notice.\n"
            "3. Auto-Debit: EMI deductions shall occur strictly via NACH from the Borrower's designated primary bank account, revocable upon settlement.\n"
            "4. Prepayment: Zero prepayment or foreclosure charges shall apply on floating-rate individual loans.\n"
            "5. Data Protection: Borrower information shall only be shared with authorized credit bureaus (CIBIL) and statutory regulators.\n"
            "6. Dispute Resolution: Disputes shall be resolved through mutually agreed mediation or courts within the Borrower's city of residence."
        )
    }
}

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ClauseGuard — Offline Contract Risk Auditor</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #020617; color: #f1f5f9; font-family: system-ui, -apple-system, sans-serif; line-height: 1.5; }
    header { background: #0f172a; border-bottom: 1px solid #1e293b; padding: 14px 24px; display: flex; justify-content: space-between; align-items: center; }
    .brand { display: flex; align-items: center; gap: 12px; }
    .logo { width: 38px; height: 38px; border-radius: 8px; background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.4); color: #34d399; font-weight: 800; display: flex; align-items: center; justify-content: center; }
    .badge-live { font-size: 12px; padding: 5px 12px; border-radius: 999px; background: rgba(16,185,129,0.12); color: #34d399; border: 1px solid rgba(16,185,129,0.3); font-weight: 600; }
    main { max-width: 1260px; margin: 28px auto; padding: 0 20px; display: grid; grid-template-columns: 5fr 7fr; gap: 24px; }
    @media (max-width: 900px) { main { grid-template-columns: 1fr; } }
    .card { background: #0f172a; border: 1px solid #1e293b; border-radius: 12px; padding: 20px; }
    .toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; gap: 8px; flex-wrap: wrap; }
    .toolbar h2 { font-size: 13px; text-transform: uppercase; letter-spacing: 0.06em; color: #94a3b8; }
    button { cursor: pointer; font-family: inherit; border-radius: 8px; font-weight: 600; transition: 0.15s; }
    .btn-sample-risk { font-size: 12px; padding: 6px 10px; background: rgba(244,63,94,0.15); color: #fda4af; border: 1px solid rgba(244,63,94,0.35); }
    .btn-sample-risk:hover { background: rgba(244,63,94,0.28); }
    .btn-sample-fair { font-size: 12px; padding: 6px 10px; background: rgba(16,185,129,0.15); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.35); }
    .btn-sample-fair:hover { background: rgba(16,185,129,0.28); }
    textarea { width: 100%; height: 340px; background: #020617; color: #e2e8f0; border: 1px solid #334155; border-radius: 8px; padding: 14px; font-size: 14px; line-height: 1.6; resize: vertical; }
    textarea:focus { outline: none; border-color: #10b981; }
    .actions { display: flex; gap: 10px; margin-top: 14px; }
    .btn-clear { padding: 11px 16px; background: #1e293b; color: #cbd5e1; border: none; }
    .btn-clear:hover { background: #334155; }
    .btn-audit { flex: 1; padding: 11px 18px; background: #10b981; color: #020617; border: none; font-size: 14px; font-weight: 700; }
    .btn-audit:hover { background: #34d399; }
    .empty { border: 1px dashed #334155; border-radius: 12px; padding: 60px 24px; text-align: center; color: #94a3b8; }
    .score-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }
    .score-num { font-size: 42px; font-weight: 800; color: #fff; }
    .pill { padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 800; margin-left: 8px; }
    .pill-CRITICAL { background: rgba(244,63,94,0.2); color: #fda4af; border: 1px solid rgba(244,63,94,0.45); }
    .pill-MODERATE { background: rgba(245,158,11,0.2); color: #fcd34d; border: 1px solid rgba(245,158,11,0.45); }
    .pill-LOW { background: rgba(16,185,129,0.2); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.45); }
    .stats { display: flex; gap: 24px; text-align: right; }
    .stat-label { font-size: 12px; color: #94a3b8; }
    .stat-val { font-size: 22px; font-weight: 700; }
    .bar-bg { width: 100%; height: 10px; background: #020617; border-radius: 999px; margin-top: 16px; overflow: hidden; border: 1px solid #1e293b; }
    .bar-fill { height: 100%; width: 0%; transition: width 0.4s ease; }
    .finding { background: #0f172a; border: 1px solid #1e293b; border-radius: 12px; padding: 18px; margin-top: 14px; }
    .finding-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
    .sev-HIGH { background: rgba(244,63,94,0.16); color: #fda4af; border: 1px solid rgba(244,63,94,0.35); padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; }
    .sev-MEDIUM { background: rgba(245,158,11,0.16); color: #fcd34d; border: 1px solid rgba(245,158,11,0.35); padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; }
    .quote { background: #020617; border: 1px solid #1e293b; border-radius: 8px; padding: 12px; margin: 12px 0; font-family: monospace; font-size: 13px; color: #cbd5e1; }
    mark { background: rgba(244,63,94,0.32); color: #fecdd3; padding: 1px 4px; border-radius: 4px; font-weight: 700; }
    .advice-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 13px; }
    @media (max-width: 650px) { .advice-grid { grid-template-columns: 1fr; } }
    .box-warn { background: rgba(244,63,94,0.06); border: 1px solid rgba(244,63,94,0.2); border-radius: 8px; padding: 12px; }
    .box-fix { background: rgba(16,185,129,0.06); border: 1px solid rgba(16,185,129,0.2); border-radius: 8px; padding: 12px; }
    .clean-msg { background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.35); color: #6ee7b7; padding: 16px; border-radius: 10px; margin-top: 14px; font-size: 14px; }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="logo">CG</div>
      <div>
        <div style="font-weight:700;font-size:17px;">ClauseGuard</div>
        <div style="font-size:12px;color:#94a3b8;">Offline Deterministic Contract Risk Engine</div>
      </div>
    </div>
    <span class="badge-live">● Offline Engine Active</span>
  </header>

  <main>
    <div class="card">
      <div class="toolbar">
        <h2>Contract Text</h2>
        <div style="display:flex;gap:6px;">
          <button type="button" class="btn-sample-risk" id="btnRisk">Load Risky Sample</button>
          <button type="button" class="btn-sample-fair" id="btnFair">Load Fair Sample</button>
        </div>
      </div>
      <textarea id="contractInput" placeholder="Paste loan agreement or contract clauses here..."></textarea>
      <div class="actions">
        <button type="button" class="btn-clear" id="btnClear">Clear</button>
        <button type="button" class="btn-audit" id="btnAudit">Audit Contract Clauses</button>
      </div>
    </div>

    <div>
      <div id="emptyState" class="empty">
        <h3 style="color:#e2e8f0;margin-bottom:6px;">Ready to Audit</h3>
        <p style="font-size:14px;">Click <strong>Load Risky Sample</strong> on the left or paste any agreement and hit <strong>Audit Contract Clauses</strong>.</p>
      </div>

      <div id="resultsBox" style="display:none;">
        <div class="card">
          <div class="score-header">
            <div>
              <div style="font-size:12px;text-transform:uppercase;color:#94a3b8;font-weight:700;">Overall Risk Score</div>
              <div style="display:flex;align-items:center;">
                <span class="score-num" id="scoreVal">0</span>
                <span style="color:#94a3b8;margin-left:4px;">/ 100</span>
                <span class="pill pill-LOW" id="levelBadge">LOW</span>
              </div>
            </div>
            <div class="stats">
              <div>
                <div class="stat-label">Clauses Scanned</div>
                <div class="stat-val" id="scannedVal">0</div>
              </div>
              <div>
                <div class="stat-label">Hidden Flags</div>
                <div class="stat-val" style="color:#fb7185;" id="flagsVal">0</div>
              </div>
            </div>
          </div>
          <div class="bar-bg"><div class="bar-fill" id="barFill"></div></div>
        </div>

        <div id="cleanBanner" class="clean-msg" style="display:none;">
          <strong>No Predatory Clauses Found:</strong> All scanned paragraphs passed ClauseGuard's deterministic risk checks.
        </div>

        <div id="findingsList"></div>
      </div>
    </div>
  </main>

  <script>
    const inputEl = document.getElementById('contractInput');
    const emptyEl = document.getElementById('emptyState');
    const resultsEl = document.getElementById('resultsBox');

    function escapeHtml(s) {
      return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    function highlight(fullText, phrase) {
      const safeFull = escapeHtml(fullText);
      const safePhrase = escapeHtml(phrase);
      const idx = safeFull.toLowerCase().indexOf(safePhrase.toLowerCase());
      if (!safePhrase || idx === -1) return safeFull;
      return safeFull.slice(0, idx) + '<mark>' + safeFull.slice(idx, idx + safePhrase.length) + '</mark>' + safeFull.slice(idx + safePhrase.length);
    }

    async function loadSample(key) {
      try {
        const res = await fetch('/api/samples');
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        inputEl.value = data.samples[key].text;
        await runAudit();
      } catch (err) {
        alert('Error loading sample: ' + err.message + '. Make sure you opened http://127.0.0.1:8000 in your browser.');
      }
    }

    async function runAudit() {
      const text = inputEl.value.trim();
      if (text.length < 5) {
        alert('Please paste at least 5 characters of contract text.');
        return;
      }
      const btn = document.getElementById('btnAudit');
      btn.disabled = true;
      btn.textContent = 'Analyzing...';

      try {
        const res = await fetch('/api/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ contract_text: text })
        });
        if (!res.ok) {
          const errText = await res.text();
          throw new Error('Server error (' + res.status + '): ' + errText);
        }
        const data = await res.json();
        renderResults(data);
      } catch (err) {
        alert('Audit failed: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.textContent = 'Audit Contract Clauses';
      }
    }

    function renderResults(data) {
      emptyEl.style.display = 'none';
      resultsEl.style.display = 'block';

      document.getElementById('scoreVal').textContent = data.risk_score;
      document.getElementById('scannedVal').textContent = data.total_clauses_scanned;
      document.getElementById('flagsVal').textContent = data.flags_count;

      const badge = document.getElementById('levelBadge');
      badge.textContent = data.risk_level;
      badge.className = 'pill pill-' + data.risk_level;

      const bar = document.getElementById('barFill');
      bar.style.width = data.risk_score + '%';
      bar.style.background = data.risk_level === 'CRITICAL' ? '#f43f5e' : (data.risk_level === 'MODERATE' ? '#f59e0b' : '#10b981');

      const cleanBanner = document.getElementById('cleanBanner');
      const list = document.getElementById('findingsList');
      list.innerHTML = '';

      if (data.findings.length === 0) {
        cleanBanner.style.display = 'block';
        return;
      }
      cleanBanner.style.display = 'none';

      data.findings.forEach(item => {
        const div = document.createElement('div');
        div.className = 'finding';
        div.innerHTML = `
          <div class="finding-top">
            <div>
              <div style="font-size:12px;color:#94a3b8;font-family:monospace;">Clause #${item.clause_number} • ${escapeHtml(item.rule_id)}</div>
              <div style="font-size:16px;font-weight:700;color:#fff;margin-top:2px;">${escapeHtml(item.title)}</div>
            </div>
            <span class="sev-${item.severity}">${item.severity} (+${item.weight})</span>
          </div>
          <div class="quote">"${highlight(item.clause_text, item.matched_phrase)}"</div>
          <div class="advice-grid">
            <div class="box-warn">
              <div style="font-weight:700;color:#fda4af;margin-bottom:4px;">Why This Matters</div>
              <div style="color:#cbd5e1;">${escapeHtml(item.explanation)}</div>
            </div>
            <div class="box-fix">
              <div style="font-weight:700;color:#6ee7b7;margin-bottom:4px;">Counter-Proposal</div>
              <div style="color:#cbd5e1;">${escapeHtml(item.recommendation)}</div>
            </div>
          </div>
        `;
        list.appendChild(div);
      });
    }

    document.getElementById('btnRisk').addEventListener('click', () => loadSample('predatory_loan'));
    document.getElementById('btnFair').addEventListener('click', () => loadSample('fair_loan'));
    document.getElementById('btnAudit').addEventListener('click', runAudit);
    document.getElementById('btnClear').addEventListener('click', () => {
      inputEl.value = '';
      resultsEl.style.display = 'none';
      emptyEl.style.display = 'block';
    });
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def serve_ui():
    return HTML_PAGE


@app.get("/api/samples")
def get_sample_contracts() -> Dict[str, Any]:
    return {"samples": SAMPLE_CONTRACTS}


@app.post("/api/analyze")
def analyze_endpoint(payload: ContractRequest) -> Dict[str, Any]:
    cleaned_text = payload.contract_text.strip()
    if not cleaned_text:
        raise HTTPException(status_code=400, detail="Contract text cannot be empty.")
    return analyze_contract(cleaned_text)