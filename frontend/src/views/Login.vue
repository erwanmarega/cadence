<script setup>
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { supabase } from "../lib/supabase";
import Spinner from "../components/Spinner.vue";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

const timedOut = ref(route.query.timeout === "1");

const isSignup = ref(false);
const email = ref("");
const password = ref("");
const error = ref("");
const busy = ref(false);


const mfaStep = ref(false);
const mfaCode = ref("");
const mfaFactorId = ref(null);

function proceed() {
  router.push(auth.onboarded ? { name: "dashboard" } : { name: "onboarding" });
}

async function submit() {
  error.value = "";
  busy.value = true;
  try {
    if (isSignup.value) {
      await auth.signUp(email.value, password.value);
    }
    await auth.signIn(email.value, password.value);


    const { data: aal } = await supabase.auth.mfa.getAuthenticatorAssuranceLevel();
    if (aal?.nextLevel === "aal2" && aal.nextLevel !== aal.currentLevel) {
      const { data: factors } = await supabase.auth.mfa.listFactors();
      const totp = (factors.totp || []).find((f) => f.status === "verified");
      if (totp) {
        mfaFactorId.value = totp.id;
        mfaStep.value = true;
        return;
      }
    }
    proceed();
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}

async function google() {
  error.value = "";
  busy.value = true;
  try {
    await auth.signInWithGoogle();
  } catch (e) {
    error.value = e.message;
    busy.value = false;
  }
}

async function submitMfa() {
  error.value = "";
  busy.value = true;
  try {
    const { data: ch, error: ce } = await supabase.auth.mfa.challenge({ factorId: mfaFactorId.value });
    if (ce) throw ce;
    const { error: ve } = await supabase.auth.mfa.verify({
      factorId: mfaFactorId.value,
      challengeId: ch.id,
      code: mfaCode.value.trim(),
    });
    if (ve) throw ve;
    proceed();
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div class="grid min-h-screen lg:grid-cols-2">

    <div class="relative hidden flex-col justify-between overflow-hidden bg-brand p-12 text-white lg:flex">
      <div class="flex items-center gap-2">
        <span class="grid h-8 w-8 place-items-center rounded-lg bg-white/15 font-bold">C</span>
        <span class="h-display text-2xl font-semibold">Cadence</span>
      </div>
      <div class="max-w-sm">
        <h1 class="h-display text-4xl font-semibold leading-tight">
          Épargner en crypto, sans y penser.
        </h1>
        <p class="mt-4 text-white/75">
          Tu choisis un montant et un rythme. Cadence achète pour toi, à
          intervalle régulier. Comme un virement automatique vers ton épargne.
        </p>
        <ul class="mt-6 space-y-2 text-sm text-white/85">
          <li class="flex gap-2"><span>✓</span> Tes exchanges réunis en une seule vue</li>
          <li class="flex gap-2"><span>✓</span> Ton prix d'achat moyen suivi clairement</li>
          <li class="flex gap-2"><span>✓</span> Des objectifs d'épargne motivants</li>
          <li class="flex gap-2"><span>✓</span> Pensé pour les débutants, pas pour les traders</li>
        </ul>
      </div>
      <p class="text-sm text-white/60">
        Non-custodial · tes fonds restent sur ton exchange.
      </p>
      <div class="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-white/10"></div>
      <div class="pointer-events-none absolute -bottom-32 -left-10 h-80 w-80 rounded-full bg-brand-hover/40"></div>
    </div>


    <div class="flex items-center justify-center p-6">
      <div class="w-full max-w-sm">
        <div class="mb-8 lg:hidden">
          <span class="h-display text-2xl font-semibold">Cadence</span>
        </div>

        <template v-if="mfaStep">
          <h2 class="h-display text-3xl font-semibold">Vérification</h2>
          <p class="mt-1 text-muted">Entre le code de ton appli d'authentification.</p>
          <form class="mt-8 space-y-4" @submit.prevent="submitMfa">
            <div>
              <label class="field-label">Code à 6 chiffres</label>
              <input v-model="mfaCode" inputmode="numeric" maxlength="6" autofocus
                     class="field tracking-widest" placeholder="123456" />
            </div>
            <p v-if="error" class="text-sm text-danger">{{ error }}</p>
            <button type="submit" class="btn-primary flex w-full items-center justify-center gap-2" :disabled="busy || mfaCode.length < 6">
              <Spinner v-if="busy" size="1rem" />
              {{ busy ? "Vérification…" : "Valider" }}
            </button>
          </form>
        </template>

        <template v-else>
          <h2 class="h-display text-3xl font-semibold">
            {{ isSignup ? "Créer un compte" : "Bon retour" }}
          </h2>
          <p class="mt-1 text-muted">
            {{ isSignup ? "Quelques secondes, puis on configure ton épargne." : "Connecte-toi pour reprendre où tu en étais." }}
          </p>

          <p v-if="timedOut" class="mt-4 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
            Tu as été déconnecté après 15 minutes d'inactivité. Reconnecte-toi pour continuer.
          </p>

          <button type="button" class="btn-secondary mt-8 flex w-full items-center justify-center gap-2" :disabled="busy" @click="google">
            <Spinner v-if="busy" size="1rem" />
            <svg v-else class="h-4 w-4" viewBox="0 0 48 48" aria-hidden="true">
              <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
              <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
              <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
              <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
            </svg>
            Continuer avec Google
          </button>

          <div class="my-5 flex items-center gap-3 text-xs text-muted">
            <span class="h-px flex-1 bg-line"></span>ou<span class="h-px flex-1 bg-line"></span>
          </div>

          <form class="space-y-4" @submit.prevent="submit">
            <div>
              <label class="field-label">Email</label>
              <input v-model="email" type="email" required autocomplete="email" class="field" placeholder="toi@email.com" />
            </div>
            <div>
              <label class="field-label">Mot de passe</label>
              <input v-model="password" type="password" required autocomplete="current-password" class="field" placeholder="••••••••" />
            </div>
            <p v-if="error" class="text-sm text-danger">{{ error }}</p>
            <button type="submit" class="btn-primary flex w-full items-center justify-center gap-2" :disabled="busy">
              <Spinner v-if="busy" size="1rem" />
              {{ busy ? "Connexion…" : isSignup ? "Créer mon compte" : "Se connecter" }}
            </button>
          </form>

          <button class="btn-ghost mt-4 w-full" @click="isSignup = !isSignup; error = ''">
            {{ isSignup ? "J'ai déjà un compte" : "Pas encore de compte ? S'inscrire" }}
          </button>

          <RouterLink to="/simulate" class="mt-6 block text-center text-sm text-muted hover:text-ink">
            Curieux ? → Simule une épargne crypto, sans compte
          </RouterLink>
        </template>
      </div>
    </div>
  </div>
</template>
