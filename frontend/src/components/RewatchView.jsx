import { useEffect, useState } from "react";
import { getMovies, getRewatchOrder, updateMovie } from "../api";

// 307 minutes becomes "5h 7m"
function formatTime(minutes) {
  return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
}

export default function RewatchView() {
  const [movies, setMovies] = useState([]);
  const [targetId, setTargetId] = useState("");
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getMovies().then(setMovies);
  }, []);

  async function loadPlan(id) {
    setError("");
    try {
      setPlan(await getRewatchOrder(id));
    } catch (err) {
      setError(err.message);
    }
  }

  function chooseTarget(event) {
    const id = event.target.value;
    setTargetId(id);
    if (id === "") {
      setPlan(null);
    } else {
      loadPlan(id);
    }
  }

  async function toggleWatched(movie) {
    setError("");
    try {
      await updateMovie(movie.id, { watched: !movie.watched });
    } catch (err) {
      setError(err.message);
      return;
    }
    loadPlan(targetId);
  }

  let percent = 0;
  if (plan && plan.total_count > 0) {
    percent = Math.round((plan.watched_count / plan.total_count) * 100);
  }

  return (
    <div>
      <section className="mb-6 rounded-xl border border-zinc-800 bg-zinc-900 p-5">
        <label className="block">
          <span className="mb-2 block text-lg font-semibold">I want to watch</span>
          <select
            className="w-full rounded-lg border border-zinc-700 bg-zinc-800 p-2 text-zinc-100 focus:border-emerald-500 focus:outline-none"
            value={targetId}
            onChange={chooseTarget}
          >
            <option value="">Pick a movie...</option>
            {movies.map((movie) => (
              <option key={movie.id} value={movie.id}>
                {movie.title}
              </option>
            ))}
          </select>
        </label>
      </section>

      {error && (
        <p className="mb-4 rounded-lg border border-red-800 bg-red-950 p-3 text-red-300">
          {error}
        </p>
      )}

      {plan && (
        <div>
          <h2 className="mb-3 text-xl font-semibold">
            Before <span className="text-emerald-400">{plan.target.title}</span>
          </h2>

          {plan.total_count === 0 ? (
            <p className="rounded-xl border border-zinc-800 bg-zinc-900 p-5 text-zinc-400">
              Nothing to watch first.
            </p>
          ) : (
            <div>
              <section className="mb-4 rounded-xl border border-zinc-800 bg-zinc-900 p-5">
                <div className="mb-4 grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-zinc-400">Watched</p>
                    <p className="text-2xl font-bold">
                      {plan.watched_count} of {plan.total_count}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-zinc-400">Remaining watch time</p>
                    <p className="text-2xl font-bold">
                      {plan.remaining_runtime_minutes === 0
                        ? "All caught up!"
                        : formatTime(plan.remaining_runtime_minutes)}
                    </p>
                  </div>
                </div>

                <div className="h-3 w-full rounded-full bg-zinc-800">
                  <div
                    className="h-3 rounded-full bg-emerald-500"
                    style={{ width: `${percent}%` }}
                  ></div>
                </div>
              </section>

              <ol className="grid gap-2">
                {plan.order.map((movie, index) => (
                  <li
                    key={movie.id}
                    className="flex items-center gap-3 rounded-xl border border-zinc-800 bg-zinc-900 p-3"
                  >
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-zinc-800 text-xs text-zinc-300">
                      {index + 1}
                    </span>
                    <input
                      className="h-4 w-4 accent-emerald-500"
                      type="checkbox"
                      checked={movie.watched}
                      onChange={() => toggleWatched(movie)}
                    />
                    <span className={movie.watched ? "text-zinc-500 line-through" : ""}>
                      {movie.title}
                    </span>
                    <span className="ml-auto text-sm text-zinc-500">
                      {movie.runtime} min
                    </span>
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}
    </div>
  );
}