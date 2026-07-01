# Cadence — bot d'épargne crypto automatique (DCA)

## Vision du produit

Cadence est une application qui permet à des particuliers d'investir
automatiquement un montant fixe en cryptomonnaie à intervalle régulier
(Dollar-Cost Averaging), sans avoir à surveiller les marchés.

Positionnement : une appli d'épargne automatique, pas une plateforme de
trading. L'inspiration est plus proche d'un virement automatique vers un
livret d'épargne que d'un terminal de trading façon 3Commas ou
Cryptohopper. Une seule fonctionnalité (le DCA), faite simplement et bien,
plutôt qu'un empilement de bots (grid, arbitrage, futures...).

Le marché du bot de trading crypto est déjà occupé par des acteurs établis
(3Commas, Cryptohopper, Bitsgap, Pionex...) qui ciblent des traders actifs
avec des outils denses et multi-fonctions. La niche de Cadence : les
particuliers qui veulent juste épargner en crypto sans rien comprendre au
trading, et qui sont aujourd'hui mal servis par des outils trop complexes
pour eux.

## Public cible

Deux profils, traités différemment dès l'onboarding :

- **Débutant** : ne connaît rien ou presque à la crypto / au DCA. A besoin
  d'explications contextuelles, d'un vocabulaire vulgarisé, d'un parcours
  guidé pas à pas.
- **Confirmé** : connaît déjà les bases (exchanges, API, DCA). Veut une
  interface dense, rapide, sans friction pédagogique.

Le profil est déterminé par un court questionnaire à l'inscription
(1-2 minutes). Le résultat détermine quelle interface est affichée
ensuite (voir "Onboarding adaptatif" ci-dessous).

## Fonctionnalité cœur : le DCA

- L'utilisateur définit un montant fixe et un intervalle (ex : 20€ chaque
  semaine).
- Le bot achète automatiquement la/les cryptomonnaies choisies à cet
  intervalle, peu importe le prix du marché.
- Pas de stratégie complexe (pas de grid, pas d'arbitrage, pas de
  futures/levier) — DCA simple, éventuellement DCA conditionnel sur baisse
  de prix dans une version ultérieure, mais hors scope du MVP.

## Connexion aux comptes utilisateurs

- Le bot ne détient jamais les fonds (non-custodial). L'argent reste sur
  l'exchange de l'utilisateur.
- Connexion via clé API exchange, avec permissions limitées au trading
  (jamais de permission de retrait). Les clés sont chiffrées en base de
  données, jamais stockées en clair.
- Exchanges ciblés au lancement : Kraken et Coinbase (API publiques et
  documentées, adaptées à un usage particulier). Binance à évaluer selon
  la zone géographique des utilisateurs.
- Exclu : Trade Republic et les néobrokers actions grand public
  (Boursorama, Trading 212...) — pas d'API publique disponible, usage non
  autorisé par leurs CGU.

## Onboarding adaptatif

1. Questionnaire court à l'inscription : niveau de connaissance crypto,
   préférence d'accompagnement (explications à chaque étape ou accès
   direct).
2. Selon la réponse :
   - **Mode débutant** : tooltips et explications contextuelles à chaque
     écran, vocabulaire simple ("tu vas mettre X€ chaque semaine" plutôt
     que "configurer l'intervalle DCA"), éventuellement une simulation
     avant de connecter un vrai compte exchange.
   - **Mode confirmé** : interface plus dense, accès direct aux réglages
     fins (choix d'indicateurs de déclenchement, plusieurs cryptos en
     parallèle), pas de pop-ups explicatifs.
