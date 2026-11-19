import { blockedExample, configs, receipts, type ConfigRow } from "./results";

const REPO = "https://github.com/cherylaurelia/datacurve-demo";
const TRIAL_URL = "https://deepswe.datacurve.ai/data/v1.1/trials/";

const muse = configs.find((c) => c.config === "mini_swe_agent_muse_spark_1_2_xhigh");
const fullRuns = configs.filter((c) => c.full);
const sampled = configs.filter((c) => !c.full);
const sampledTrials = sampled.reduce((n, c) => n + c.checked, 0);
const sampledReached = sampled.reduce((n, c) => n + c.reached, 0);
const sampledWithBlocks = sampled.filter((c) => c.blocked > 0).length;
const sampledNoAttempts = sampled.filter((c) => c.attempted === 0).length;

function label(config: string): string {
  return config.replace("mini_swe_agent_", "").replaceAll("_", "-");
}

function Label({ children }: { children: React.ReactNode }) {
  return <p className="font-mono text-[11px] tracking-[0.08em] text-faint uppercase">{children}</p>;
}

function Outcome({ passed }: { passed: boolean }) {
  return passed ? (
    <span className="rounded-sm bg-pass/10 px-1.5 py-0.5 font-mono text-[11px] text-pass">PASS</span>
  ) : (
    <span className="rounded-sm bg-fail/10 px-1.5 py-0.5 font-mono text-[11px] text-fail">FAIL</span>
  );
}

function Row({ row }: { row: ConfigRow }) {
  const open = row.reached > 0;

  return (
    <tr className={`border-t border-line ${open ? "bg-fail/5" : ""}`}>
      <td className="py-2 pr-4 font-mono text-[13px]">{label(row.config)}</td>
      <td className="py-2 pr-4 text-right font-mono text-[13px]">{row.checked}</td>
      <td className="py-2 pr-4 text-right font-mono text-[13px]">{row.attempted}</td>
      <td className="py-2 pr-4 text-right font-mono text-[13px]">{row.blocked}</td>
      <td className={`py-2 text-right font-mono text-[13px] ${open ? "font-semibold text-fail" : ""}`}>
        {row.reached}
      </td>
    </tr>
  );
}

