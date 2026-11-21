// Empty locally (the Vite proxy handles /api). On the live site it is the backend's address.
const BASE = import.meta.env.VITE_API_URL || "";

// Send a request and return the JSON. On an error response, throw its message.
// Send a request and return the JSON. On an error response, throw its message.
async function request(url, options) {
  const response = await fetch(BASE + url, options);

  let data = null;
  try {
    data = await response.json();
  } catch {
    // the server sent no JSON (empty body or an HTML error page)
  }

  if (!response.ok) {
    throw new Error(data ? data.message : `Server error (${response.status})`);
  }
  return data;
}

function sendJson(method, url, body) {
  return request(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export const getMovies = () => request("/api/movies");
export const createMovie = (movie) => sendJson("POST", "/api/movies", movie);
export const updateMovie = (id, changes) => sendJson("PATCH", `/api/movies/${id}`, changes);
export const getRewatchOrder = (id) => request(`/api/movies/${id}/rewatch-order`);

export const getCinemas = () => request("/api/cinemas");
export const getBooking = (id, groupSize) =>
  request(`/api/cinemas/${id}/booking?groupSize=${groupSize}`);