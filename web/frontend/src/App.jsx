import { useEffect, useMemo, useState } from "react";
import "./index.css";

const API = "http://127.0.0.1:8000";

const fmt = (value, digits = 3) =>
  typeof value === "number" && Number.isFinite(value)
    ? value.toFixed(digits)
    : "—";

const pct = (value, digits = 2) =>
  typeof value === "number" && Number.isFinite(value)
    ? `${(value * 100).toFixed(digits)}%`
    : "—";

function Metric({ label, value, detail }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value ?? "—"}</strong>
      {detail && <small>{detail}</small>}
    </div>
  );
}

function Scatter({ points }) {
  const normalized = useMemo(() => {
    if (!points?.length) return [];

    const xs = points.map((p) => p.x);
    const ys = points.map((p) => p.y);

    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);

    return points.map((p) => ({
      x: 8 + ((p.x - minX) / (maxX - minX || 1)) * 84,
      y: 8 + ((p.y - minY) / (maxY - minY || 1)) * 84,
    }));
  }, [points]);

  return (
    <div className="scatter">
      <div className="gridlines" />

      {normalized.map((p, i) => (
        <i
          key={i}
          style={{
            left: `${p.x}%`,
            bottom: `${p.y}%`,
            opacity: 0.35 + (i % 6) * 0.1,
          }}
        />
      ))}

      <span className="axis y">Latent Dimension 2</span>
      <span className="axis x">Latent Dimension 1</span>
    </div>
  );
}

function MolecularPage({ title, subtitle, endpoint, render }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setData(null);
    setError("");

    fetch(`${API}${endpoint}`)
      .then(async (r) => {
        const d = await r.json();

        if (!r.ok) {
          throw new Error(d?.detail?.message || "Request failed");
        }

        setData(d);
      })
      .catch((e) => setError(e.message));
  }, [endpoint]);

  return (
    <section className="page">
      <p className="eyebrow">PHASE 4 • MOLECULAR VISUALIZATION</p>

      <h1>{title}</h1>

      <p className="lead">{subtitle}</p>

      {error ? (
        <div className="notice">
          Backend data unavailable: {error}
        </div>
      ) : !data ? (
        <div className="notice">
          Loading live backend result…
        </div>
      ) : (
        render(data)
      )}
    </section>
  );
}

