import { useEffect, useState } from "react";
import { getBooking, getCinemas } from "../api";

const inputClass =
  "rounded-lg border border-zinc-700 bg-zinc-800 p-2 text-zinc-100 placeholder-zinc-500 focus:border-emerald-500 focus:outline-none";

export default function BookingView() {
  const [cinemas, setCinemas] = useState([]);
  const [cinemaId, setCinemaId] = useState("");
  const [groupSize, setGroupSize] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getCinemas().then(setCinemas);
  }, []);

  function chooseCinema(event) {
    setCinemaId(event.target.value);
    setResult(null);
    setError("");
  }

  function changeGroupSize(event) {
    setGroupSize(event.target.value);
    setResult(null);
    setError("");
  }

  async function getQuote(event) {
    event.preventDefault();
    setError("");
    setResult(null);

    try {
      setResult(await getBooking(cinemaId, groupSize));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      <section className="mb-6 rounded-xl border border-zinc-800 bg-zinc-900 p-5">
        <h2 className="mb-3 text-lg font-semibold">Book a watch party</h2>
        <form onSubmit={getQuote} className="flex flex-wrap gap-3">
          <select
            className={`${inputClass} min-w-52 flex-1`}
            value={cinemaId}
            onChange={chooseCinema}
            required
          >
            <option value="">Pick a cinema...</option>
            {cinemas.map((cinema) => (
              <option key={cinema.id} value={cinema.id}>
                {cinema.name} (bundles: {cinema.bundle_sizes.join(", ")})
              </option>
            ))}
          </select>

          <input
            className={`${inputClass} w-40`}
            type="number"
            placeholder="Group size"
            min="1"
            max="10000"
            value={groupSize}
            onChange={changeGroupSize}
            required
          />

          <button className="rounded-lg bg-emerald-600 px-5 py-2 font-semibold text-white hover:bg-emerald-500">
            Get quote
          </button>
        </form>
      </section>

      {error && (
        <p className="mb-4 rounded-lg border border-red-800 bg-red-950 p-3 text-red-300">
          {error}
        </p>
      )}

      {result && !result.possible && (
        <section className="rounded-xl border border-amber-700 bg-amber-950 p-5 text-amber-200">
          <p className="text-lg font-semibold">Not possible</p>
          <p className="mt-1 text-sm">
            No combination of this cinema's bundles adds up to exactly {result.group_size}{" "}
            seats.
          </p>
        </section>
      )}

      {result && result.possible && (
        <section className="rounded-xl border border-emerald-700 bg-zinc-900 p-5">
          <p className="mb-4 text-lg font-semibold">
            {result.total_bundles} {result.total_bundles === 1 ? "bundle" : "bundles"} for{" "}
            <span className="text-emerald-400">{result.group_size} seats</span>
          </p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {result.bundles.map((bundle) => (
              <div
                key={bundle.size}
                className="rounded-lg border border-zinc-700 bg-zinc-800 p-4 text-center"
              >
                <p className="text-3xl font-bold">× {bundle.count}</p>
                <p className="text-sm text-zinc-400">bundle of {bundle.size} seats</p>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}