<script setup>
import { ref, onMounted, computed } from "vue";
import { supabase } from "../lib/supabase";

const factors = ref([]);
const loading = ref(true);


const enrolling = ref(false);
const enrollData = ref(null);
const code = ref("");
const error = ref("");
const busy = ref(false);

const hasVerified = computed(() => factors.value.some((f) => f.status === "verified"));

async function loadFactors() {
  loading.value = true;
  try {
    const { data, error: e } = await supabase.auth.mfa.listFactors();
    if (e) throw e;
    factors.value = data.totp || [];
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
onMounted(loadFactors);

async function startEnroll() {
  error.value = "";
  busy.value = true;
  try {

    const stale = factors.value.find((f) => f.status === "unverified");
    if (stale) await supabase.auth.mfa.unenroll({ factorId: stale.id });

    const { data, error: e } = await supabase.auth.mfa.enroll({ factorType: "totp" });
    if (e) throw e;
    enrollData.value = { id: data.id, qr_code: data.totp.qr_code, secret: data.totp.secret };
    enrolling.value = true;
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}

async function verifyEnroll() {
  error.value = "";
  busy.value = true;
  try {
    const { data: ch, error: ce } = await supabase.auth.mfa.challenge({ factorId: enrollData.value.id });
    if (ce) throw ce;
    const { error: ve } = await supabase.auth.mfa.verify({
      factorId: enrollData.value.id,
      challengeId: ch.id,
      code: code.value.trim(),
    });
    if (ve) throw ve;
    enrolling.value = false;
    enrollData.value = null;
    code.value = "";
    await loadFactors();
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}

async function cancelEnroll() {
  if (enrollData.value) {
    try { await supabase.auth.mfa.unenroll({ factorId: enrollData.value.id }); } catch {  }
  }
  enrolling.value = false;
  enrollData.value = null;
  code.value = "";
}

async function disable(factorId) {
  busy.value = true;
  try {
    await supabase.auth.mfa.unenroll({ factorId });
    await loadFactors();
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div class="mx-auto max-w-2xl px-5 py-10">
    <RouterLink to="/settings" class="mb-4 inline-block text-sm text-muted hover:text-ink">← Réglages</RouterLink>
    <h1 class="h-display text-3xl font-semibold">Sécurité</h1>


    <div class="mt-6 rounded-[var(--radius-xl2)] border border-brand/25 bg-brand-soft/50 p-6">
      <div class="flex items-start gap-3">
        <span class="text-2xl">🔒</span>
        <div>
          <h2 class="h-display text-xl font-semibold text-brand-ink">On ne peut jamais retirer tes fonds</h2>
          <p class="mt-2 text-sm text-ink-soft">
            Cadence est <strong>non-custodial</strong> : ton argent et tes cryptos
            restent en permanence sur ton compte d'échange (Kraken, Coinbase).
            Nous ne les détenons jamais.
          </p>
        </div>
      </div>
      <ul class="mt-4 space-y-2 text-sm text-ink-soft">
        <li class="flex gap-2"><span class="text-brand">✓</span> Ta clé API n'a que la permission de <strong>trading</strong> — jamais celle de retrait.</li>
        <li class="flex gap-2"><span class="text-brand">✓</span> Aucune ligne de code Cadence ne peut déclencher un retrait : la fonction n'existe pas.</li>
        <li class="flex gap-2"><span class="text-brand">✓</span> Tes clés sont <strong>chiffrées</strong> avant stockage, jamais lisibles en clair.</li>
        <li class="flex gap-2"><span class="text-brand">✓</span> Chaque utilisateur est isolé (Row Level Security) : personne d'autre n'accède à tes données.</li>
      </ul>
    </div>

    <div class="card mt-6">
      <div class="flex items-start justify-between gap-4">
        <div>
          <h2 class="h-display text-xl font-semibold">Double authentification (2FA)</h2>
          <p class="mt-1 text-sm text-muted">
            Ajoute un code temporaire (Google Authenticator, Authy…) en plus de ton mot de passe.
          </p>
        </div>
        <span v-if="hasVerified" class="badge badge-success whitespace-nowrap">Activée</span>
        <span v-else class="badge badge-paused whitespace-nowrap">Désactivée</span>
      </div>

      <p v-if="error" class="mt-4 text-sm text-danger">{{ error }}</p>

      <div v-if="hasVerified && !enrolling" class="mt-5">
        <button class="btn-secondary text-danger" :disabled="busy"
                @click="disable(factors.find((f) => f.status === 'verified').id)">
          Désactiver la 2FA
        </button>
      </div>

      <div v-else-if="!enrolling" class="mt-5">
        <button class="btn-primary" :disabled="busy || loading" @click="startEnroll">Activer la 2FA</button>
      </div>

      <div v-else class="mt-5 space-y-4">
        <ol class="space-y-3 text-sm text-ink-soft">
          <li><strong>1.</strong> Scanne ce QR code avec ton appli d'authentification :</li>
        </ol>
        <div class="flex flex-col items-center gap-3 rounded-xl border border-line bg-paper/40 p-5">
          <img v-if="enrollData?.qr_code" :src="enrollData.qr_code" alt="QR 2FA" class="h-44 w-44" />
          <p class="text-xs text-muted">Pas de caméra ? Saisis ce code :
            <code class="select-all rounded bg-paper-2 px-1.5 py-0.5 text-ink">{{ enrollData?.secret }}</code>
          </p>
        </div>
        <div>
          <label class="field-label">2. Entre le code à 6 chiffres</label>
          <input v-model="code" inputmode="numeric" maxlength="6" class="field tracking-widest" placeholder="123456" />
        </div>
        <div class="flex gap-3">
          <button class="btn-primary" :disabled="busy || code.length < 6" @click="verifyEnroll">Vérifier et activer</button>
          <button class="btn-ghost" :disabled="busy" @click="cancelEnroll">Annuler</button>
        </div>
      </div>
    </div>
  </div>
</template>
