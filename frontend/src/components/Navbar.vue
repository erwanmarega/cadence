<script setup>
import { computed, ref, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { api } from "../lib/api";
import EmergencyStop from "./EmergencyStop.vue";

const auth = useAuthStore();
const router = useRouter();

const links = computed(() => [
  { to: "/", label: "Portefeuille" },
  { to: "/goals", label: "Objectifs" },
  { to: "/trends", label: "Tendances" },
  { to: "/history", label: "Historique" },
  ...(auth.isBeginner ? [{ to: "/learn", label: "Apprendre" }] : []),
  { to: "/settings", label: "Réglages" },
]);

const notifs = ref([]);
const unread = ref(0);
const bellOpen = ref(false);
let timer = null;

async function loadNotifs() {
  try {
    const r = await api.listNotifications();
    notifs.value = r.items;
    unread.value = r.unread;
  } catch {
    // ignore
  }
}

async function toggleBell() {
  bellOpen.value = !bellOpen.value;
  if (bellOpen.value) {
    await loadNotifs();
    if (unread.value > 0) {
      try {
        await api.markNotificationsRead();
        unread.value = 0;
      } catch {
        // ignore
      }
    }
  }
}

function fmtWhen(d) {
  return new Date(d).toLocaleString("fr-FR", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

onMounted(() => {
  loadNotifs();
  timer = setInterval(loadNotifs, 60000);
});
onUnmounted(() => timer && clearInterval(timer));

async function logout() {
  await auth.signOut();
  router.push({ name: "login" });
}
</script>

<template>
  <header class="sticky top-0 z-30 border-b border-line bg-paper/85 backdrop-blur-md">
    <div class="mx-auto flex h-16 max-w-5xl items-center gap-6 px-5">
      <RouterLink to="/" class="flex items-center gap-2">
        <span class="grid h-7 w-7 place-items-center rounded-lg bg-brand text-sm font-bold text-white">C</span>
        <span class="h-display text-xl font-semibold">Cadence</span>
      </RouterLink>

      <nav class="hidden flex-1 items-center gap-1 md:flex">
        <RouterLink
          v-for="l in links"
          :key="l.to"
          :to="l.to"
          class="rounded-lg px-3 py-1.5 text-sm text-muted transition hover:bg-paper-2 hover:text-ink"
          active-class="!text-ink font-medium bg-paper-2"
        >{{ l.label }}</RouterLink>
      </nav>

      <div class="ml-auto flex items-center gap-3">
        <EmergencyStop />

        <div class="relative">
          <button class="relative grid h-9 w-9 place-items-center rounded-lg text-muted transition hover:bg-paper-2 hover:text-ink"
                  aria-label="Notifications" @click="toggleBell">
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" stroke-linecap="round" stroke-linejoin="round" />
              <path d="M13.7 21a2 2 0 0 1-3.4 0" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            <span v-if="unread > 0"
                  class="absolute -right-0.5 -top-0.5 grid h-4 min-w-4 place-items-center rounded-full bg-danger px-1 text-[10px] font-semibold text-white">
              {{ unread > 9 ? "9+" : unread }}
            </span>
          </button>

          <template v-if="bellOpen">
            <div class="fixed inset-0 z-40" @click="bellOpen = false"></div>
            <div class="absolute right-0 z-50 mt-2 w-80 overflow-hidden rounded-xl border border-line bg-surface shadow-lg">
              <div class="border-b border-line px-4 py-3">
                <p class="font-medium">Notifications</p>
              </div>
              <div v-if="!notifs.length" class="px-4 py-8 text-center text-sm text-muted">
                Rien pour l'instant.
              </div>
              <ul v-else class="max-h-96 overflow-auto">
                <li v-for="n in notifs" :key="n.id"
                    class="border-b border-line px-4 py-3 last:border-0"
                    :class="n.read ? '' : 'bg-brand-soft/20'">
                  <p class="text-sm font-medium">{{ n.title }}</p>
                  <p v-if="n.body" class="mt-0.5 text-xs text-muted">{{ n.body }}</p>
                  <p class="mt-1 text-[11px] text-muted/70">{{ fmtWhen(n.created_at) }}</p>
                </li>
              </ul>
            </div>
          </template>
        </div>

        <span class="badge badge-active whitespace-nowrap">
          {{ auth.isBeginner ? "Débutant" : "Confirmé" }}
        </span>
        <button class="btn-ghost" @click="logout">Quitter</button>
      </div>
    </div>
  </header>
</template>
