<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const open = ref(0);
function toggle(i) {
  open.value = open.value === i ? -1 : i;
}

const sections = [
  {
    q: "C'est quoi le DCA (l'idée derrière Cadence) ?",
    a: "DCA veut dire « investir un montant fixe, à intervalle régulier ». Par exemple 20€ chaque semaine, peu importe le prix du jour. Quand le prix est haut tu achètes moins de crypto, quand il est bas tu en achètes plus. Sur la durée, ton prix d'achat se lisse : tu évites d'avoir à deviner le « bon moment ». C'est la même logique qu'un virement automatique vers un livret d'épargne.",
  },
  {
    q: "C'est quoi une cryptomonnaie ?",
    a: "Une cryptomonnaie est une monnaie numérique qui s'échange sur internet, sans banque au milieu. Le Bitcoin (BTC) est la plus connue, l'Ethereum (ETH) la deuxième. Leur prix varie selon l'offre et la demande — il n'y a pas de valeur « officielle » fixée par un État.",
  },
  {
    q: "Pourquoi ça monte et ça descend autant ?",
    a: "Les cryptos sont volatiles : leur prix peut bouger de plusieurs pour cent en une journée. C'est normal pour cette classe d'actif. Le DCA sert justement à traverser ces hauts et ces bas sans stress, en achetant régulièrement plutôt qu'en une fois. Cadence te montre les variations de façon factuelle, sans jamais te dire quoi faire.",
  },
  {
    q: "Comment lire ma performance ?",
    a: "Trois chiffres à connaître : ce que tu as investi (la somme totale versée), la valeur actuelle (ce que valent tes cryptos aujourd'hui), et ton prix de revient moyen (le prix moyen auquel tu as acheté). Si la valeur actuelle dépasse l'investi, tu es en plus-value latente ; sinon en moins-value latente. « Latente » = tant que tu ne vends pas, rien n'est figé.",
  },
  {
    q: "Est-ce que Cadence peut toucher à mon argent ?",
    a: "Non. Cadence est non-custodial : ton argent et tes cryptos restent sur TON compte d'échange (Kraken, Coinbase). Cadence se connecte via une clé API limitée à l'achat — jamais au retrait. Personne chez Cadence ne peut envoyer tes fonds ailleurs. Tes clés sont chiffrées avant d'être stockées.",
  },
  {
    q: "Quels sont les risques ?",
    a: "Investir comporte un risque de perte en capital : la valeur peut baisser, parfois durablement. Le DCA lisse le prix d'achat mais ne garantit aucun rendement — en marché fortement haussier, il peut même sous-performer un achat en une fois. Règle de bon sens : n'investis que ce que tu peux te permettre de laisser immobilisé, et de voir baisser.",
  },
  {
    q: "Comment je démarre avec Cadence ?",
    a: "1) Tu connectes ton compte d'échange avec une clé API (on te guide, permission achat seulement). 2) Tu crées un plan : un montant, un rythme, une crypto. 3) Cadence achète automatiquement à chaque échéance et tu suis tout depuis le tableau de bord. Tu peux mettre en pause à tout moment.",
  },
];

const glossary = [
  ["DCA", "Investir un montant fixe à intervalle régulier pour lisser le prix d'achat."],
  ["Exchange", "Plateforme où on achète/vend des cryptos (Kraken, Coinbase)."],
  ["Clé API", "Un code qui autorise Cadence à passer des achats sur ton compte — sans accès au retrait."],
  ["Non-custodial", "Cadence ne détient jamais tes fonds ; ils restent chez toi, sur ton exchange."],
  ["Volatilité", "L'ampleur des variations de prix. Élevée en crypto."],
  ["Prix de revient moyen", "Le prix moyen auquel tu as acheté, tous achats confondus."],
  ["Paire (ex : BTC/EUR)", "Ce que tu achètes / avec quelle monnaie tu paies."],
  ["MiCA", "La réglementation européenne encadrant les cryptos depuis 2024."],
];
</script>

<template>
  <div class="mx-auto max-w-2xl px-5 py-10">
    <h1 class="h-display text-3xl font-semibold">Apprendre</h1>
    <p class="mt-1 text-muted">Tout ce qu'il faut comprendre, expliqué simplement. Pas de jargon.</p>

    <div class="mt-4 rounded-xl border border-line bg-brand-soft/30 p-4 text-sm">
      <p class="font-medium text-brand-ink">Information, pas conseil.</p>
      <p class="mt-1 text-muted">
        On t'explique comment ça marche pour que tu décides en connaissance de cause.
        Cadence ne te dira jamais quoi acheter, quand, ni combien — ce serait un conseil
        en investissement, encadré par la loi.
      </p>
    </div>

    <div class="mt-6 space-y-3">
      <div v-for="(s, i) in sections" :key="i" class="card !p-0 overflow-hidden">
        <button class="flex w-full items-center justify-between gap-4 px-5 py-4 text-left" @click="toggle(i)">
          <span class="font-medium">{{ s.q }}</span>
          <span class="text-muted transition-transform" :class="open === i ? 'rotate-45' : ''">+</span>
        </button>
        <div v-if="open === i" class="border-t border-line px-5 py-4 text-sm leading-relaxed text-ink-soft">
          {{ s.a }}
        </div>
      </div>
    </div>

    <h2 class="h-display mt-10 text-xl font-semibold">Lexique</h2>
    <dl class="mt-4 space-y-3">
      <div v-for="([term, def]) in glossary" :key="term" class="rounded-xl border border-line bg-surface px-4 py-3">
        <dt class="text-sm font-medium text-brand-ink">{{ term }}</dt>
        <dd class="mt-0.5 text-sm text-muted">{{ def }}</dd>
      </div>
    </dl>

    <div class="mt-10 rounded-xl2 bg-brand p-6 text-center text-white">
      <h3 class="h-display text-xl font-semibold">Prêt à te lancer ?</h3>
      <p class="mt-1 text-white/80">Connecte un compte, crée ton premier plan. On te guide pas à pas.</p>
      <button class="btn mt-4 bg-white text-brand hover:bg-white/90" @click="router.push({ name: 'strategy-new' })">
        Créer un plan d'épargne
      </button>
    </div>

    <p class="mt-6 text-center text-xs text-muted">
      ⚠️ Investir comporte un risque de perte en capital. Les performances passées ne préjugent pas des performances futures.
    </p>
  </div>
</template>
