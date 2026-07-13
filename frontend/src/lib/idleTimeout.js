import { watch, onBeforeUnmount } from "vue";
import { storeToRefs } from "pinia";
import { useAuthStore } from "../stores/auth";
import router from "../router";

const IDLE_LIMIT_MS = 15 * 60 * 1000;
const CHECK_INTERVAL_MS = 30 * 1000;
const LAST_ACTIVITY_KEY = "cadence_last_activity";

const ACTIVITY_EVENTS = [
  "mousemove",
  "mousedown",
  "keydown",
  "scroll",
  "touchstart",
  "click",
];

export function useIdleTimeout() {
  const auth = useAuthStore();
  const { isAuthenticated } = storeToRefs(auth);

  let intervalId = null;

  function markActivity() {
    localStorage.setItem(LAST_ACTIVITY_KEY, String(Date.now()));
  }

  function lastActivity() {
    const raw = localStorage.getItem(LAST_ACTIVITY_KEY);
    const parsed = raw ? parseInt(raw, 10) : NaN;
    return Number.isNaN(parsed) ? Date.now() : parsed;
  }

  async function checkIdle() {
    if (!isAuthenticated.value) return;
    if (Date.now() - lastActivity() < IDLE_LIMIT_MS) return;
    await logout();
  }

  async function logout() {
    stop();
    await auth.signOut();
    localStorage.removeItem(LAST_ACTIVITY_KEY);
    if (router.currentRoute.value.name !== "login") {
      router.push({ name: "login", query: { timeout: "1" } });
    }
  }

  function start() {
    markActivity();
    ACTIVITY_EVENTS.forEach((e) =>
      window.addEventListener(e, markActivity, { passive: true })
    );
    document.addEventListener("visibilitychange", checkIdle);
    intervalId = setInterval(checkIdle, CHECK_INTERVAL_MS);
  }

  function stop() {
    ACTIVITY_EVENTS.forEach((e) => window.removeEventListener(e, markActivity));
    document.removeEventListener("visibilitychange", checkIdle);
    if (intervalId) {
      clearInterval(intervalId);
      intervalId = null;
    }
  }

  watch(
    isAuthenticated,
    (authed) => {
      stop();
      if (authed) start();
    },
    { immediate: true }
  );

  onBeforeUnmount(stop);
}
