// Send a request and return the JSON. On an error response, throw its message.
async function request(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message);
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