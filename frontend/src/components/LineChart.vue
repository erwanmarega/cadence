<script setup>

import { computed, ref } from "vue";

const props = defineProps({
  points: { type: Array, default: () => [] },
  quote: { type: String, default: "EUR" },
  height: { type: Number, default: 220 },
});

const W = 800;
const H = computed(() => props.height);
const PAD = { t: 16, r: 16, b: 24, l: 48 };

const valuePts = computed(() => props.points.filter((p) => p.value !== null && p.value !== undefined));

const bounds = computed(() => {
  const vals = [];
  for (const p of props.points) {
    if (p.invested != null) vals.push(p.invested);
    if (p.value != null) vals.push(p.value);
  }
  const max = vals.length ? Math.max(...vals) : 1;
  return { min: 0, max: max * 1.1 || 1 };
});

function x(i, total) {
  const span = W - PAD.l - PAD.r;
  return PAD.l + (total <= 1 ? span / 2 : (i / (total - 1)) * span);
}
function y(v) {
  const span = H.value - PAD.t - PAD.b;
  const { min, max } = bounds.value;
  return PAD.t + span - ((v - min) / (max - min || 1)) * span;
}

function linePath(key) {
  const pts = props.points
    .map((p, i) => ({ i, v: p[key] }))
    .filter((p) => p.v !== null && p.v !== undefined);
  if (!pts.length) return "";
  return pts.map((p, k) => `${k ? "L" : "M"}${x(p.i, props.points.length).toFixed(1)} ${y(p.v).toFixed(1)}`).join(" ");
}

const valuePath = computed(() => linePath("value"));
const investedPath = computed(() => linePath("invested"));
const areaPath = computed(() => {
  const pts = props.points
    .map((p, i) => ({ i, v: p.value }))
    .filter((p) => p.v !== null && p.v !== undefined);
  if (!pts.length) return "";
  const top = pts.map((p, k) => `${k ? "L" : "M"}${x(p.i, props.points.length).toFixed(1)} ${y(p.v).toFixed(1)}`).join(" ");
  const x0 = x(pts[0].i, props.points.length).toFixed(1);
  const x1 = x(pts[pts.length - 1].i, props.points.length).toFixed(1);
  const base = (H.value - PAD.b).toFixed(1);
  return `${top} L${x1} ${base} L${x0} ${base} Z`;
});

const lastValue = computed(() => (valuePts.value.length ? valuePts.value[valuePts.value.length - 1] : null));
const lastInvested = computed(() => {
  const inv = props.points.filter((p) => p.invested != null);
  return inv.length ? inv[inv.length - 1] : null;
});


const hover = ref(null);
function onMove(e) {
  if (!props.points.length) return;
  const svg = e.currentTarget;
  const rect = svg.getBoundingClientRect();
  const px = ((e.clientX - rect.left) / rect.width) * W;
  const span = W - PAD.l - PAD.r;
  let idx = Math.round(((px - PAD.l) / span) * (props.points.length - 1));
  idx = Math.max(0, Math.min(props.points.length - 1, idx));
  hover.value = idx;
}
function onLeave() { hover.value = null; }

const hoverPoint = computed(() => (hover.value !== null ? props.points[hover.value] : null));

function fmt(n) {
  if (n == null) return "—";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: props.quote, maximumFractionDigits: 0 }).format(n);
}
function fmtDate(d) {
  return new Date(d).toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
}
const yTicks = computed(() => {
  const { max } = bounds.value;
  return [0, max / 2, max].map((v) => ({ v, y: y(v) }));
});
</script>

<template>
  <div>
    <div class="mb-3 flex items-center gap-4 text-xs">
      <span class="flex items-center gap-1.5"><span class="h-2 w-3 rounded-sm bg-brand"></span> Valeur</span>
      <span class="flex items-center gap-1.5"><span class="h-0 w-3 border-t-2 border-dashed border-muted"></span> Investi</span>
    </div>
    <svg :viewBox="`0 0 ${W} ${H}`" class="w-full" :style="{ height: H + 'px' }"
         @mousemove="onMove" @mouseleave="onLeave">
      <defs>
        <linearGradient id="valArea" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="var(--color-brand)" stop-opacity="0.22" />
          <stop offset="100%" stop-color="var(--color-brand)" stop-opacity="0" />
        </linearGradient>
      </defs>


      <g>
        <line v-for="t in yTicks" :key="'g'+t.v" :x1="PAD.l" :x2="W - PAD.r" :y1="t.y" :y2="t.y"
              stroke="var(--color-line)" stroke-width="1" />
        <text v-for="t in yTicks" :key="'l'+t.v" :x="PAD.l - 8" :y="t.y + 3" text-anchor="end"
              font-size="11" fill="var(--color-muted)">{{ fmt(t.v) }}</text>
      </g>

      <path :d="areaPath" fill="url(#valArea)" />
      <path :d="investedPath" fill="none" stroke="var(--color-muted)" stroke-width="2"
            stroke-dasharray="5 5" />
      <path :d="valuePath" fill="none" stroke="var(--color-brand)" stroke-width="2.5" />


      <circle v-if="lastValue" :cx="x(points.length - 1, points.length)" :cy="y(lastValue.value)"
              r="4" fill="var(--color-brand)" stroke="white" stroke-width="2" />


      <g v-if="hoverPoint">
        <line :x1="x(hover, points.length)" :x2="x(hover, points.length)" :y1="PAD.t" :y2="H - PAD.b"
              stroke="var(--color-line-strong)" stroke-width="1" />
        <circle v-if="hoverPoint.value != null" :cx="x(hover, points.length)" :cy="y(hoverPoint.value)"
                r="4" fill="var(--color-brand)" stroke="white" stroke-width="2" />
      </g>
    </svg>

    <div v-if="hoverPoint" class="mt-1 flex justify-between text-xs text-muted">
      <span>{{ fmtDate(hoverPoint.date) }}</span>
      <span>Valeur <strong class="text-brand">{{ fmt(hoverPoint.value) }}</strong> · Investi {{ fmt(hoverPoint.invested) }}</span>
    </div>
    <div v-else-if="lastValue" class="mt-1 flex justify-between text-xs text-muted">
      <span>{{ fmtDate(points[0].date) }} → aujourd'hui</span>
      <span>Valeur <strong class="text-brand">{{ fmt(lastValue.value) }}</strong> · Investi {{ fmt(lastInvested?.invested) }}</span>
    </div>
  </div>
</template>
