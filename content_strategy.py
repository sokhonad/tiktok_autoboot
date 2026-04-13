"""
content_strategy.py — Planning éditorial hebdomadaire.
Définit le thème du jour, le pool de topics, et l'affiliation associée.
"""

import random
from datetime import datetime
from typing import TypedDict


class DayStrategy(TypedDict):
    theme: str
    affiliation: str
    topics: list[str]
    tone: str
    hashtags: list[str]


# ── Planning par jour de la semaine (0=Lundi … 6=Dimanche) ──────────────────
WEEKLY_PLAN: dict[int, DayStrategy] = {
    0: {  # Lundi — Python & Dev
        "theme": "python_tips",
        "affiliation": "https://bit.ly/python-bootcamp-fr",
        "tone": "éducatif, débutant-friendly",
        "hashtags": ["#python", "#programmation", "#devfr", "#codeurdujour", "#apprendreacoder"],
        "topics": [
            "5 f-strings Python que tu n'utilises pas encore",
            "List comprehensions : propre et rapide",
            "Décorateurs Python expliqués en 60 secondes",
            "Walrus operator := : quand l'utiliser ?",
            "dataclasses vs TypedDict : lequel choisir ?",
            "match/case en Python 3.10 : le switch FR",
            "asyncio expliqué simplement en 60 secondes",
            "pathlib > os.path : pourquoi migrer maintenant",
            "Gestion d'erreurs Pythonique : try/except avancé",
            "Les secrets du module itertools",
        ],
    },
    1: {  # Mardi — IA & LLM
        "theme": "ai_llm",
        "affiliation": "https://bit.ly/cursor-ai-fr",
        "tone": "enthousiaste, axé business et productivité",
        "hashtags": ["#ia", "#intelligenceartificielle", "#llm", "#chatgpt", "#techfr"],
        "topics": [
            "Prompt engineering : 3 techniques qui changent tout",
            "Claude vs GPT-4o : lequel choisir pour coder ?",
            "RAG expliqué en 60 secondes",
            "Fine-tuning vs prompting : quand choisir ?",
            "LangChain en 2025 : vaut-il encore le coup ?",
            "Vector databases : Pinecone vs Chroma vs Weaviate",
            "Agents IA : ce que personne ne te dit",
            "Function calling OpenAI : le guide rapide",
            "Mistral 7B : l'IA FR qui concurrence GPT",
            "Ollama : fais tourner un LLM en local gratuitement",
        ],
    },
    2: {  # Mercredi — DevOps & Cloud
        "theme": "devops_cloud",
        "affiliation": "https://bit.ly/aws-certs-fr",
        "tone": "professionnel, orienté carrière",
        "hashtags": ["#devops", "#cloud", "#docker", "#kubernetes", "#awsfr"],
        "topics": [
            "Docker en 60 secondes : ce que tu dois savoir",
            "GitHub Actions : ton premier CI/CD en 5 minutes",
            "K8s vs Docker Compose : lequel pour ton projet ?",
            "Terraform basics : infra as code pour les nuls",
            "Nginx reverse proxy : config ultime",
            "Secrets management : jamais de clés dans le code",
            "Monitoring avec Grafana + Prometheus : guide rapide",
            "Blue/Green deployment expliqué simplement",
            "AWS Lambda : serverless en 60 secondes",
            "Optimiser ton Dockerfile : 5 best practices",
        ],
    },
    3: {  # Jeudi — Outils & Productivité
        "theme": "tools_productivity",
        "affiliation": "https://bit.ly/notion-affiliate-fr",
        "tone": "hack de productivité, gain de temps concret",
        "hashtags": ["#devtools", "#productivite", "#vscode", "#git", "#techlife"],
        "topics": [
            "5 extensions VSCode qui m'ont sauvé la vie",
            "Git aliases : les commandes que tu devrais avoir",
            "tmux : le terminal multiplexeur qu'il te faut",
            "Zsh + Oh My Zsh : config dev parfaite",
            "Neovim pour les développeurs en 2025",
            "GitHub Copilot vs Cursor : mon vrai avis",
            "Warp terminal : révolution ou hype ?",
            "Obsidian pour les devs : prendre des notes qui servent",
            "Makefile : automatise ton workflow en 5 minutes",
            "HTTPie vs curl : tester une API proprement",
        ],
    },
    4: {  # Vendredi — Cybersécurité
        "theme": "cybersecurity",
        "affiliation": "https://bit.ly/hackthebox-fr",
        "tone": "mystérieux, pédagogique, sensibilisation",
        "hashtags": ["#cybersecurite", "#hacking", "#securite", "#pentest", "#infosec"],
        "topics": [
            "SQL Injection : comprendre pour mieux protéger",
            "OWASP Top 10 : les failles que tout dev doit connaître",
            "JWT : pourquoi ton implémentation est probablement fausse",
            "XSS expliqué en 60 secondes",
            "Password hashing : bcrypt vs argon2",
            "HTTPS : ce que le cadenas ne garantit PAS",
            "Phishing technique : comment les hackers t'attrapent",
            "2FA : toutes les méthodes comparées",
            "Rate limiting : protège ton API en 5 minutes",
            "CVE : comment lire une vulnérabilité de sécurité",
        ],
    },
    5: {  # Samedi — Carrière & Salaires
        "theme": "career_money",
        "affiliation": "https://bit.ly/openclassrooms-fr",
        "tone": "motivant, concret, chiffres réels FR",
        "hashtags": ["#devsalaire", "#carrrierefr", "#freelance", "#recrutement", "#codeurfr"],
        "topics": [
            "Salaires dev en France en 2025 : la vérité",
            "Freelance dev : combien facturer en FR ?",
            "Négocier son salaire : le script exact",
            "Full-stack vs spécialisé : quel impact sur le salaire ?",
            "Remote : comment trouver un job dev en full remote",
            "Portfolio dev : ce qui fait vraiment la différence",
            "LinkedIn pour les devs : 5 trucs qui marchent",
            "De zéro à dev en 12 mois : c'est possible ?",
            "Les technos les mieux payées en France",
            "Senior vs Lead vs Architect : les différences réelles",
        ],
    },
    6: {  # Dimanche — Web & Frontend
        "theme": "web_frontend",
        "affiliation": "https://bit.ly/vercel-fr",
        "tone": "visuel, moderne, orienté résultats",
        "hashtags": ["#react", "#nextjs", "#frontend", "#webdev", "#javascript"],
        "topics": [
            "Next.js 15 : les nouveautés qui changent tout",
            "React Server Components : enfin compris",
            "Tailwind CSS vs CSS Modules : en 2025",
            "TypeScript strict mode : pourquoi l'activer",
            "Zustand vs Redux : state management en 2025",
            "Web Performance : 3 quick wins pour ton score Lighthouse",
            "shadcn/ui : le design system que tout le monde copie",
            "tRPC : API type-safe sans effort",
            "Turbopack vs Vite : le vrai benchmark",
            "Framer Motion : 3 animations qui impressionnent",
        ],
    },
}


def get_today_strategy() -> DayStrategy:
    """Retourne la stratégie éditoriale du jour courant."""
    weekday = datetime.now().weekday()  # 0=Lundi
    return WEEKLY_PLAN[weekday]


def get_today_topic() -> str:
    """Sélectionne un topic aléatoire parmi ceux du jour."""
    strategy = get_today_strategy()
    return random.choice(strategy["topics"])


def inject_cta(script: dict, strategy: DayStrategy) -> dict:
    """
    Injecte le CTA d'affiliation dans le champ 'cta' du script généré.
    Ajoute aussi les hashtags du jour.
    """
    affiliation_cta = (
        f"🔗 Lien en bio pour aller plus loin ! {strategy['affiliation']}"
    )
    script["cta"] = script.get("cta", "") + f"\n{affiliation_cta}"

    # Fusionne les hashtags du script avec ceux du thème du jour
    existing_tags = script.get("hashtags", [])
    merged = list(dict.fromkeys(existing_tags + strategy["hashtags"]))  # déduplique
    script["hashtags"] = merged[:30]  # TikTok limite à 30 hashtags

    return script
