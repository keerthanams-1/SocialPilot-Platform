import axios from 'axios';

// Configure standard Axios client
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  withCredentials: true, // Crucial for sending/receiving HttpOnly cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Response Interceptor to capture 401 Unauthorized and perform silent token refreshes
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Check if error is 401 Unauthorized and request hasn't been retried yet
    // Also, ensure we don't intercept auth routes (login, register, refresh-token) to prevent loops
    const isAuthRoute = originalRequest.url && (
      originalRequest.url.includes('/auth/refresh-token') || 
      originalRequest.url.includes('/auth/login') ||
      originalRequest.url.includes('/auth/register')
    );

    if (error.response && error.response.status === 401 && !originalRequest._retry && !isAuthRoute) {
      
      // If we are already refreshing, push the request into the queue
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({
            resolve: (token) => {
              // Retry request with new Authorization header if necessary
              originalRequest.headers['Authorization'] = 'Bearer ' + token;
              resolve(api(originalRequest));
            },
            reject: (err) => {
              reject(err);
            },
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      return new Promise((resolve, reject) => {
        // Handshake with refresh-token endpoint
        api.post('/auth/refresh-token')
          .then(({ data }) => {
            const { access_token } = data;
            
            // Set authorization headers
            api.defaults.headers.common['Authorization'] = 'Bearer ' + access_token;
            originalRequest.headers['Authorization'] = 'Bearer ' + access_token;
            
            processQueue(null, access_token);
            resolve(api(originalRequest));
          })
          .catch((err) => {
            processQueue(err, null);
            
            // If refresh fails, session is completely dead. Clear states and redirect
            if (typeof window !== 'undefined') {
              window.dispatchEvent(new CustomEvent('auth-expired'));
            }
            reject(err);
          })
          .finally(() => {
            isRefreshing = false;
          });
      });
    }

    return Promise.reject(error);
  }
);

export default api;