3. Le mode choisi doit rester modifiable à tout moment dans les
   paramètres (un débutant devenant plus à l'aise doit pouvoir basculer).

## Écrans principaux (cible)

- Tableau de bord : valeur du portefeuille, performance, statut du bot
  (actif/en pause), positions ouvertes.
- Configuration de la stratégie : montant, intervalle, cryptos ciblées,
  niveau de risque.
- Historique des trades : chaque achat exécuté par le bot, daté, avec le
  prix d'exécution.
- Connexion exchange : instructions claires pour générer une clé API avec
  les bonnes permissions (trading oui, retrait non).
- Bouton pause/arrêt d'urgence toujours visible.

## Assistant éducatif et informatif (phase 2 du MVP)

En plus de l'exécution automatique du DCA, Cadence propose un assistant
qui aide l'utilisateur à comprendre le marché — sans jamais lui dire quoi
faire. Distinction stricte à respecter dans toute génération de contenu
ou de code lié à cette fonctionnalité :

- **Autorisé (information / éducation)** :
  - expliquer des concepts (DCA, volatilité, lecture d'un graphique de
    prix, ce qu'est une crypto donnée...).
  - afficher l'évolution des prix en temps réel ou sur une période
    (ex : "le Bitcoin a baissé de 5% sur 7 jours").
  - donner du contexte factuel et neutre sur un mouvement de marché.
- **Interdit (conseil en investissement réglementé)** :
  - recommander un montant, un timing, ou un actif à acheter/vendre de
    façon personnalisée ("tu devrais acheter maintenant", "investis X% de
    ton épargne en Bitcoin").
  - toute formulation qui transforme une info factuelle en directive
    d'action pour l'utilisateur.

Règle de formulation à appliquer partout dans l'assistant : présenter ce
qui se passe sur le marché, jamais ce que l'utilisateur devrait faire en
réaction. En cas de doute sur une formulation, pencher vers le ton
neutre/informatif plutôt que vers le conseil.

Si le produit évolue un jour vers du conseil personnalisé réel (ex :
recommandations adaptées à la situation financière de l'utilisateur),
cela nécessite un statut réglementé (en France, agrément AMF / statut de
CIF ou équivalent) et sort du cadre actuel du projet.

## Roadmap : actions boursières (phase ultérieure, hors MVP)

Le MVP de Cadence se concentre exclusivement sur la cryptomonnaie. Une
extension aux actions boursières est envisagée dans une phase
ultérieure, mais n'est pas dans le scope actuel. Points à retravailler le
moment venu :
- les brokers actions grand public n'ont pour la plupart pas d'API
  publique (Trade Republic, Boursorama, Trading 212...) — voir options
  comme Interactive Brokers ou DEGIRO, qui n'ont pas encore été
  validées.
- l'assistant éducatif/informatif décrit ci-dessus devra suivre la même
  distinction stricte information/conseil une fois étendu aux actions.

- Ne jamais promettre ou laisser entendre un rendement garanti. Le bot
  exécute une stratégie, il ne prédit pas le marché.
- Toujours afficher clairement les risques (perte en capital possible,
  notamment en tendance baissière prolongée).
- Toute communication marketing doit rester honnête sur les limites du
  DCA (sous-performance possible en marché fortement haussier comparé à
  un investissement en une fois).

## Stack technique

- Backend : Python avec FastAPI.
- Frontend : Vue.js.
- Base de données et auth : Supabase (PostgreSQL).
- Connexion exchanges : via `ccxt` ou les SDK officiels (Kraken, Coinbase).
- Stockage des clés API exchange : chiffrement obligatoire côté
  applicatif (FastAPI) avant écriture en base, jamais en clair, même dans
  Supabase. Ne pas compter uniquement sur la sécurité de la base.
- Row Level Security (RLS) Supabase à configurer et tester rigoureusement
  pour isoler les données par utilisateur (clés API, configuration de
  stratégie, historique de trades).
- Tâches planifiées (exécution du DCA à intervalle régulier) : à définir
  entre cron jobs simples au démarrage et un outil dédié (Celery,
  APScheduler) si la charge le justifie.

## Pricing (repère marché, à ajuster)

Les concurrents établis pratiquent des tarifs entre 15 et 140$/mois selon
les fonctionnalités. Cadence visant une fonctionnalité unique et un
public différent, un positionnement prix d'entrée (10-30€/mois) ou
freemium est plus cohérent pour démarrer, quitte à ajuster une fois une
base d'utilisateurs établie.

## Notes pour Claude

- Toujours garder la simplicité comme principe directeur : avant d'ajouter
  une fonctionnalité, se demander si elle dessert le positionnement
  "épargne simple" ou si elle rapproche le produit des plateformes de
  trading classiques (ce qui irait à l'encontre du positionnement choisi).
- Respecter strictement la distinction entre mode débutant et mode
  confirmé dans toute interface générée.
- Ne jamais générer de logique qui donnerait au bot un accès aux retraits
  de fonds sur un compte exchange.