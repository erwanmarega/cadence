<script setup>
import { ref, onMounted } from "vue";
import { api } from "../lib/api";
import { useAuthStore } from "../stores/auth";
import Tooltip from "../components/Tooltip.vue";
import ConfirmModal from "../components/ConfirmModal.vue";

const auth = useAuthStore();

const connections = ref([]);
const form = ref({ exchange: "kraken", api_key: "", api_secret: "", passphrase: "" });
const error = ref("");
const busy = ref(false);

const toDelete = ref(null);
const deleting = ref(false);

async function load() {
  connections.value = await api.listExchanges();
}
onMounted(load);

async function submit() {
  error.value = "";
  busy.value = true;
  try {
    const payload = {
      exchange: form.value.exchange,
      api_key: form.value.api_key.trim(),
      api_secret: form.value.api_secret.trim(),
    };
    if (form.value.passphrase) payload.passphrase = form.value.passphrase.trim();
    await api.connectExchange(payload);
    form.value = { exchange: "kraken", api_key: "", api_secret: "", passphrase: "" };
    await load();
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}

async function confirmRemove() {
  if (!toDelete.value) return;
  deleting.value = true;
  try {
    await api.deleteExchange(toDelete.value.id);
    await load();
    toDelete.value = null;
  } finally {
    deleting.value = false;
  }
}
</script>

<template>
  <div class="mx-auto max-w-xl px-5 py-10">
    <RouterLink to="/settings" class="mb-4 inline-block text-sm text-muted hover:text-ink">← Réglages</RouterLink>
    <h1 class="h-display text-3xl font-semibold">Comptes d'échange</h1>

    <div class="mt-5 rounded-[var(--radius-xl2)] border border-brand/25 bg-brand-soft/50 p-5">
      <div class="flex items-start gap-3">
        <span class="text-lg">🔒</span>
        <div>
          <strong class="text-brand-ink">Permission « retrait » jamais nécessaire</strong>
          <p class="mt-1 text-sm text-ink-soft">
            Cadence ne touche jamais à tes fonds. Crée une clé API avec
            <strong>uniquement</strong> la permission de trading. N'active
            <strong>jamais</strong> le retrait. Tes clés sont chiffrées avant
            stockage, jamais lisibles en clair.
          </p>
        </div>
      </div>
    </div>


    <div v-if="connections.length" class="mt-6 space-y-3">
      <div v-for="c in connections" :key="c.id" class="card flex items-center justify-between !p-4">
        <div class="flex items-center gap-3">
          <span class="grid h-9 w-9 place-items-center rounded-lg bg-paper-2 text-sm font-semibold capitalize">
            {{ c.exchange[0] }}
          </span>
          <div>
            <p class="font-medium capitalize">{{ c.exchange }}</p>
            <p class="text-sm text-muted">Clé ••••{{ c.api_key_hint }}</p>
          </div>
        </div>
        <button class="btn-ghost text-danger hover:bg-danger-soft" @click="toDelete = c">Supprimer</button>
      </div>
    </div>


    <form class="card mt-6 space-y-5" @submit.prevent="submit">
      <h3 class="h-display text-lg font-semibold">Connecter un compte</h3>
      <div>
        <label class="field-label">Plateforme</label>
        <select v-model="form.exchange" class="field">
          <option value="kraken">Kraken</option>
          <option value="coinbase">Coinbase</option>
        </select>
      </div>
      <div>
        <label class="field-label">Clé API <Tooltip text="Générée sur ta plateforme, dans les réglages API. Trading uniquement." /></label>
        <input v-model="form.api_key" autocomplete="off" class="field" />
      </div>
      <div>
        <label class="field-label">Secret API</label>
        <input v-model="form.api_secret" type="password" autocomplete="off" class="field" />
      </div>
      <div v-if="form.exchange === 'coinbase'">
        <label class="field-label">Passphrase (si demandée)</label>
        <input v-model="form.passphrase" type="password" autocomplete="off" class="field" />
      </div>
      <p v-if="auth.isBeginner" class="text-xs text-muted">
        On vérifie la clé en lecture seule avant de l'enregistrer. Si elle a la
        permission de retrait, supprime-la et régénère-en une sans cette permission.
      </p>
      <p v-if="error" class="text-sm text-danger">{{ error }}</p>
      <button type="submit" class="btn-primary w-full" :disabled="busy">
        {{ busy ? "Vérification…" : "Vérifier et connecter" }}
      </button>
    </form>
  </div>

  <ConfirmModal
    :open="!!toDelete"
    danger
    title="Supprimer ce compte ?"
    :message="toDelete ? `Le compte ${toDelete.exchange} sera supprimé. Les plans qui l'utilisent seront aussi supprimés. Cela n'affecte pas ton compte sur l'exchange ni tes fonds.` : ''"
    confirm-label="Supprimer"
    :busy="deleting"
    @update:open="(v) => { if (!v) toDelete = null; }"
    @confirm="confirmRemove"
  />
</template>
