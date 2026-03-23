import axios from "axios";

const BASE_URL = import.meta.env.DEV ? "http://localhost:8000" : "";

const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
});

export default api;