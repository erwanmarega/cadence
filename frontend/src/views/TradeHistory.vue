<script setup>
import { ref, onMounted } from "vue";
import { api } from "../lib/api";

const trades = ref([]);
const loading = ref(false);
const syncing = ref(false);
const syncMsg = ref("");
const syncErrors = ref([]);

async function load() {
  loading.value = true;
  try {
    trades.value = await api.listTrades();
  } finally {
    loading.value = false;
  }
}

async function sync() {
  syncing.value = true;
  syncMsg.value = "";
  syncErrors.value = [];
  try {
    const r = await api.syncTrades();
    syncErrors.value = r.errors || [];
    syncMsg.value = r.imported > 0
      ? `${r.imported} achat${r.imported > 1 ? "s" : ""} importé${r.imported > 1 ? "s" : ""} depuis tes exchanges.`
      : (syncErrors.value.length ? "" : "Aucun nouvel achat à importer.");
    await load();
  } catch (e) {
    syncMsg.value = e.message;
  } finally {
    syncing.value = false;
  }
}

onMounted(load);

function fmtDate(d) {
  return new Date(d).toLocaleString("fr-FR", {
    day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
}
</script>

<template>
  <div class="mx-auto max-w-5xl px-5 py-10">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 class="h-display text-3xl font-semibold">Historique des achats</h1>
        <p class="mt-1 text-muted">
          Les achats du bot <span class="text-ink-soft">et</span> ceux faits directement sur tes exchanges.
        </p>
      </div>
      <button class="btn-secondary" :disabled="syncing" @click="sync">
        {{ syncing ? "Synchronisation…" : "↻ Synchroniser mes exchanges" }}
      </button>
    </div>

    <p v-if="syncMsg" class="mt-3 text-sm text-muted">{{ syncMsg }}</p>
    <div v-if="syncErrors.length" class="mt-3 rounded-xl border border-danger/30 bg-danger-soft px-4 py-3 text-sm text-danger">
      <p v-for="(e, i) in syncErrors" :key="i">{{ e }}</p>
    </div>

    <div v-if="!loading && !trades.length" class="card mt-6 text-center text-muted">
      Aucun achat encore. Crée un plan, ou synchronise tes achats déjà faits sur tes exchanges.
    </div>

    <div v-else-if="trades.length" class="card mt-6 p-0 overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-line text-left text-xs uppercase tracking-wide text-muted">
            <th class="px-5 py-3 font-medium">Date</th>
            <th class="px-5 py-3 font-medium">Crypto</th>
            <th class="px-5 py-3 font-medium">Sens</th>
            <th class="px-5 py-3 font-medium">Montant</th>
            <th class="px-5 py-3 font-medium">Prix</th>
            <th class="px-5 py-3 font-medium">Origine</th>
            <th class="px-5 py-3 font-medium">Statut</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in trades" :key="t.id" class="border-b border-line last:border-0 hover:bg-paper-2/40">
            <td class="px-5 py-3 text-ink-soft">{{ fmtDate(t.executed_at) }}</td>
            <td class="px-5 py-3 font-medium">{{ t.symbol }}</td>
            <td class="px-5 py-3">
              <span v-if="t.side === 'sell'" class="text-danger">Vente</span>
              <span v-else>Achat</span>
            </td>
            <td class="px-5 py-3">{{ t.amount }} {{ t.quote_currency }}</td>
            <td class="px-5 py-3">{{ t.price ? `${t.price} ${t.quote_currency}` : "—" }}</td>
            <td class="px-5 py-3">
              <span class="badge capitalize" :class="t.source === 'exchange' ? 'badge-paused' : 'badge-active'">
                {{ t.source === "exchange" ? (t.exchange || "Manuel") : "Cadence" }}
              </span>
            </td>
            <td class="px-5 py-3">
              <span class="badge" :class="t.status === 'success' ? 'badge-success' : 'badge-failed'">
                {{ t.status === "success" ? "Réussi" : "Échec" }}
              </span>
              <span v-if="t.error" class="ml-1 cursor-help text-muted" :title="t.error">ⓘ</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
