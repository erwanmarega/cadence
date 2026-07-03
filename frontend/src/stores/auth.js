import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { supabase } from "../lib/supabase";


const MODE_KEY = "cadence_mode";

export const useAuthStore = defineStore("auth", () => {
  const user = ref(null);
  const mode = ref(localStorage.getItem(MODE_KEY) || null);
  const ready = ref(false);

  const isAuthenticated = computed(() => !!user.value);
  const isBeginner = computed(() => mode.value === "beginner");

  const onboarded = computed(() => mode.value === "beginner" || mode.value === "advanced");
  const fullName = computed(() => {
    const m = user.value?.user_metadata || {};
    return [m.first_name, m.last_name].filter(Boolean).join(" ") || m.full_name || "";
  });

  async function init() {
    const { data } = await supabase.auth.getSession();
    setSession(data.session);
    supabase.auth.onAuthStateChange((_event, session) => setSession(session));
    ready.value = true;
  }

  function setSession(session) {
    user.value = session?.user || null;
    const metaMode = user.value?.user_metadata?.mode;
    if (metaMode) {
      mode.value = metaMode;
      localStorage.setItem(MODE_KEY, metaMode);
    }
  }

  async function signIn(email, password) {
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw new Error(error.message);
  }

  async function signUp(email, password) {
    const { error } = await supabase.auth.signUp({ email, password });
    if (error) throw new Error(error.message);
  }

  async function signInWithGoogle() {


    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: window.location.origin },
    });
    if (error) throw new Error(error.message);
  }

  async function signOut() {
    await supabase.auth.signOut();
    user.value = null;
  }

  async function setMode(newMode) {
    mode.value = newMode;
    localStorage.setItem(MODE_KEY, newMode);

    if (user.value) {
      await supabase.auth.updateUser({ data: { mode: newMode } });
    }
  }

  async function setProfile(firstName, lastName) {
    const first_name = firstName.trim();
    const last_name = lastName.trim();
    const { data, error } = await supabase.auth.updateUser({
      data: { first_name, last_name, full_name: `${first_name} ${last_name}`.trim() },
    });
    if (error) throw new Error(error.message);
    if (data?.user) user.value = data.user;
  }

  return {
    user, mode, ready,
    isAuthenticated, isBeginner, onboarded, fullName,
    init, signIn, signUp, signInWithGoogle, signOut, setMode, setProfile,
  };
});
