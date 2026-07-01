<script setup>
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import EmergencyStop from "./EmergencyStop.vue";

const auth = useAuthStore();
const router = useRouter();

const links = [
  { to: "/", label: "Portefeuille" },
  { to: "/goals", label: "Objectifs" },
  { to: "/trends", label: "Tendances" },
  { to: "/history", label: "Historique" },
  { to: "/settings", label: "Réglages" },
];

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
        <span class="badge badge-active whitespace-nowrap">
          {{ auth.isBeginner ? "Débutant" : "Confirmé" }}
        </span>
        <button class="btn-ghost" @click="logout">Quitter</button>
      </div>
    </div>
  </header>
</template>
