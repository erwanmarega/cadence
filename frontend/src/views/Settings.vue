<script setup>

import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { api } from "../lib/api";

const auth = useAuthStore();
const router = useRouter();
const busy = ref(false);
const connCount = ref(null);

onMounted(async () => {
  try {
    connCount.value = (await api.listExchanges()).length;
  } catch {
    connCount.value = null;
  }
});

async function choose(mode) {
  if (mode === auth.mode) return;
  busy.value = true;
  try {
    await auth.setMode(mode);
  } finally {
    busy.value = false;
  }
}

const modes = [
  { key: "beginner", title: "Débutant", desc: "Explications à chaque étape, vocabulaire simple." },
  { key: "advanced", title: "Confirmé", desc: "Interface dense, accès direct, sans pop-ups." },
];
</script>

<template>
  <div class="mx-auto max-w-xl px-5 py-10">
    <h1 class="h-display text-3xl font-semibold">Réglages</h1>

    <div class="card mt-6">
      <h3 class="h-display text-lg font-semibold">Mode d'affichage</h3>
      <p class="mt-1 text-sm text-muted">Tu peux changer de mode quand tu veux.</p>

      <div class="mt-5 grid gap-3 sm:grid-cols-2">
        <button
          v-for="m in modes"
          :key="m.key"
          class="rounded-xl border p-4 text-left transition cursor-pointer"
          :class="auth.mode === m.key
            ? 'border-brand bg-brand-soft/50 ring-1 ring-brand'
            : 'border-line-strong bg-paper/40 hover:border-ink/30'"
          :disabled="busy"
          @click="choose(m.key)"
        >
          <div class="flex items-center justify-between">
            <strong class="font-medium">{{ m.title }}</strong>
            <span v-if="auth.mode === m.key" class="text-brand">✓</span>
          </div>
          <p class="mt-1 text-sm text-muted">{{ m.desc }}</p>
        </button>
      </div>
    </div>

    <button class="card mt-4 flex w-full items-center justify-between text-left transition hover:border-ink/30"
            @click="router.push({ name: 'exchanges' })">
      <div>
        <h3 class="h-display text-lg font-semibold">Comptes d'échange</h3>
        <p class="mt-1 text-sm text-muted">
          <span v-if="connCount !== null">{{ connCount }} compte{{ connCount > 1 ? "s" : "" }} connecté{{ connCount > 1 ? "s" : "" }}</span>
          <span v-else>Connecter Kraken ou Coinbase</span>
        </p>
      </div>
      <span class="text-muted">→</span>
    </button>


    <button class="card mt-4 flex w-full items-center justify-between text-left transition hover:border-ink/30"
            @click="router.push({ name: 'security' })">
      <div>
        <h3 class="h-display text-lg font-semibold">Sécurité</h3>
        <p class="mt-1 text-sm text-muted">Double authentification, protection de tes fonds</p>
      </div>
      <span class="text-muted">→</span>
    </button>

    <div class="card mt-4 text-sm text-muted">
      Connecté en tant que <span class="text-ink">{{ auth.user?.email }}</span>
    </div>
  </div>
</template>