export default function Page() {
  if (!muse) {
    throw new Error("results.ts is missing the muse-spark-1-2 row");
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-line">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <span className="text-[15px] font-semibold tracking-tight">DeepSWE egress check</span>
          <span className="font-mono text-[11px] text-faint uppercase">unofficial · not by Datacurve</span>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6">
        <section className="py-14">
          <Label>DeepSWE v1.1 · published trajectories · checked 2026-11-18</Label>
          <h1 className="mt-4 max-w-3xl text-[34px] leading-[1.15] font-medium tracking-tight sm:text-[42px]">
            One leaderboard row ran with the network open.
          </h1>
          <p className="mt-5 max-w-2xl text-[17px] leading-relaxed text-ink-soft">
            In <b>muse-spark-1.2 [xhigh]</b>, agents reached GitHub and PyPI in {muse.reached} of {muse.checked}{" "}
            trials of tasks marked <code className="font-mono text-[15px]">network_mode = &quot;no-network&quot;</code>,
            and not one network attempt in that row was refused. No other row checked had a fetch get through.
          </p>
          <p className="mt-3 max-w-2xl text-[17px] leading-relaxed text-ink-soft">
            The fix is a check before a row goes live: a small stdlib script that reads Pier trajectories and flags any
            network attempt that got through.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <a href={REPO} className="bg-ink px-4 py-2.5 text-[14px] font-medium text-white hover:bg-ink-soft">
              Checker + data on GitHub →
            </a>
            <a href="#receipts" className="border border-line px-4 py-2.5 text-[14px] font-medium hover:bg-panel">
              See the receipts
            </a>
          </div>
          <dl className="mt-12 grid grid-cols-2 gap-y-4 border-y border-line py-6 font-mono text-[13px] sm:grid-cols-4">
            <div>
              <dt className="text-faint">trials reached net</dt>
              <dd className="mt-1 text-[22px] text-fail">
                {muse.reached}/{muse.checked}
              </dd>
            </div>
            <div>
              <dt className="text-faint">attempts blocked</dt>
              <dd className="mt-1 text-[22px]">0</dd>
            </div>
            <div>
              <dt className="text-faint">reached + passed</dt>
              <dd className="mt-1 text-[22px]">
                {muse.reachedPassed}/{muse.reached}
              </dd>
            </div>
            <div>
              <dt className="text-faint">other rows: reached</dt>
              <dd className="mt-1 text-[22px]">0</dd>
            </div>
          </dl>
        </section>

        <section id="receipts" className="border-t border-line py-12">
          <Label>Receipts · muse-spark-1.2 [xhigh]</Label>
          <h2 className="mt-3 text-[24px] font-medium tracking-tight">What came back</h2>
          <p className="mt-2 max-w-2xl text-[15px] text-muted">
            Six of the {muse.reached} trials, each with the exact command and the first lines of the response, copied
            from the published trajectory. All {113} tasks declare <code className="font-mono">[agent] network_mode =
            &quot;no-network&quot;</code> in their task.toml.
          </p>
          <div className="mt-8 space-y-6">
            {receipts.map((r) => (
              <article key={`${r.trial}-${r.step}`} className="border border-line">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-line bg-panel px-4 py-3">
                  <Outcome passed={r.passed} />
                  <span className="text-[14px] font-medium">{r.task}</span>
                  <a
                    href={`${TRIAL_URL}${r.trial}`}
                    className="font-mono text-[12px] text-muted underline decoration-line hover:text-ink"
                  >
                    {r.trial} · step {r.step} ↗
                  </a>
                </div>
                <p className="px-4 pt-3 text-[14px] text-ink-soft">{r.why}</p>
                <pre className="mx-4 mt-3 overflow-x-auto bg-ink px-3 py-2 font-mono text-[12px] leading-relaxed text-white">
                  $ {r.command}
                </pre>
                <pre className="mx-4 mt-2 mb-4 max-h-48 overflow-auto border border-line px-3 py-2 font-mono text-[12px] leading-relaxed text-ink-soft">
                  {r.response}
                </pre>
              </article>
            ))}
          </div>

          <div className="mt-10 border-l-2 border-pass pl-4">
            <Label>For contrast · {blockedExample.model}</Label>
            <p className="mt-2 text-[14px] text-ink-soft">
              The same kind of fetch in an air-gapped row, {blockedExample.task} step {blockedExample.step}:
            </p>
            <pre className="mt-2 overflow-x-auto bg-ink px-3 py-2 font-mono text-[12px] text-white">
              $ {blockedExample.command}
            </pre>
            <pre className="mt-2 overflow-x-auto border border-line px-3 py-2 font-mono text-[12px] text-ink-soft">
              {blockedExample.response}
            </pre>
          </div>
        </section>

        <section className="border-t border-line py-12">
          <Label>Every row checked</Label>
          <h2 className="mt-3 text-[24px] font-medium tracking-tight">Trials with a network attempt, by outcome</h2>
          <p className="mt-2 max-w-2xl text-[15px] text-muted">
            Every trial of the {fullRuns.length} rows run near the same dates or through the same provider. A trial can
            have both kinds; attempts whose output settles neither are counted in &quot;attempted&quot; only.
          </p>
          <div className="mt-6 overflow-x-auto">
            <table className="w-full min-w-[560px] border-b border-line">
              <thead>
                <tr className="text-left font-mono text-[11px] text-faint uppercase">
                  <th className="pb-2 font-normal">config</th>
                  <th className="pb-2 pr-4 text-right font-normal">trials</th>
                  <th className="pb-2 pr-4 text-right font-normal">attempted</th>
                  <th className="pb-2 pr-4 text-right font-normal">blocked</th>
                  <th className="pb-2 text-right font-normal">reached</th>
                </tr>
              </thead>
              <tbody>
                {fullRuns.map((row) => (
                  <Row key={row.config} row={row} />
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-6 max-w-2xl text-[15px] text-ink-soft">
            Plus 20 random trials (seed 0) from each of the other {sampled.length} rows: {sampledTrials} trials,{" "}
            {sampledReached} reached. In {sampledWithBlocks} of those rows the sample has blocked attempts, so the proxy
            was on; {sampledNoAttempts} rows had no network attempt in their 20 trials, so the sample says nothing about
            them. At muse-spark-1.2&apos;s rate (18 of 452, about 4%), 20 trials would miss a leak 44% of the time, so
            for those rows this is &quot;0 seen&quot;, not &quot;air-gapped&quot;.
          </p>
          <details className="mt-3">
            <summary className="cursor-pointer font-mono text-[12px] text-muted">Show the {sampled.length} sampled rows</summary>
            <div className="overflow-x-auto">
              <table className="mt-2 w-full min-w-[560px]">
                <thead>
                  <tr className="text-left font-mono text-[11px] text-faint uppercase">
                    <th className="pb-2 font-normal">config</th>
                    <th className="pb-2 pr-4 text-right font-normal">trials</th>
                    <th className="pb-2 pr-4 text-right font-normal">attempted</th>
                    <th className="pb-2 pr-4 text-right font-normal">blocked</th>
                    <th className="pb-2 text-right font-normal">reached</th>
                  </tr>
                </thead>
                <tbody>
                  {sampled.map((row) => (
                    <Row key={row.config} row={row} />
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </section>

        <section className="grid gap-10 border-t border-line py-12 sm:grid-cols-2">
          <div>
            <Label>What this doesn&apos;t show</Label>
            <ul className="mt-3 space-y-3 text-[14px] leading-relaxed text-ink-soft">
              <li>
                <b>No score claim.</b> {muse.reachedPassed} of the {muse.reached} trials that reached the network
                passed. The row&apos;s 54.9% is within the run-to-run interval of muse-spark-1.1 (53.3%, air-gapped).
                Most of what came back wasn&apos;t the answer.
              </li>
              <li>
                <b>Not why.</b> One thing worth checking: deep-swe#44 (Jul 22) moved tasks from{" "}
                <code className="font-mono">allow_internet = false</code> to Harbor&apos;s{" "}
                <code className="font-mono">network_mode</code>, and Pier read <code className="font-mono">network_mode</code>{" "}
                from 0946a47 (Aug 11). This row ran Aug 6–7. But gemini-3.7-flash ran Aug 6–9 and was blocked, so that
                timing alone doesn&apos;t explain it.
              </li>
              <li>
                <b>Only what the agent printed.</b> A fetch whose output was piped away or discarded can&apos;t be seen in
                a trajectory.
              </li>
            </ul>
          </div>
          <div>
            <Label>The check</Label>
            <p className="mt-3 text-[14px] leading-relaxed text-ink-soft">
              <code className="font-mono">egress_check.py</code> reads trajectories from trials.json or a local Pier job
              directory and labels each network attempt blocked, reached, or unclear, printing the step and the matched
              line for a human to confirm. It exits 1 when anything reached, so it can gate publishing a row.
            </p>
            <pre className="mt-3 overflow-x-auto bg-ink px-3 py-2 font-mono text-[12px] leading-relaxed text-white">
              {`python3 egress_check.py --job-dir jobs/<job>
python3 egress_check.py --trials trials.json \\
  --config mini_swe_agent_muse_spark_1_2_xhigh`}
            </pre>
            <p className="mt-3 text-[14px] leading-relaxed text-ink-soft">
              Stdlib only, 19 tests built from real steps, including the false positives found by hand: editable
              installs of the task repo, a wheel pulled out of pip&apos;s cache, httpx source that mentions{" "}
              <code className="font-mono">ProxyError</code>, test files written with heredocs.
            </p>
            <p className="mt-3 text-[14px] leading-relaxed text-ink-soft">
              It leans conservative: a blocked marker beats a reached one, so a GitHub API 403 (a rate limit, say)
              counts as blocked, and anything it can&apos;t settle is &quot;unclear&quot;, never &quot;reached&quot;.
              On the air-gapped muse-spark-1.1 row (452 trials, 19 with blocked attempts) it exits 0.
            </p>
          </div>
        </section>

        <section className="border-t border-line py-12">
          <Label>Why this was checkable at all</Label>
          <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-ink-soft">
            DeepSWE publishes every trajectory, verifier output and patch. Most leaderboards would make this impossible
            to see from the outside. Nothing here has been posted anywhere else.
          </p>
        </section>
      </main>

      <footer className="border-t border-line">
        <div className="mx-auto max-w-5xl px-6 py-6 font-mono text-[12px] text-faint">
          Unofficial demo by Cheryl Aurelia: not affiliated with Datacurve. Data: deepswe.datacurve.ai (v1.1
          trials.json and trajectories).
        </div>
      </footer>
    </div>
  );
}
