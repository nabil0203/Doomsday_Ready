import { useState } from "react";
import MoviesView from "./components/MoviesView";
import RewatchView from "./components/RewatchView";
import BookingView from "./components/BookingView";

const TABS = ["Movies", "Rewatch Plan", "Booking"];

export default function App() {
  const [tab, setTab] = useState("Movies");

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="border-b border-zinc-800 bg-zinc-900">
        <div className="mx-auto flex max-w-4xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <h1 className="text-2xl font-extrabold tracking-wide">
            DOOMSDAY <span className="text-emerald-500">READY</span>
          </h1>

          <nav className="flex gap-1 rounded-full bg-zinc-800 p-1">
            {TABS.map((name) => (
              <button
                key={name}
                onClick={() => setTab(name)}
                className={
                  tab === name
                    ? "rounded-full bg-emerald-600 px-4 py-1.5 text-sm font-semibold text-white"
                    : "rounded-full px-4 py-1.5 text-sm text-zinc-400 hover:text-white"
                }
              >
                {name}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-8">
        {tab === "Movies" && <MoviesView />}
        {tab === "Rewatch Plan" && <RewatchView />}
        {tab === "Booking" && <BookingView />}
      </main>
    </div>
  );
}