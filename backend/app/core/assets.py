"""Liste curée d'actifs — source unique côté backend.

Positionnement Cadence : épargne simple, pas terminal de trading. Par défaut
on propose de grands actifs disponibles en EUR sur Kraken et Coinbase. Le mode
confirmé peut demander la liste complète via /market/bases (dynamique ccxt).
"""

CURATED_BASES = [
    "BTC", "ETH", "SOL", "XRP", "ADA", "DOT", "LINK", "AVAX",
    "DOGE", "ATOM", "LTC", "XLM", "BCH", "UNI", "AAVE", "ALGO",
]
