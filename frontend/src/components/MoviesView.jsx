import { useEffect, useState } from "react";
import { createMovie, getMovies, updateMovie } from "../api";

const inputClass =
  "rounded-lg border border-zinc-700 bg-zinc-800 p-2 text-zinc-100 placeholder-zinc-500 focus:border-emerald-500 focus:outline-none";

export default function MoviesView() {
  const [movies, setMovies] = useState([]);
  const [error, setError] = useState("");
  const [title, setTitle] = useState("");
  const [year, setYear] = useState("");
  const [runtime, setRuntime] = useState("");
  const [editingId, setEditingId] = useState(null);   // movie whose prerequisites are being edited
  const [selectedIds, setSelectedIds] = useState([]); // checked prerequisites in the editor

  async function loadMovies() {
    setMovies(await getMovies());
  }

  useEffect(() => {
    loadMovies();
  }, []);

  async function addMovie(event) {
    event.preventDefault();
    setError("");

    try {
      await createMovie({
        title: title,
        release_year: Number(year),
        runtime: Number(runtime),
      });
    } catch (err) {
      setError(err.message);
      return;
    }

    setTitle("");
    setYear("");
    setRuntime("");
    loadMovies();
  }

  async function toggleWatched(movie) {
    setError("");
    try {
      await updateMovie(movie.id, { watched: !movie.watched });
    } catch (err) {
      setError(err.message);
      return;
    }
    loadMovies();
  }

  function startEditing(movie) {
    setError("");
    setEditingId(movie.id);
    setSelectedIds(movie.prerequisites);
  }

  function toggleSelected(id) {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter((selected) => selected !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  }

  async function savePrerequisites() {
    setError("");
    try {
      await updateMovie(editingId, { prerequisites: selectedIds });
    } catch (err) {
      setError(err.message);   // for example the circular dependency message
      return;
    }
    setEditingId(null);
    loadMovies();
  }

  // Look up a movie's title from its id
  const titleById = {};
  movies.forEach((movie) => {
    titleById[movie.id] = movie.title;
  });

  return (
    <div>
      <section className="mb-6 rounded-xl border border-zinc-800 bg-zinc-900 p-5">
        <h2 className="mb-3 text-lg font-semibold">Add a movie</h2>
        <form onSubmit={addMovie} className="flex flex-wrap gap-3">
          <input
            className={`${inputClass} min-w-52 flex-1`}
            placeholder="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
          <input
            className={`${inputClass} w-28`}
            type="number"
            placeholder="Year"
            min="2000"
            max="2050"
            value={year}
            onChange={(e) => setYear(e.target.value)}
            required
          />
          <input
            className={`${inputClass} w-32`}
            type="number"
            placeholder="Minutes"
            min="1"
            max="300"
            value={runtime}
            onChange={(e) => setRuntime(e.target.value)}
            required
          />
          <button className="rounded-lg bg-emerald-600 px-5 py-2 font-semibold text-white hover:bg-emerald-500">
            Add movie
          </button>
        </form>
      </section>

      {error && (
        <p className="mb-4 rounded-lg border border-red-800 bg-red-950 p-3 text-red-300">
          {error}
        </p>
      )}

      <h2 className="mb-3 text-lg font-semibold">
        Movies <span className="text-zinc-500">({movies.length})</span>
      </h2>

      <div className="grid gap-3">
        {movies.map((movie) => (
          <article
            key={movie.id}
            className="rounded-xl border border-zinc-800 bg-zinc-900 p-4"
          >
            <div className="flex flex-wrap items-center gap-3">
              <input
                className="h-4 w-4 accent-emerald-500"
                type="checkbox"
                checked={movie.watched}
                onChange={() => toggleWatched(movie)}
              />
              <h3 className="font-semibold">{movie.title}</h3>
              <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-xs text-zinc-300">
                {movie.release_year}
              </span>
              <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-xs text-zinc-300">
                {movie.runtime} min
              </span>
              {movie.watched && (
                <span className="rounded-full bg-emerald-900 px-2 py-0.5 text-xs text-emerald-300">
                  Watched
                </span>
              )}
              <button
                onClick={() => startEditing(movie)}
                className="ml-auto text-sm text-emerald-400 hover:underline"
              >
                Edit prerequisites
              </button>
            </div>

            <p className="mt-2 text-sm text-zinc-400">
              Watch first:{" "}
              {movie.prerequisites.length === 0
                ? "none"
                : movie.prerequisites.map((id) => titleById[id]).join(", ")}
            </p>

            {editingId === movie.id && (
              <div className="mt-3 rounded-lg border border-zinc-700 bg-zinc-800 p-4">
                <div className="grid gap-1 sm:grid-cols-2">
                  {movies
                    .filter((other) => other.id !== movie.id)
                    .map((other) => (
                      <label key={other.id} className="flex items-center gap-2 text-sm">
                        <input
                          className="accent-emerald-500"
                          type="checkbox"
                          checked={selectedIds.includes(other.id)}
                          onChange={() => toggleSelected(other.id)}
                        />
                        {other.title}
                      </label>
                    ))}
                </div>
                <div className="mt-4 flex gap-2">
                  <button
                    onClick={savePrerequisites}
                    className="rounded-lg bg-emerald-600 px-4 py-1.5 font-semibold text-white hover:bg-emerald-500"
                  >
                    Save
                  </button>
                  <button
                    onClick={() => setEditingId(null)}
                    className="rounded-lg border border-zinc-600 px-4 py-1.5 hover:bg-zinc-700"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}