function App() {
  const [view, setView] = useState("home");
  const [online, setOnline] = useState(false);
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [preview, setPreview] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API}/health`)
      .then((r) => setOnline(r.ok))
      .catch(() => setOnline(false));
  }, []);

  const analyze = async () => {
    if (!file) return;

    setLoading(true);
    setError("");
    setResult(null);
    setPreview([]);

    try {
      const fd = new FormData();
      fd.append("file", file);

      const r = await fetch(`${API}/analyze`, {
        method: "POST",
        body: fd,
      });

      const d = await r.json();

      if (!r.ok) {
        throw new Error(d?.detail?.message || "Analysis failed");
      }

      console.log("PRINOVA ANALYSIS RESPONSE:", d);

      setResult(d);
      setView("results");

      if (d.latent?.id) {
        try {
          const pr = await fetch(
            `${API}/latent/${d.latent.id}/preview`
          );

          const pd = await pr.json();

          console.log("LATENT PREVIEW RESPONSE:", pd);

          if (pr.ok) {
            setPreview(pd.points || []);
          }
        } catch (previewError) {
          console.error(
            "Could not load latent preview:",
            previewError
          );
        }
      }
    } catch (e) {
      console.error("Analysis error:", e);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const a = result?.analysis;
  const input = result?.input;

  const nav = (key, label) => (
    <button
      className={view === key ? "active" : ""}
      onClick={() => setView(key)}
    >
      {label}
    </button>
  );

  return (
    <div className="app">
      <header className="topbar">
        <button
          className="brand"
          onClick={() => setView("home")}
        >
          PRINOVA
        </button>

        <nav>
          {nav("home", "Home")}
          {nav("results", "Results")}
          {nav("pca", "PCA")}
          {nav("latent", "Latent Space")}
          {nav("clustering", "Clustering")}
          {nav("robustness", "Robustness")}
          {nav("biology", "Biology")}
        </nav>

        <span className={`status ${online ? "on" : ""}`}>
          {online ? "Backend online" : "Backend offline"}
        </span>
      </header>

      {view === "home" && (
        <main className="page hero-page">
          <p className="eyebrow">
            PROTEIN REPRESENTATION • LATENT STRUCTURE ANALYSIS
          </p>

          <h1>
            Discover the structure
            <br />
            hidden in your data.
          </h1>

          <p className="lead">
            Upload a CSV or NPY embedding matrix. PRINOVA generates
            a PCA-based latent representation and evaluates
            reconstruction, information retention and compression.
          </p>

          <div className="upload-card">
            <input
              type="file"
              accept=".csv,.npy"
              onChange={(e) =>
                setFile(e.target.files?.[0] || null)
              }
            />

            {file && (
              <p className="selected">
                {file.name}
              </p>
            )}

            <button
              className="primary"
              disabled={!file || !online || loading}
              onClick={analyze}
            >
              {loading
                ? "Running PRINOVA…"
                : "Run analysis →"}
            </button>

            {error && (
              <div className="notice error">
                {error}
              </div>
            )}
          </div>
        </main>
      )}

      {view === "results" && (
        <main className="page">
          {!result ? (
            <div className="notice">
              Run an analysis first.
            </div>
          ) : (
            <>
              <p className="eyebrow">
                PRINOVA • ANALYSIS RESULTS
              </p>

              <h1>Latent structure discovered.</h1>

              <p className="lead">
                Live metrics returned by the PRINOVA backend for the
                uploaded dataset.
              </p>

              <div className="metrics">
                <Metric
                  label="SAMPLES"
                  value={input?.samples?.toLocaleString()}
                  detail="Input observations"
                />

                <Metric
                  label="INPUT DIMENSIONS"
                  value={input?.dimensions}
                  detail="Original feature dimensions"
                />

                <Metric
                  label="LATENT DIMENSIONS"
                  value={a?.dimension}
                  detail="PCA representation"
                />

                <Metric
                  label="PRINOVA SCORE"
                  value={fmt(a?.prinova_score)}
                  detail="Composite representation score"
                />
              </div>

              <div className="metrics">
                <Metric
                  label="RECONSTRUCTION ERROR"
                  value={fmt(a?.mse, 4)}
                  detail="Lower is better"
                />

                <Metric
                  label="VARIANCE EXPLAINED"
                  value={pct(a?.variance_explained)}
                  detail="Information retained"
                />

                <Metric
                  label="R² SCORE"
                  value={pct(a?.r2)}
                  detail="Reconstruction quality"
                />

                <Metric
                  label="COMPRESSION"
                  value={pct(a?.compression_score)}
                  detail="Dimensional reduction"
                />
              </div>

              <div className="card">
                <p className="eyebrow">
                  LIVE REPRESENTATION
                </p>

                <h2>
                  {a?.representation || "PCA"}-{a?.dimension}
                </h2>

                <p>
                  {result.latent?.samples} ×{" "}
                  {result.latent?.dimensions} latent matrix • ID:{" "}
                  {result.latent?.id}
                </p>
              </div>
            </>
          )}
        </main>
      )}

      {view === "pca" && (
        <main className="page">
          {!result ? (
            <div className="notice">
              Run an analysis first.
            </div>
          ) : (
            <>
              <p className="eyebrow">
                PHASE 4 • MOLECULAR VISUALIZATION
              </p>

              <h1>
                Principal component analysis.
              </h1>

              <p className="lead">
                A live 2-D view derived from the first two coordinates
                of the stored PCA latent representation.
              </p>

              <div className="metrics">
                <Metric
                  label="LATENT DIMENSIONS"
                  value={a?.dimension}
                />

                <Metric
                  label="SAMPLES"
                  value={input?.samples}
                />

                <Metric
                  label="VARIANCE EXPLAINED"
                  value={pct(a?.variance_explained)}
                />

                <Metric
                  label="R²"
                  value={pct(a?.r2)}
                />
              </div>

              <div className="card">
                <h2>Live PCA representation</h2>

                {preview.length ? (
                  <Scatter points={preview} />
                ) : (
                  <div className="notice">
                    Loading representation preview…
                  </div>
                )}
              </div>
            </>
          )}
        </main>
      )}

      {view === "latent" && (
        <main className="page">
          {!result ? (
            <div className="notice">
              Run an analysis first.
            </div>
          ) : (
            <>
              <p className="eyebrow">
                PHASE 4 • MOLECULAR VISUALIZATION
              </p>

              <h1>Latent space.</h1>

              <p className="lead">
                Explore sample relationships in the representation
                generated by PRINOVA.
              </p>

              <div className="metrics">
                <Metric
                  label="LATENT DIMENSIONS"
                  value={a?.dimension}
                />

                <Metric
                  label="SAMPLES"
                  value={input?.samples}
                />

                <Metric
                  label="COMPRESSION"
                  value={pct(a?.compression_score)}
                />

                <Metric
                  label="PRINOVA SCORE"
                  value={fmt(a?.prinova_score)}
                />
              </div>

              <div className="card">
                <h2>Sample distribution</h2>

                {preview.length ? (
                  <Scatter points={preview} />
                ) : (
                  <div className="notice">
                    No preview available.
                  </div>
                )}
              </div>
            </>
          )}
        </main>
      )}

      {view === "clustering" && (
        <MolecularPage
          title="Clustering analysis."
          subtitle="Compare clustering configurations calculated from the molecular analysis results."
          endpoint="/molecular/clustering"
          render={(d) => (
            <div className="card">
              <div className="metrics">
                <Metric
                  label="BEST DIMENSION"
                  value={d.best_configuration?.dimension}
                />

                <Metric
                  label="CLUSTERS"
                  value={d.best_configuration?.clusters}
                />

                <Metric
                  label="METHOD"
                  value={d.best_configuration?.method}
                />

                <Metric
                  label="SILHOUETTE"
                  value={fmt(
                    d.best_configuration?.silhouette,
                    3
                  )}
                />
              </div>

              <h2>Configuration comparison</h2>

              <div className="table">
                {d.configurations
                  ?.slice(0, 15)
                  .map((x, i) => (
                    <div key={i}>
                      <b>{x.dimension}D</b>
                      <span>{x.method}</span>
                      <span>{x.clusters} clusters</span>
                      <strong>
                        {fmt(x.silhouette, 3)}
                      </strong>
                    </div>
                  ))}
              </div>
            </div>
          )}
        />
      )}

      {view === "robustness" && (
        <MolecularPage
          title="Robustness."
          subtitle="Evaluate how consistently PCA representations behave across multiple random seeds."
          endpoint="/molecular/robustness"
          render={(d) => (
            <div className="card">
              <div className="metrics">
                <Metric
                  label="SEEDS"
                  value={d.seed_count}
                />

                <Metric
                  label="DIMENSIONS TESTED"
                  value={d.dimension_count}
                />

                <Metric
                  label="RESULTS"
                  value={d.result_count}
                />
              </div>

              <div className="table">
                {d.stability?.map((x, i) => (
                  <div key={i}>
                    <b>{x.dimension}D</b>
                    <span>MSE range</span>
                    <span>{fmt(x.mse_range, 6)}</span>
                    <strong>
                      Stable across {x.seeds} seeds
                    </strong>
                  </div>
                ))}
              </div>
            </div>
          )}
        />
      )}

      {view === "biology" && (
        <MolecularPage
          title="Biological validation."
          subtitle="Inspect biological annotations and functional structure returned by the molecular validation endpoint."
          endpoint="/molecular/biological-validation"
          render={(d) => (
            <div className="card">
              <div className="metrics">
                <Metric
                  label="CLUSTERS"
                  value={d.cluster_count}
                />

                <Metric
                  label="ANNOTATED PROTEINS"
                  value={d.annotated_protein_count}
                />
              </div>

              <h2>Cluster summary</h2>

              <div className="table">
                {d.cluster_summary
                  ?.slice(0, 12)
                  .map((x, i) => (
                    <div key={i}>
                      <b>Cluster {x.cluster}</b>
                      <span>
                        {x.protein_count} proteins
                      </span>
                      <span>
                        {x.proteins_with_go} with GO
                      </span>
                    </div>
                  ))}
              </div>

              <h2>Protein annotations</h2>

              <div className="table">
                {d.protein_annotations
                  ?.slice(0, 20)
                  .map((x, i) => (
                    <div key={i}>
                      <b>{x.protein_id}</b>
                      <span>{x.protein_name}</span>
                      <span>{x.organism}</span>
                    </div>
                  ))}
              </div>
            </div>
          )}
        />
      )}
    </div>
  );
}

export default App;