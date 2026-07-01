<script setup>
import { ref, onMounted } from "vue";
import { api } from "../lib/api";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const trades = ref([]);
const loading = ref(false);

onMounted(async () => {
  loading.value = true;
  try {
    trades.value = await api.listTrades();
  } finally {
    loading.value = false;
  }
});

function fmtDate(d) {
  return new Date(d).toLocaleString("fr-FR", {
    day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
}
</script>

<template>
  <div class="mx-auto max-w-5xl px-5 py-10">
    <h1 class="h-display text-3xl font-semibold">Historique des achats</h1>
    <p v-if="auth.isBeginner" class="mt-1 text-muted">
      Chaque achat exécuté automatiquement par le bot, avec sa date et son prix.
    </p>

    <div v-if="!loading && !trades.length" class="card mt-6 text-center text-muted">
      Aucun achat encore exécuté.
    </div>

    <div v-else-if="trades.length" class="card mt-6 !p-0 overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-line text-left text-xs uppercase tracking-wide text-muted">
            <th class="px-5 py-3 font-medium">Date</th>
            <th class="px-5 py-3 font-medium">Crypto</th>
            <th class="px-5 py-3 font-medium">Montant</th>
            <th class="px-5 py-3 font-medium">Prix</th>
            <th class="px-5 py-3 font-medium">Statut</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in trades" :key="t.id" class="border-b border-line last:border-0 hover:bg-paper-2/40">
            <td class="px-5 py-3 text-ink-soft">{{ fmtDate(t.executed_at) }}</td>
            <td class="px-5 py-3 font-medium">{{ t.symbol }}</td>
            <td class="px-5 py-3">{{ t.amount }} {{ t.quote_currency }}</td>
            <td class="px-5 py-3">{{ t.price ? `${t.price} ${t.quote_currency}` : "—" }}</td>
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
