/* Compare docs/gp.js against the scikit-learn reference.
 *   node docs/tools/check_gp.js
 * Exits non-zero if the page's math has drifted from the program's. */
const fs = require("fs"), path = require("path"), vm = require("vm");

const here = __dirname;
const ctx = { console };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(here, "..", "gp.js"), "utf8"), ctx);

const ref = JSON.parse(fs.readFileSync(path.join(here, "gp_fixture.json"), "utf8"));
const model = ctx.GP.fit(ref.xs, ref.ys, { ell: ref.ell, noise: ref.noise });

let maxMean = 0, maxStd = 0;
ref.grid.forEach((x, i) => {
  const p = model.predict(x);
  maxMean = Math.max(maxMean, Math.abs(p.mean - ref.mean[i]));
  maxStd = Math.max(maxStd, Math.abs(p.std - ref.std[i]));
});

const TOL = 1e-6;
console.log(`max |Δmean| = ${maxMean.toExponential(2)}   max |Δstd| = ${maxStd.toExponential(2)}   (tol ${TOL})`);
if (maxMean > TOL || maxStd > TOL) {
  console.error("FAIL — the page's GP no longer matches scikit-learn");
  process.exit(1);
}
console.log("OK — the page's GP matches scikit-learn");
