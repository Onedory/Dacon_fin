const $ = (id) => document.getElementById(id);

document.querySelectorAll(".sample").forEach(b =>
  b.addEventListener("click", () => { $("query").value = b.textContent; }));

$("submit").addEventListener("click", analyze);

async function analyze() {
  const query = $("query").value.trim();
  if (!query) return alert("질문을 입력하세요.");
  $("status").classList.remove("hidden");
  $("result").classList.add("hidden");
  $("submit").disabled = true;
  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, domain: "auto" }),
    });
    if (!res.ok) throw new Error((await res.json()).detail || res.status);
    render(await res.json());
  } catch (e) {
    alert("오류: " + e.message);
  } finally {
    $("status").classList.add("hidden");
    $("submit").disabled = false;
  }
}

function render(r) {
  $("domain").textContent = r.domain;
  $("latency").textContent = (r.latency_ms / 1000).toFixed(1) + "s";
  setBadge($("risk"), r.safety.risk_level, { none: "safe", low: "low", mid: "mid", high: "high" });
  setBadge($("action"), r.safety.action, { pass: "safe", warn: "mid", mask: "mid", rewrite: "high", block: "high" });
  $("raw").textContent = r.raw_response || "(차단됨 — LLM 미호출)";
  $("final").textContent = r.final_response;

  $("rules").innerHTML = r.safety.violated_rules.length
    ? r.safety.violated_rules.map(v =>
        `<li><code>${v.rule_id}</code> [${v.severity}] ${v.description}</li>`).join("")
    : "<li class='muted'>위반 없음</li>";

  $("evidence").innerHTML = r.evidence.length
    ? r.evidence.map(e =>
        `<div class="doc"><b>${e.title}</b> <span class="muted">(${e.doc_id}, score ${e.score})</span>
         <p>${e.snippet}...</p>
         <small>출처: ${e.metadata.source || "-"} ${e.metadata.url ? `· <a href="${e.metadata.url}" target="_blank">${e.metadata.url}</a>` : ""}</small></div>`).join("")
    : "<p class='muted'>검색된 문서 없음</p>";

  $("result").classList.remove("hidden");
}

function setBadge(el, text, map) {
  el.textContent = text;
  el.className = "badge " + (map[text] || "");
}
