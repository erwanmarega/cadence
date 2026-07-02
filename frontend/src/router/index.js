import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

const routes = [
  { path: "/login", name: "login", component: () => import("../views/Login.vue"), meta: { public: true } },
  { path: "/simulate", name: "simulate", component: () => import("../views/Simulate.vue"), meta: { public: true } },
  { path: "/onboarding", name: "onboarding", component: () => import("../views/Onboarding.vue") },
  { path: "/", name: "dashboard", component: () => import("../views/Dashboard.vue") },
  { path: "/strategy/new", name: "strategy-new", component: () => import("../views/StrategyConfig.vue") },
  { path: "/exchanges", name: "exchanges", component: () => import("../views/ExchangeConnect.vue") },
  { path: "/goals", name: "goals", component: () => import("../views/Goals.vue") },
  { path: "/trends", name: "trends", component: () => import("../views/Trends.vue") },
  { path: "/history", name: "history", component: () => import("../views/TradeHistory.vue") },
  { path: "/settings", name: "settings", component: () => import("../views/Settings.vue") },
  { path: "/security", name: "security", component: () => import("../views/Security.vue") },
  { path: "/tax", name: "tax", component: () => import("../views/TaxExport.vue") },
  { path: "/learn", name: "learn", component: () => import("../views/Learn.vue") },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  if (!auth.ready) await auth.init();

  if (to.meta.public) return true;

  if (!auth.isAuthenticated) return { name: "login" };


  if (!auth.onboarded && to.name !== "onboarding") return { name: "onboarding" };

  return true;
});

export default router;
