<script setup>

import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const router = useRouter();

const step = ref(0);
const answers = ref({ knowledge: null, guidance: null });
const busy = ref(false);

const suggestedMode = computed(() => {
  const { knowledge, guidance } = answers.value;
  if (knowledge === "none" || guidance === "guided") return "beginner";
  return "advanced";
});

function pick(key, value) {
  answers.value[key] = value;
  if (step.value < 2) step.value++;
}

async function finish(mode) {
  busy.value = true;
  try {
    await auth.setMode(mode);
    router.push({ name: "dashboard" });
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center p-6">
    <div class="w-full max-w-md">

      <div class="mb-8 flex items-center justify-center gap-1.5">
        <span
          v-for="i in 3"
          :key="i"
          class="h-1.5 rounded-full transition-all"
          :class="i - 1 <= step ? 'w-8 bg-brand' : 'w-4 bg-line-strong'"
        ></span>
      </div>

      <div class="card">
        <p v-if="step < 2" class="field-label !text-brand">Faisons connaissance · 1 min</p>


        <div v-if="step === 0">
          <h2 class="h-display text-2xl font-semibold">Tu connais la crypto ?</h2>
          <p class="mt-1 text-sm text-muted">Et l'investissement automatique (DCA) ?</p>
          <div class="mt-5 space-y-2.5">
            <button class="onb-opt" @click="pick('knowledge', 'none')">
              <strong>Je débute</strong><span>Explique-moi tout, pas à pas.</span>
            </button>
            <button class="onb-opt" @click="pick('knowledge', 'some')">
              <strong>Je connais les bases</strong><span>J'ai déjà quelques notions.</span>
            </button>
            <button class="onb-opt" @click="pick('knowledge', 'pro')">
              <strong>Je suis à l'aise</strong><span>Exchanges, API, DCA — ça me parle.</span>
            </button>
          </div>
        </div>

        <div v-else-if="step === 1">
          <h2 class="h-display text-2xl font-semibold">Comment t'accompagner ?</h2>
          <div class="mt-5 space-y-2.5">
            <button class="onb-opt" @click="pick('guidance', 'guided')">
              <strong>Avec des explications</strong><span>Des repères à chaque étape.</span>
            </button>
            <button class="onb-opt" @click="pick('guidance', 'direct')">
              <strong>Accès direct</strong><span>Interface dense, sans pop-ups.</span>
            </button>
          </div>
          <button class="btn-ghost mt-4" @click="step = 0">← Retour</button>
        </div>


        <div v-else>
          <h2 class="h-display text-2xl font-semibold">
            Mode {{ suggestedMode === "beginner" ? "Débutant" : "Confirmé" }}
          </h2>
          <p class="mt-2 text-muted">
            {{ suggestedMode === "beginner"
              ? "Tu seras guidé, avec des explications simples à chaque étape."
              : "Interface dense et directe, sans friction pédagogique." }}
            <span class="block mt-2 text-sm">Tu pourras changer à tout moment dans les réglages.</span>
          </p>
          <div class="mt-6 space-y-2.5">
            <button class="btn-primary w-full" :disabled="busy" @click="finish(suggestedMode)">
              Continuer en {{ suggestedMode === "beginner" ? "Débutant" : "Confirmé" }}
            </button>
            <button class="btn-ghost w-full" :disabled="busy"
              @click="finish(suggestedMode === 'beginner' ? 'advanced' : 'beginner')">
              Plutôt l'autre mode
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@reference "../style.css";
.onb-opt {
  @apply flex w-full flex-col items-start gap-0.5 rounded-xl border border-line-strong
         bg-paper/40 px-4 py-3 text-left transition cursor-pointer
         hover:border-brand hover:bg-brand-soft/40;
}
.onb-opt strong { @apply text-ink font-medium; }
.onb-opt span { @apply text-sm text-muted; }
</style>
