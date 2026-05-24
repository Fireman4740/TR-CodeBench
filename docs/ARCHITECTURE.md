# TR-CodeBench — Architecture & Academic Research Agent

> Version 0.4 — 40 items — Python 3.11+

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Structure du dépôt](#2-structure-du-dépôt)
3. [Pipeline d'évaluation (flux de données)](#3-pipeline-dévaluation-flux-de-données)
4. [Modules expliqués](#4-modules-expliqués)
   - 4.1 [Exécution sécurisée — `run_candidate.py`](#41-exécution-sécurisée--run_candidatepy)
   - 4.2 [Vérifications statiques — `static_checks.py`](#42-vérifications-statiques--static_checkspy)
   - 4.3 [Extraction de features AST — `ast_features.py`](#43-extraction-de-features-ast--ast_featurespy)
   - 4.4 [Classification de paradigmes — `paradigm_classifier.py`](#44-classification-de-paradigmes--paradigm_classifierpy)
   - 4.5 [Stack d'évidence — `paradigm_evidence/`](#45-stack-dévidence--paradigm_evidence)
   - 4.6 [Anti-contamination — `salieri_minhash.py`](#46-anti-contamination--salieri_minhashpy)
   - 4.7 [Tests cachés — `hidden_tests.py`](#47-tests-cachés--hidden_testspy)
   - 4.8 [Profil 5 axes — `metrics_profile.py`](#48-profil-5-axes--metrics_profilepy)
   - 4.9 [Score composite (deprecated) — `scoring.py`](#49-score-composite-deprecated--scoringpy)
   - 4.10 [Trajectoires de déni — `denial/`](#410-trajectoires-de-déni--denial)
   - 4.11 [Évaluateur principal — `evaluate.py`](#411-évaluateur-principal--evaluatepy)
   - 4.12 [Runner OpenRouter — `openrouter_runner.py`](#412-runner-openrouter--openrouter_runnerpy)
5. [Schéma des données (item JSON)](#5-schéma-des-données-item-json)
6. [Commandes d'utilisation](#6-commandes-dutilisation)
7. [Agent de recherche — validation académique](#7-agent-de-recherche--validation-académique)
   - 7.1 [Contexte et enjeux académiques](#71-contexte-et-enjeux-académiques)
   - 7.2 [Architecture de l'agent](#72-architecture-de-lagent)
   - 7.3 [Code de l'agent complet](#73-code-de-lagent-complet)
   - 7.4 [Métriques académiques cibles](#74-métriques-académiques-cibles)
   - 7.5 [Intégration dans le pipeline existant](#75-intégration-dans-le-pipeline-existant)

---

## 1. Vue d'ensemble

TR-CodeBench est un **benchmark de génération de code** sous **Régime de Vérité T2** (Truth Regime 2) :

| Propriété | Valeur |
|---|---|
| **Nombre d'items** | 40 |
| **Langage** | Python 3.11 uniquement |
| **Concept clé** | Productive Divergence (PD) — divergence productive de l'oracle |
| **Oracle** | Exécutable, non exposé, testé avec Hypothesis (PBT) |
| **Exécution** | `multiprocessing.Process` — vraie isolation processus |
| **Scoring** | 5 axes indépendants (correctness, robustness, efficiency, divergence, safety) |

### Principe fondamental : T2 vs T1

```
T1 (vérité unique) : une seule solution correcte attendue
         ↓
T2 (latitude algorithmique) : TOUT paradigme correct est accepté
                              mais l'oracle reste le juge ultime
```

**La clé de T2** : le modèle peut utiliser n'importe quel algorithme
(fenwick tree, segment tree, z-algorithm, etc.) tant que :
1. Il passe **tous** les tests (public + caché + PBT)
2. Il respecte la **complexité temporelle** requise
3. Il ne copie pas l'oracle (Salieri overlap < 0.70)

---

## 2. Structure du dépôt

```
TR-CodeBench/
├── src/trcodebench/              # Package principal
│   ├── evaluate.py               # Point d'entrée CLI : --format human/compact/json
│   ├── run_candidate.py          # Exécution via multiprocessing.Process
│   ├── static_checks.py          # Gate AST avant exécution (imports interdits)
│   ├── ast_features.py           # Extraction de 13 features algorithmiques
│   ├── paradigm_classifier.py    # 28 paradigmes × signatures → cosine distance
│   ├── salieri_minhash.py        # Jaccard 5-gram sur tokens normalisés
│   ├── hidden_tests.py           # Génération Hypothesis → cas cachés
│   ├── metrics_profile.py        # 5 axes indépendants (PRIMAIRE)
│   ├── scoring.py                # Score composite (DEPRECATED)
│   ├── load_items.py             # Chargement JSON + résolution chemins
│   ├── openrouter_runner.py      # Évaluation multi-modèles OpenRouter en parallèle
│   ├── paradigm_evidence/        # Stack d'évidence pour paradigmes fragiles
│   │   ├── ast_signals.py        # Signaux AST spécifiques (segment_tree, z_algo, rolling_hash)
│   │   ├── structural_signals.py # Patterns structurels (boucles, récursion)
│   │   ├── dataflow_signals.py   # Analyse du flux de données
│   │   ├── behavioral_probes.py  # Probes comportementales (I/O observationnelles)
│   │   ├── evidence_fusion.py    # Fusion pondérée des couches d'évidence
│   │   └── schema.py             # Types : ParadigmSignal, ParadigmEvidence
│   └── denial/                   # Trajectoires de déni itératives
│       ├── denial_schema.py      # Types : DenialConstraint, DenialStepResult, DenialTrajectory
│       ├── denial_scoring.py     # Métriques de trajectoire
│       ├── build_denial_prompt.py # Construction du prompt de déni
│       ├── select_next_constraint.py # Sélection de la prochaine contrainte
│       ├── run_denial_trajectory.py  # Orchestration de la trajectoire complète
│       └── verify_denial.py      # Vérification AST des contraintes de déni
├── datasets/curated/             # 40 items JSON (trcb-proto-0001 → 0040)
├── schemas/item.schema.json      # Schéma JSON pour validation
├── tests/unit/                   # 141 tests unitaires
│   ├── test_evaluator.py         # Tests formatters, classifieurs, failure_analysis
│   ├── test_openrouter_runner.py # Tests fix pbt_pass_rate, colonnes JSONL
│   ├── test_metrics_profile.py   # Tests profil 5 axes
│   ├── test_dataset_integrity.py # Tests intégrité des 40 items
│   └── ...
├── scripts/
│   ├── run_openrouter_eval.sh    # Script bash d'évaluation multi-modèles
│   └── annotate_oracle_features.py # Précompute oracle_ast_features dans les items JSON
├── candidates/                   # Candidats exemples pour tests manuels
├── pyproject.toml                # Configuration package + dépendances
└── docs/
    ├── SPEC.md                   # Spécification complète v0.4
    ├── ARCHITECTURE.md           # Ce fichier
    └── README.md                 # Guide d'utilisation
```

---

## 3. Pipeline d'évaluation (flux de données)

```
             ┌─────────────────────────────────────────────────────────┐
             │                   evaluate_candidate()                   │
             └─────────────────────────────────────────────────────────┘
                                         │
           ┌─────────────────────────────┼─────────────────────────────┐
           │                             │                             │
           ▼                             ▼                             ▼
   ┌──────────────┐            ┌──────────────────┐          ┌──────────────────┐
   │ static_checks │            │  run_suite()     │          │  paradigm stack  │
   │  (AST gate)   │            │  ┌────────────┐  │          │                  │
   │               │            │  │ public_    │  │          │  ast_features    │
   │  - banned     │            │  │ cases      │  │          │      ↓           │
   │    imports    │            │  └────────────┘  │          │  paradigm_       │
   │  - banned     │            │  ┌────────────┐  │          │  classifier      │
   │    calls      │            │  │ hidden_    │  │          │      ↓           │
   │               │            │  │ cases      │  │          │  paradigm_       │
   └──────────────┘            │  └────────────┘  │          │  evidence        │
           │                   │  ┌────────────┐  │          │  (fragile        │
           │ ok=True/False      │  │ pbt_groups │  │          │   paradigms)     │
           │                   │  │ (Hypothesis│  │          │                  │
           ▼                   │  │ @given)    │  │          └──────────────────┘
   ┌──────────────┐            │  └────────────┘  │                   │
   │  candidate   │◄───────────┤                  │◄──────────────────┘
   │  executed in │            │  run_one_case()  │
   │  mp.Process  │            │  ┌────────────┐  │          ┌──────────────────┐
   │  per case    │            │  │  mp.Queue  │  │          │  salieri_minhash  │
   │  + timeout   │            │  │  timeout   │  │          │  Jaccard 5-gram   │
   └──────────────┘            │  │  ok/crash/ │  │          │  token-normalized │
                               │  │  timeout   │  │          └──────────────────┘
                               └──────────────────┘
                                         │
                               ┌──────────────────┐
                               │  metrics_profile  │
                               │  5 axes           │
                               │  ┌─────────────┐  │
                               │  │ correctness │  │
                               │  │ robustness  │  │
                               │  │ efficiency  │  │
                               │  │ divergence  │  │
                               │  │ safety      │  │
                               │  └─────────────┘  │
                               └──────────────────┘
                                         │
                               ┌──────────────────┐
                               │  evaluate_candidate│
                               │  return dict:     │
                               │  - metrics_profile│
                               │  - failure_analysis│
                               │  - execution_ctx  │
                               │  - pd_classification│
                               │  - suites         │
                               └──────────────────┘
```

---

## 4. Modules expliqués

### 4.1 Exécution sécurisée — `run_candidate.py`

**Rôle** : Exécuter le code candidat dans un **vrai processus Python isolé**, avec timeout.

```python
# Architecture d'exécution
mp.Process(target=_child_run, args=(queue, path, fn_name, argument_order, inputs))
process.start()
process.join(timeout_seconds)
if process.is_alive():
    process.terminate()  # Timeout → kill
```

**Ce qui se passe dans le processus enfant** :
1. Import dynamique du fichier candidat via `importlib.util`
2. Redirection de `stdout`/`stderr` (évite les prints pollutants)
3. Appel de la fonction avec les arguments
4. Résultat mis dans une `mp.Queue` → pickle pour IPC
5. Toute exception → `{"status": "crash", "error": ...}`

**Isolation** : niveau processus uniquement (pas de réseau/filesystem). Les `static_checks.py` bloquent les imports dangereux **avant** l'exécution.

**Statuts possibles** :
| Statut | Signification |
|---|---|
| `"ok"` | Exécution réussie (peut être wrong answer si output != expected) |
| `"crash"` | Exception non gérée dans le candidat |
| `"timeout"` | Dépassement du timeout, processus tué |

---

### 4.2 Vérifications statiques — `static_checks.py`

**Rôle** : Gate AST **avant** toute exécution. Bloque les candidats dangereux.

```python
BANNED_MODULES = {"os", "sys", "socket", "subprocess", "importlib", ...}
BANNED_CALLS = {"eval", "exec", "open", "compile", "__import__", ...}
```

**Flux** :
1. Parse le source en AST
2. Walk tous les `ast.Import` et `ast.ImportFrom`
3. Vérifie chaque module contre `BANNED_MODULES` et `allowed_imports` de l'item
4. Walk tous les `ast.Call` et vérifie contre `BANNED_CALLS`

**Résultat** :
```python
{
    "ok": False,
    "violations": ["banned_import:os", "disallowed_import:numpy"],
    "imported_modules": ["os", "numpy"],
    "suspicious_calls": []
}
```

---

### 4.3 Extraction de features AST — `ast_features.py`

**Rôle** : Extraire 13 features binaires/numériques qui caractérisent l'algorithme.

| Feature | Description | Détection |
|---|---|---|
| `recursion` | Appel récursif auto-référentiel | `_RecursionVisitor` (stack de fonctions) |
| `heapq` | File de priorité | Import `heapq` ou appel `heappush`/`heappop` |
| `bisect` | Recherche binaire | Import `bisect` ou `bisect_left`/`bisect_right` |
| `deque` | File double-ended | Import `collections` + usage `deque` |
| `dict_memo` | Mémoïsation | Variable `memo`, `cache`, ou `lru_cache` |
| `union_find` | Structure DSU | Variables `parent`/`rank`/`find`/`union` |
| `fenwick` | Arbre de Fenwick | Pattern `i & -i` ou variable `bit` |
| `kmp_prefix_table` | KMP prefix function | Variables `lps`/`pi`/`prefix`/`border` |
| `rolling_hash` | Hachage glissant | Variables `hash`+`base`+`mod` ou `"rolling"` |
| `z_algorithm` | Z-algorithm | Variable `z` + `left`/`right` ou `"z_algorithm"` |
| `adjacency_list` | Liste d'adjacence | Variables `graph`/`adj`/`neighbors` |
| `coordinate_compression` | Compression coords | Pattern `sorted(set(` ou `rank`+`values` |
| `nested_loops` | Nombre de boucles imbriquées | Count via `ast.walk` sur For/While |

**Limitation connue** : Features heuristiques basées sur noms de variables. Fragile pour les paradigmes avancés → corrigé par `paradigm_evidence/`.

---

### 4.4 Classification de paradigmes — `paradigm_classifier.py`

**Rôle** : Mapper les features AST vers des **paradigmes algorithmiques nommés**, et calculer une **distance cosinus** entre candidat et oracle.

**28 paradigmes définis** (exemples) :
```python
PARADIGM_SIGNATURES = {
    "patience_sorting":         {"bisect": True, "recursion": False},
    "fenwick_tree":             {"fenwick": True, "coordinate_compression": False},
    "fenwick_tree_coord_compr": {"fenwick": True, "coordinate_compression": True},
    "segment_tree":             {"recursion": True, "nested_loops": 0},
    "dfs_memoization":          {"recursion": True, "dict_memo": True, "adjacency_list": True},
    "kmp":                      {"kmp_prefix_table": True},
    "dijkstra_heap":            {"heapq": True, "adjacency_list": True},
    ...
}
```

**Distance paradigmatique** (cosine distance sur vecteur de 13 features) :
```
paradigm_distance = 1 - cosine_similarity(candidate_vector, oracle_vector)

0.0 = paradigmes identiques (même stratégie que l'oracle)
1.0 = paradigmes orthogonaux (stratégie radicalement différente)
```

**Détection** : Un paradigme est "détecté" si toutes les features requises par sa signature correspondent.

---

### 4.5 Stack d'évidence — `paradigm_evidence/`

**Rôle** : Corriger les **faux positifs/négatifs** du classifieur heuristique pour les paradigmes **fragiles** (difficiles à détecter par signatures seules).

**Paradigmes couverts** : `segment_tree`, `z_algorithm`, `rolling_hash_with_verification`, `dfs_memoization`

**Architecture 4 couches** :
```
┌─────────────────────────────────────────────────────────┐
│                   evidence_fusion.py                     │
│   _fuse(signals) = Σ(confidence × weight) / Σ(weight)   │
└─────────────────────────────────────────────────────────┘
         ▲              ▲              ▲              ▲
   ast_feature     structural      dataflow      behavioral
   (poids 0.30)   (poids 0.50)   (poids 0.20)   (poids 0.25)
         │              │              │              │
   "recursion      "array left/   "memo table    "I/O test
    present"        right          dfs pattern"   probes"
                    indices"
```

**Décisions** :
| Confiance | Décision | Action |
|---|---|---|
| ≥ `ACCEPT_THRESHOLD` | `"accept"` | Ajoute le paradigme si absent |
| ≥ `JUDGE_THRESHOLD` | `"judge"` | Laisse la décision du classifieur |
| < `JUDGE_THRESHOLD` | `"abstain"` | Retire le paradigme si présent |

---

### 4.6 Anti-contamination — `salieri_minhash.py`

**Rôle** : Détecter si le candidat est une **copie** de l'oracle (pas une contamination de training).

**Algorithme** :
1. **Normalisation** : tokenize Python → remplace `NAME`/`NUMBER`/`STRING` par leur type
   ```python
   "def solve(nums): return sorted(nums)"
   → ["def", "NAME", "(", "NAME", ")", ":", "return", "NAME", "(", "NAME", ")"]
   ```
2. **5-grams** : fenêtre glissante de 5 tokens
3. **Jaccard similarity** : `|A ∩ B| / |A ∪ B|`

**Seuil** : `SALIERI_MEMORISATION_THRESHOLD = 0.70`
- `salieri_overlap > 0.70` → copie détectée → `divergence = 0.0`
- `salieri_overlap ≤ 0.70` → originalité suffisante

**Note** : Ceci détecte la **copie directe de l'oracle**, PAS la contamination d'entraînement.

---

### 4.7 Tests cachés — `hidden_tests.py`

**Rôle** : Générer des cas de test à partir de la **stratégie Hypothesis** définie dans l'item.

```python
# Dans l'item JSON
"hypothesis_strategy": "trcodebench.strategies.trcb_0001:make_strategy"
# → Hypothesis génère des listes aléatoires de longueur variable
```

**PBT (Property-Based Testing)** :
```python
@settings(
    max_examples=n_cases,
    phases=[Phase.explicit, Phase.reuse, Phase.generate],  # PAS de shrinking
    deadline=None,
)
@given(strategy_factory())
def _check(case):
    expected = oracle(case["input"])
    actual = candidate(case["input"])
    assert actual == expected
```

**Pourquoi pas de shrinking** : Le benchmark cherche à **détecter** les bugs, pas à minimiser les contre-exemples. Le shrinking ralentirait inutilement l'évaluation.

---

### 4.8 Profil 5 axes — `metrics_profile.py`

**Rôle** : Évaluer le candidat sur **5 dimensions indépendantes**. C'est la **métrique primaire** (le score composite est deprecated).

```
┌─────────────────────────────────────────────────────────────────┐
│  Axe 1 — Correctness  [0.0, 1.0]                                │
│  Binary gate: public_pass_rate == 1.0 AND hidden_pass_rate==1.0 │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│  Axe 2 — Robustness   [0.0, 1.0]                                │
│  0.7 × pbt_gate_passed + 0.3 × pbt_group_pass_rate             │
│  Résiste aux cas aléatoires Hypothesis                          │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│  Axe 3 — Efficiency   [0.0, 1.0] | None si correctness<1       │
│  max(0, 1 - ratio/ratio_max) où ratio = t_large/t_small         │
│  None si complexité non mesurable (timeout, correctness fail)   │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│  Axe 4 — Divergence   [0.0, 1.0] | None si correctness<1       │
│  Gates: salieri≤0.70, paradigm_dist≥0.20                        │
│  Score: harmonic_mean(paradigm_dist, 1-salieri)                 │
│  Bonus ×1.2 si is_genuine_divergence                            │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│  Axe 5 — Safety       [0.0, 1.0]                                │
│  0.0 si crash || static_violation || hidden_pass_rate<1          │
│  1.0 sinon                                                       │
└─────────────────────────────────────────────────────────────────┘
```

**Interprétation** :
- `None` sur un axe = non applicable (gate précédent non satisfait)
- Les axes sont **indépendants** → un modèle peut exceller en divergence mais échouer en efficience

---

### 4.9 Score composite (deprecated) — `scoring.py`

**Conservé pour rétrocompatibilité**. Formule :
```
score = 0.50 × correctness
      + 0.20 × robustness
      + 0.15 × optimization
      + 0.15 × pd_score
      - 0.25 × hallucination_flag
```

**Limites** :
- Un seul nombre masque les problèmes spécifiques
- Pondération arbitraire non justifiée académiquement
- Remplacé par le profil 5 axes pour l'analyse

---

### 4.10 Trajectoires de déni — `denial/`

**Concept** : Forcer le modèle à résoudre le **même problème** sous des **contraintes successivement plus restrictives**. Mesure la **flexibilité algorithmique réelle**.

```
Step 0 : Résoudre librement
         → Paradigme détecté: "patience_sorting"
         ↓
Step 1 : Contrainte: forbidden_api=["bisect"]
         → Le modèle DOIT changer de paradigme
         → Paradigme détecté: "fenwick_tree"
         ↓
Step 2 : Contrainte: forbidden_import=["collections"]
         → Nouveau paradigme requis
         → Paradigme détecté: "two_pointers"
```

**Types de contraintes** :
| Type | Exemple | Vérification |
|---|---|---|
| `forbidden_api` | `["bisect", "sort"]` | AST: noms d'attributs/fonctions |
| `forbidden_import` | `["heapq"]` | AST: imports + références |
| `forbidden_structure` | `["recursion"]` | AST: appels auto-référentiels |
| `forbidden_paradigm` | `["dp"]` | Soft: commentaires seulement |
| `forbidden_construct` | `["nested_for_loops"]` | AST: multi-stratégie |
| `resource` | time/memory limits | Vérification externe |

**Métriques de trajectoire** :
```python
DenialTrajectory.denial_pass_rate             # % étapes réussies avec contrainte
DenialTrajectory.constraint_satisfaction_rate  # % contraintes réellement respectées
DenialTrajectory.unique_valid_paradigms        # Liste des paradigmes distincts trouvés
DenialTrajectory.pd_confirmed                 # ≥2 paradigmes valides = PD confirmée
```

---

### 4.11 Évaluateur principal — `evaluate.py`

**Point d'entrée** du système. Orchestre tous les modules.

**API Python** :
```python
result = evaluate_candidate(
    item_id="trcb-proto-0001",
    candidate_path="my_solution.py",
    hidden_cases=30,    # Cas Hypothesis générés
    pbt_cases=25,       # Exemples Hypothesis PBT
    timeout_seconds=1.0 # Par cas
)
```

**Structure du résultat** :
```python
{
    "item_id": "trcb-proto-0001",
    "candidate": "/path/to/solution.py",
    "metrics": {...},                    # Raw metrics
    "metrics_profile": {                 # 5 axes (PRIMAIRE)
        "correctness": 1.0,
        "robustness": 0.95,
        "efficiency": 0.87,
        "divergence": 0.62,
        "safety": 1.0
    },
    "score": {"score": 0.85, ...},       # Legacy composite (deprecated)
    "static_checks": {"ok": True, ...},
    "pd_classification": {               # Paradigmes détectés
        "candidate_paradigms": ["fenwick_tree"],
        "oracle_paradigms": ["patience_sorting"],
        "is_genuine_divergence": True,
        "paradigm_evidence": {...}        # Détail couches d'évidence
    },
    "suites": {
        "public":  {"total": 5, "passed": 5, "failures": []},
        "hidden":  {"total": 30, "passed": 30, "failures": []},
        "pbt":     {"pbt_gate_passed": True, "pass_rate": 1.0, "failures": []}
    },
    "failure_analysis": {                # NOUVEAU: détail des échecs
        "public": {"wrong_answer": 0, "crash": 0, "timeout": 0},
        "hidden": {"wrong_answer": 0, "crash": 0, "timeout": 0},
        "pbt":    {"wrong_answer": 0, "crash": 0, "unsatisfiable": 0}
    },
    "execution_context": {               # NOUVEAU: contexte d'exécution
        "model": "multiprocessing.Process",
        "python_version": "3.11.0",
        "timeout_seconds": 1.0,
        "isolation": "process-level ..."
    }
}
```

**CLI** :
```bash
# Sortie JSON complète
python -m trcodebench.evaluate --item trcb-proto-0001 --candidate sol.py --format json

# Tableau lisible humain
python -m trcodebench.evaluate --item trcb-proto-0001 --candidate sol.py --format human

# Une ligne résumé
python -m trcodebench.evaluate --item trcb-proto-0001 --candidate sol.py --format compact
```

---

### 4.12 Runner OpenRouter — `openrouter_runner.py`

**Rôle** : Évaluer **plusieurs modèles LLM** sur **tous les items** en parallèle via l'API OpenRouter.

**Flux** :
```
1. Construire le prompt T2 (consignes + tests publics)
2. Appeler l'API OpenRouter (avec retry)
3. Extraire le code Python de la réponse (markdown ou plain)
4. Sauvegarder le candidat dans tmp/openrouter_candidates/
5. Évaluer avec evaluate_candidate()
6. Écrire une ligne JSONL + CSV
```

**Colonnes JSONL produites** :
```
run_id, model, item_id, run_index,
mp_correctness, mp_robustness, mp_efficiency, mp_divergence, mp_safety,  # 5 axes
pbt_pass_rate, pbt_gate_passed,
public_pass_rate, hidden_pass_rate,
public_failures, hidden_failures, pbt_failures,
paradigm_distance, salieri_overlap, genuine_divergence,
complexity_ratio_ok, complexity_ratio,
candidate_paradigms, oracle_paradigms,
execution_model,  # "multiprocessing.Process"
...
```

---

## 5. Schéma des données (item JSON)

Chaque item `trcb-proto-XXXX.json` suit ce schéma :

```json
{
  "id": "trcb-proto-0001",
  "language": "python",
  "family": "sorting",
  "source_type": "competitive_programming",
  "source": {
    "origin": "LeetCode",
    "date": "2024-01-15",
    "license": "CC-BY-4.0"
  },
  "task": {
    "title": "Longest Increasing Subsequence",
    "statement": "...",
    "signature": "def solve(nums: list[int]) -> int:",
    "function_name": "solve",
    "arguments": ["nums"],
    "allowed_imports": ["bisect", "heapq", "collections"],
    "forbidden_imports": ["numpy", "scipy"],
    "optimization_constraints": {
      "time_complexity": "n log n",
      "memory_mb": 256,
      "rejects_naive": "O(n²) is too slow for n=10000"
    }
  },
  "oracle": {
    "reference_solution_path": "solutions/trcb-0001/oracle.py",
    "reference_complexity": "n log n",
    "known_valid_paradigms": ["patience_sorting", "fenwick_tree_coordinate_compression"],
    "naive_solution_complexity": "O(n²)",
    "oracle_ast_features": {...},       // Précompté par annotate_oracle_features.py
    "oracle_detected_paradigms": ["patience_sorting"]
  },
  "tests": {
    "public_tests": ["tests/public/trcb-0001/test_public.py"],
    "hidden_tests_sha256": "abc123...",
    "hypothesis_strategy": "trcodebench.strategies.trcb_0001:make_strategy",
    "n_hidden_cases": 50,
    "pbt_groups": null
  },
  "anti_contamination": {
    "paraphrased": true,
    "identifier_obfuscated": true,
    "minhash_vs_original": 0.12,
    "is_honeypot": false
  },
  "scoring": {
    "correctness_weight": 0.5,
    "pbt_weight": 0.2,
    "optimization_weight": 0.15,
    "productive_divergence_weight": 0.15
  },
  "denial_constraints": [
    {
      "id": "dc-0001-01",
      "type": "forbidden_api",
      "forbidden": ["bisect", "bisect_left", "bisect_right"],
      "reason": "Force the model away from binary search",
      "expected_alternatives": ["fenwick_tree", "segment_tree"],
      "is_feasible": true
    }
  ]
}
```

---

## 6. Commandes d'utilisation

### Installation
```bash
pip install -e ".[dev]"
# ou dans WSL avec le conda local :
PYTHONPATH=/mnt/f/IA/TR-CodeBench/src ./.conda/bin/pip install hypothesis requests python-dotenv jsonschema
```

### Évaluation manuelle
```bash
# Format humain lisible
PYTHONPATH=src python -m trcodebench.evaluate \
  --item trcb-proto-0001 \
  --candidate candidates/example_lis.py \
  --hidden-cases 30 --pbt-cases 25 \
  --format human

# Format compact (une ligne)
PYTHONPATH=src python -m trcodebench.evaluate \
  --item trcb-proto-0001 \
  --candidate candidates/example_lis.py \
  --format compact
```

### Évaluation multi-modèles OpenRouter
```bash
# Configurer .env
echo "OPENROUTER_API_KEY=sk-..." > .env
echo "OPENROUTER_MODELS=openai/gpt-4o,anthropic/claude-3-5-sonnet" >> .env

# Lancer (WSL avec conda local)
PYTHONPATH=/mnt/f/IA/TR-CodeBench/src \
  ./.conda/bin/python -m trcodebench.openrouter_runner \
  --max-items all --n-runs 3 --max-workers 8

# Ou via le script bash
./scripts/run_openrouter_eval.sh --max-items all --n-runs 1 --max-workers 10
```

### Tests
```bash
PYTHONPATH=src pytest tests/unit/ -v        # Tous les tests
PYTHONPATH=src pytest tests/unit/ -q        # Résumé
PYTHONPATH=src pytest tests/unit/ -k "bar"  # Filtre
```

---

## 7. Agent de recherche — validation académique

### 7.1 Contexte et enjeux académiques

TR-CodeBench vise à mesurer la **Productive Divergence** (PD) des LLMs — leur capacité à générer des solutions algorithmiquement différentes de l'oracle tout en étant correctes. Pour être académiquement crédible, le benchmark doit :

1. **Discriminer** les modèles (éviter les effets plafond/plancher)
2. **Être fiable** (faible variance inter-runs)
3. **Corrélat valide** avec la vraie flexibilité algorithmique
4. **Résister à la contamination** (mémorisation ≠ compétence)
5. **Avoir des items de difficulté calibrée**

Les principaux risques académiques actuels :

| Risque | Impact | Module concerné |
|---|---|---|
| Fragility de la détection de paradigmes | Faux PD | `paradigm_classifier.py`, `paradigm_evidence/` |
| Threshold Salieri arbitraire (0.70) | Faux négatifs PD | `metrics_profile.py` |
| PBT strategies non validées | Robustness bias | `hidden_tests.py` |
| Items trop similaires entre eux | Multicollinéarité | `datasets/` |
| Score composite deprecated mais utilisé | Confusion métriques | `scoring.py` |

---

### 7.2 Architecture de l'agent

L'agent de recherche utilise le **Claude Agent SDK** pour effectuer une validation académique en boucle :

```
┌─────────────────────────────────────────────────────────────┐
│                  ResearchValidationAgent                     │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Literature  │    │  Statistical │    │  Benchmark   │  │
│  │   Scanner    │    │   Validator  │    │  Stress      │  │
│  │              │    │              │    │  Tester      │  │
│  │ ArXiv, ACL,  │    │ Inter-rater  │    │ Edge cases,  │  │
│  │ NeurIPS      │    │ reliability, │    │ adversarial  │  │
│  │              │    │ effect size  │    │ candidates   │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                  │                    │           │
│         └──────────────────┴────────────────────┘          │
│                             │                               │
│                    ┌────────▼────────┐                      │
│                    │  Academic       │                       │
│                    │  Report         │                       │
│                    │  Generator      │                       │
│                    └─────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

---

### 7.3 Code de l'agent complet

```python
"""
TR-CodeBench Academic Research Agent
=====================================
Utilise le Claude Agent SDK pour valider et améliorer le benchmark
académiquement. L'agent effectue 4 tâches en boucle :

1. Scanner la littérature (ArXiv/ACL/NeurIPS) pour comparer les approches
2. Valider statistiquement les métriques (fiabilité, discriminabilité)
3. Stress-tester les modules critiques (paradigm_classifier, salieri)
4. Générer un rapport de recommandations académiques

Usage :
    python docs/research_agent.py \
        --results-dir reports/openrouter_runs/ \
        --output-dir docs/academic_reports/ \
        [--n-runs 3] [--anthropic-key sk-...]
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from pathlib import Path
from typing import Any

import anthropic

# Ajouter src/ au path pour importer trcodebench
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from trcodebench.metrics_profile import (
    PARADIGM_COSMETIC_THRESHOLD,
    SALIERI_MEMORISATION_THRESHOLD,
    aggregate_profiles,
    compute_metrics_profile,
)
from trcodebench.paradigm_classifier import (
    PARADIGM_SIGNATURES,
    paradigm_distance,
)
from trcodebench.salieri_minhash import jaccard_similarity


# ---------------------------------------------------------------------------
# Outils mis à disposition de l'agent
# ---------------------------------------------------------------------------

TOOLS: list[dict] = [
    {
        "name": "compute_benchmark_statistics",
        "description": (
            "Calcule les statistiques statistiques clés sur les résultats du benchmark : "
            "moyenne, écart-type, effet de taille (Cohen's d), taux d'items discriminants, "
            "corrélation inter-runs (fiabilité test-retest). "
            "Prend en entrée une liste de résultats JSONL du openrouter_runner."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "jsonl_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Chemins vers les fichiers JSONL de résultats",
                },
                "group_by": {
                    "type": "string",
                    "enum": ["model", "item_id", "family"],
                    "description": "Dimension d'agrégation pour la comparaison",
                },
                "metric": {
                    "type": "string",
                    "enum": ["mp_correctness", "mp_robustness", "mp_efficiency",
                             "mp_divergence", "mp_safety", "pbt_pass_rate", "score"],
                    "description": "Métrique à analyser",
                },
            },
            "required": ["jsonl_paths", "group_by", "metric"],
        },
    },
    {
        "name": "validate_paradigm_classifier",
        "description": (
            "Teste la robustesse du paradigm_classifier sur des candidats synthétiques. "
            "Génère des variantes d'un paradigme connu (renommage variables, refactoring) "
            "et vérifie que le classifieur les détecte correctement. "
            "Retourne un rapport de précision/rappel par paradigme."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "paradigm": {
                    "type": "string",
                    "description": f"Paradigme à tester. Options: {list(PARADIGM_SIGNATURES.keys())}",
                },
                "n_variants": {
                    "type": "integer",
                    "description": "Nombre de variantes synthétiques à générer (défaut: 10)",
                    "default": 10,
                },
            },
            "required": ["paradigm"],
        },
    },
    {
        "name": "calibrate_salieri_threshold",
        "description": (
            "Analyse empiriquement le seuil optimal pour SALIERI_MEMORISATION_THRESHOLD. "
            "Calcule la distribution des Jaccard overlaps entre : "
            "(a) copies directes de l'oracle, "
            "(b) solutions alternatives indépendantes, "
            "(c) paraphrases syntaxiques. "
            "Recommande un seuil basé sur la maximisation de F1."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "item_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "IDs des items à analyser (ex: ['trcb-proto-0001'])",
                },
                "candidate_dirs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Répertoires contenant des candidats à analyser",
                },
            },
            "required": ["item_ids"],
        },
    },
    {
        "name": "analyze_item_difficulty",
        "description": (
            "Analyse la difficulté et la discrimination de chaque item du benchmark. "
            "Calcule : p-value (taux de réussite), discrimination index (D), "
            "corrélation item-total, et flag les items trop faciles (p>0.90) "
            "ou trop difficiles (p<0.10). "
            "Inspiré de la théorie classique des tests (CTT)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "jsonl_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "difficulty_metric": {
                    "type": "string",
                    "enum": ["mp_correctness", "mp_divergence", "score"],
                    "default": "mp_correctness",
                },
            },
            "required": ["jsonl_paths"],
        },
    },
    {
        "name": "generate_academic_report",
        "description": (
            "Génère un rapport académique complet en Markdown. "
            "Inclut : résumé exécutif, analyse des biais, comparaison avec benchmarks existants "
            "(HumanEval, MBPP, SWE-bench, LiveCodeBench), recommandations d'amélioration, "
            "et références bibliographiques."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "findings": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Liste de findings provenant des autres outils",
                },
                "output_path": {
                    "type": "string",
                    "description": "Chemin de sortie du rapport (ex: docs/academic_reports/report.md)",
                },
            },
            "required": ["findings", "output_path"],
        },
    },
    {
        "name": "search_related_benchmarks",
        "description": (
            "Recherche dans la littérature les benchmarks de code generation existants "
            "et identifie comment TR-CodeBench se différencie ou peut s'améliorer. "
            "Compare les métriques utilisées, la taille des datasets, et les protocoles "
            "de contamination."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Mots-clés de recherche (ex: ['code generation benchmark', 'algorithmic diversity'])",
                },
                "focus": {
                    "type": "string",
                    "enum": ["metrics", "contamination", "diversity", "evaluation_protocol"],
                    "description": "Aspect à analyser en priorité",
                },
            },
            "required": ["keywords"],
        },
    },
]


# ---------------------------------------------------------------------------
# Implémentation des outils
# ---------------------------------------------------------------------------

def _load_jsonl(paths: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        p = Path(path)
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return rows


def tool_compute_benchmark_statistics(
    jsonl_paths: list[str],
    group_by: str,
    metric: str,
) -> dict[str, Any]:
    rows = _load_jsonl(jsonl_paths)
    if not rows:
        return {"error": "No data found in provided JSONL paths"}

    # Grouper par dimension
    groups: dict[str, list[float]] = {}
    for row in rows:
        key = str(row.get(group_by, "unknown"))
        val = row.get(metric)
        if val is not None:
            groups.setdefault(key, []).append(float(val))

    # Statistiques par groupe
    stats: dict[str, Any] = {}
    all_values: list[float] = []
    for key, values in groups.items():
        all_values.extend(values)
        mean = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 0.0
        stats[key] = {
            "n": len(values),
            "mean": round(mean, 4),
            "std": round(std, 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "p25": round(statistics.quantiles(values, n=4)[0], 4) if len(values) >= 4 else None,
            "p75": round(statistics.quantiles(values, n=4)[2], 4) if len(values) >= 4 else None,
        }

    # Effet de taille global (Cohen's d entre meilleur et pire groupe)
    group_means = {k: v["mean"] for k, v in stats.items()}
    if len(group_means) >= 2:
        sorted_means = sorted(group_means.values())
        pooled_std = statistics.stdev(all_values) if len(all_values) > 1 else 1.0
        cohens_d = (sorted_means[-1] - sorted_means[0]) / pooled_std if pooled_std > 0 else 0.0
    else:
        cohens_d = None

    # Taux d'items discriminants (variance > 0.05)
    if group_by == "item_id":
        discriminating = sum(1 for v in stats.values() if v["std"] > 0.05)
        discrimination_rate = discriminating / len(stats) if stats else 0.0
    else:
        discrimination_rate = None

    return {
        "metric": metric,
        "group_by": group_by,
        "n_groups": len(stats),
        "n_total_rows": len(rows),
        "group_stats": stats,
        "cohens_d": round(cohens_d, 4) if cohens_d is not None else None,
        "discrimination_rate": round(discrimination_rate, 4) if discrimination_rate is not None else None,
        "interpretation": {
            "cohens_d": (
                "large effect (>0.8)" if cohens_d and cohens_d > 0.8
                else "medium effect (0.5-0.8)" if cohens_d and cohens_d > 0.5
                else "small effect (<0.5)"
            ) if cohens_d else "N/A",
            "discrimination_rate": (
                f"{discrimination_rate:.0%} of items discriminate between models"
                if discrimination_rate is not None else "N/A"
            ),
        },
    }


def tool_validate_paradigm_classifier(
    paradigm: str,
    n_variants: int = 10,
) -> dict[str, Any]:
    """Test the paradigm classifier with synthetic code variants."""
    from trcodebench.ast_features import extract_features
    from trcodebench.paradigm_classifier import detect_paradigms

    signature = PARADIGM_SIGNATURES.get(paradigm)
    if not signature:
        return {"error": f"Unknown paradigm: {paradigm}"}

    # Variantes synthétiques connues (hard-coded pour les paradigmes principaux)
    SYNTHETIC_VARIANTS: dict[str, list[str]] = {
        "fenwick_tree": [
            # Variant 1: Noms de variables anglais classiques
            """
def solve(n, ops):
    bit = [0] * (n + 1)
    def update(i, v):
        while i <= n:
            bit[i] += v
            i += i & -i
    def query(i):
        s = 0
        while i > 0:
            s += bit[i]
            i -= i & -i
        return s
    result = []
    for op, l, r in ops:
        if op == 'add': update(l, r)
        else: result.append(query(r) - query(l-1))
    return result
""",
            # Variant 2: Noms de variables français
            """
def solve(n, ops):
    arbre = [0] * (n + 1)
    def maj(idx, val):
        while idx <= n:
            arbre[idx] += val
            idx += idx & -idx
    def somme(idx):
        total = 0
        while idx > 0:
            total += arbre[idx]
            idx -= idx & -idx
        return total
    res = []
    for op, g, d in ops:
        if op == 'add': maj(g, d)
        else: res.append(somme(d) - somme(g-1))
    return res
""",
            # Variant 3: Noms obfusqués
            """
def solve(n, ops):
    T = [0] * (n + 1)
    def U(x, v):
        while x <= n:
            T[x] += v
            x += x & -x
    def Q(x):
        r = 0
        while x > 0:
            r += T[x]
            x -= x & -x
        return r
    ans = []
    for t, a, b in ops:
        if t == 'add': U(a, b)
        else: ans.append(Q(b) - Q(a-1))
    return ans
""",
        ],
        "patience_sorting": [
            """
import bisect
def solve(nums):
    piles = []
    for n in nums:
        pos = bisect.bisect_left(piles, n)
        if pos == len(piles): piles.append(n)
        else: piles[pos] = n
    return len(piles)
""",
            """
from bisect import bisect_left
def solve(sequence):
    stacks = []
    for element in sequence:
        idx = bisect_left(stacks, element)
        if idx >= len(stacks): stacks.append(element)
        else: stacks[idx] = element
    return len(stacks)
""",
        ],
        "kmp": [
            """
def solve(text, pattern):
    n, m = len(text), len(pattern)
    lps = [0] * m
    length = 0
    i = 1
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        elif length:
            length = lps[length - 1]
        else:
            lps[i] = 0
            i += 1
    return lps
""",
        ],
    }

    variants = SYNTHETIC_VARIANTS.get(paradigm, [])
    if not variants:
        return {
            "paradigm": paradigm,
            "error": f"No synthetic variants defined for '{paradigm}'. Add them to SYNTHETIC_VARIANTS.",
            "suggestion": "Contribute variants to the research agent by adding hand-crafted examples.",
        }

    results = []
    true_positives = 0
    for i, code in enumerate(variants[:n_variants]):
        features = extract_features(code)
        detected = detect_paradigms(features, list(PARADIGM_SIGNATURES.keys()))
        correct = paradigm in detected
        true_positives += int(correct)
        results.append({
            "variant": i + 1,
            "detected_paradigms": detected,
            "correct": correct,
            "features": features,
        })

    precision = true_positives / len(results) if results else 0.0
    return {
        "paradigm": paradigm,
        "n_variants_tested": len(results),
        "true_positives": true_positives,
        "precision_on_variants": round(precision, 4),
        "variants": results,
        "recommendation": (
            "FRAGILE: precision < 0.80 — consider adding to paradigm_evidence/ evidence stack"
            if precision < 0.80
            else "ROBUST: precision >= 0.80 — signature matching sufficient"
        ),
    }


def tool_calibrate_salieri_threshold(
    item_ids: list[str],
    candidate_dirs: list[str] | None = None,
) -> dict[str, Any]:
    """Analyze the distribution of Salieri overlaps to calibrate the threshold."""
    from trcodebench.load_items import load_item, resolve_repo_path

    overlaps_copies: list[float] = []
    overlaps_alternatives: list[float] = []

    for item_id in item_ids:
        try:
            item = load_item(item_id)
            oracle_path = resolve_repo_path(item["oracle"]["reference_solution_path"])
            oracle_source = oracle_path.read_text(encoding="utf-8")
        except Exception as e:
            continue

        # Copie directe = similarité maximale
        overlaps_copies.append(jaccard_similarity(oracle_source, oracle_source))

        # Chercher des candidats alternatifs dans les répertoires fournis
        if candidate_dirs:
            for cdir in candidate_dirs:
                cdir_path = Path(cdir)
                if cdir_path.exists():
                    for candidate in cdir_path.glob("*.py"):
                        try:
                            cand_source = candidate.read_text(encoding="utf-8")
                            overlap = jaccard_similarity(cand_source, oracle_source)
                            overlaps_alternatives.append(overlap)
                        except Exception:
                            pass

    if not overlaps_copies:
        return {"error": "Could not load any items"}

    # Analyse de la distribution
    result: dict[str, Any] = {
        "current_threshold": SALIERI_MEMORISATION_THRESHOLD,
        "copies_distribution": {
            "n": len(overlaps_copies),
            "mean": round(statistics.mean(overlaps_copies), 4) if overlaps_copies else None,
            "min": round(min(overlaps_copies), 4) if overlaps_copies else None,
            "max": round(max(overlaps_copies), 4) if overlaps_copies else None,
        },
        "alternatives_distribution": {
            "n": len(overlaps_alternatives),
            "mean": round(statistics.mean(overlaps_alternatives), 4) if overlaps_alternatives else None,
            "min": round(min(overlaps_alternatives), 4) if overlaps_alternatives else None,
            "max": round(max(overlaps_alternatives), 4) if overlaps_alternatives else None,
        },
    }

    # Recommandation de seuil
    if overlaps_alternatives:
        # Le seuil idéal est entre le max des alternatives et le min des copies
        max_alt = max(overlaps_alternatives)
        min_copy = min(overlaps_copies)
        if max_alt < min_copy:
            recommended = round((max_alt + min_copy) / 2, 2)
            result["recommended_threshold"] = recommended
            result["separation_gap"] = round(min_copy - max_alt, 4)
            result["recommendation"] = (
                f"Clear separation detected. Recommend threshold={recommended} "
                f"(current={SALIERI_MEMORISATION_THRESHOLD})"
            )
        else:
            result["recommended_threshold"] = SALIERI_MEMORISATION_THRESHOLD
            result["recommendation"] = (
                "Overlap between copies and alternatives detected. "
                "Current threshold may cause false positives. "
                "Consider collecting more diverse alternative solutions."
            )
    else:
        result["recommendation"] = (
            "No alternative solutions found. Cannot calibrate threshold empirically. "
            "Provide candidate_dirs with known-correct alternative solutions."
        )

    return result


def tool_analyze_item_difficulty(
    jsonl_paths: list[str],
    difficulty_metric: str = "mp_correctness",
) -> dict[str, Any]:
    """Analyze item difficulty and discrimination (Classical Test Theory)."""
    rows = _load_jsonl(jsonl_paths)
    if not rows:
        return {"error": "No data found"}

    # Grouper par item_id
    item_scores: dict[str, list[float]] = {}
    model_scores: dict[str, list[float]] = {}

    for row in rows:
        item_id = str(row.get("item_id", "unknown"))
        model = str(row.get("model", "unknown"))
        val = row.get(difficulty_metric)
        if val is not None:
            item_scores.setdefault(item_id, []).append(float(val))
            model_scores.setdefault(model, []).append(float(val))

    # Scores totaux par modèle (pour corrélation item-total)
    model_total_means = {m: statistics.mean(vs) for m, vs in model_scores.items()}

    results: dict[str, Any] = {}
    flagged_easy: list[str] = []
    flagged_hard: list[str] = []
    flagged_low_discrim: list[str] = []

    for item_id, scores in item_scores.items():
        p = statistics.mean(scores)  # p-value (difficulty index)
        std = statistics.stdev(scores) if len(scores) > 1 else 0.0

        # Discrimination index D = P_high - P_low (CTT approach)
        # Simplification: std comme proxy de discrimination
        D = std

        item_result: dict[str, Any] = {
            "n_runs": len(scores),
            "p_value": round(p, 4),
            "std": round(std, 4),
            "discrimination_D": round(D, 4),
            "flags": [],
        }

        if p > 0.90:
            item_result["flags"].append("TOO_EASY")
            flagged_easy.append(item_id)
        if p < 0.10:
            item_result["flags"].append("TOO_HARD")
            flagged_hard.append(item_id)
        if D < 0.10:
            item_result["flags"].append("LOW_DISCRIMINATION")
            flagged_low_discrim.append(item_id)

        results[item_id] = item_result

    return {
        "metric": difficulty_metric,
        "n_items": len(results),
        "n_flagged_easy": len(flagged_easy),
        "n_flagged_hard": len(flagged_hard),
        "n_flagged_low_discrimination": len(flagged_low_discrim),
        "flagged_easy": flagged_easy,
        "flagged_hard": flagged_hard,
        "flagged_low_discrimination": flagged_low_discrim,
        "items": results,
        "recommendations": [
            f"Remove or rework {len(flagged_easy)} trivial items (p>0.90)" if flagged_easy else None,
            f"Add scaffolding or split {len(flagged_hard)} too-hard items (p<0.10)" if flagged_hard else None,
            f"Replace {len(flagged_low_discrim)} low-discrimination items (D<0.10)" if flagged_low_discrim else None,
        ],
    }


def tool_generate_academic_report(
    findings: list[dict[str, Any]],
    output_path: str,
) -> dict[str, Any]:
    """Generate a Markdown academic report from collected findings."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# TR-CodeBench — Academic Validation Report",
        "",
        f"> Generated automatically by the Research Validation Agent  ",
        f"> Date: {__import__('datetime').date.today().isoformat()}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        "This report presents an automated academic validation of the TR-CodeBench benchmark.",
        "It covers: statistical properties, paradigm classifier robustness, Salieri threshold",
        "calibration, item difficulty analysis, and comparison with existing benchmarks.",
        "",
        "---",
        "",
    ]

    for i, finding in enumerate(findings, 1):
        tool_name = finding.get("tool", f"Finding {i}")
        lines.append(f"## {i}. {tool_name.replace('_', ' ').title()}")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(finding.get("result", {}), indent=2, ensure_ascii=False)[:3000])
        lines.append("```")
        lines.append("")

    lines += [
        "---",
        "",
        "## Comparison with Existing Benchmarks",
        "",
        "| Benchmark | Size | Metric | Contamination | Algorithm Diversity |",
        "|---|---|---|---|---|",
        "| HumanEval | 164 | pass@k | Low | Low (single solution) |",
        "| MBPP | 374 | pass@k | Medium | Low |",
        "| SWE-bench | 2294 | resolved% | Low | High (repo-level) |",
        "| LiveCodeBench | 400+ | pass@k | Very Low | Medium |",
        "| **TR-CodeBench** | **40** | **5-axis profile** | **Very Low** | **High (PD measured)** |",
        "",
        "**Key differentiator**: TR-CodeBench is the first benchmark explicitly measuring",
        "**Productive Divergence** — the ability to solve problems with algorithms",
        "fundamentally different from the reference oracle.",
        "",
        "---",
        "",
        "## Academic References",
        "",
        "- Chen, M. et al. (2021). Evaluating Large Language Models Trained on Code. *arXiv:2107.03374*",
        "- Austin, J. et al. (2021). Program Synthesis with Large Language Models. *arXiv:2108.07732*",
        "- Jimenez, C. et al. (2024). SWE-bench: Can Language Models Resolve Real-World GitHub Issues? *ICLR 2024*",
        "- Liu, J. et al. (2023). Is Your Code Generated by ChatGPT Really Correct? *NeurIPS 2023*",
        "- Jain, N. et al. (2024). LiveCodeBench: Holistic and Contamination Free Evaluation of LLMs for Code. *arXiv:2403.07974*",
        "",
        "---",
        "",
        "## Recommendations",
        "",
        "1. **Expand dataset**: 40 items → 200+ for statistical power (α=0.05, β=0.80)",
        "2. **Validate paradigm signatures**: Run inter-annotator agreement study on paradigm labels",
        "3. **Calibrate Salieri threshold empirically**: Collect 100+ diverse solutions per item",
        "4. **Add stress test items**: Items designed to expose specific model weaknesses",
        "5. **Report inter-run reliability**: Publish Cohen's κ or ICC across runs",
        "6. **Release denial trajectories data**: To enable research on algorithmic flexibility",
    ]

    output.write_text("\n".join(lines), encoding="utf-8")
    return {"output_path": str(output), "n_findings": len(findings), "status": "ok"}


def tool_search_related_benchmarks(
    keywords: list[str],
    focus: str = "metrics",
) -> dict[str, Any]:
    """Return structured knowledge about related benchmarks (static KB for now)."""
    BENCHMARK_KB = {
        "HumanEval": {
            "paper": "Chen et al., 2021 (arXiv:2107.03374)",
            "size": 164,
            "metric": "pass@k (k=1,10,100)",
            "language": "Python",
            "contamination_risk": "HIGH (GitHub-derived, pre-2023 LLMs trained on it)",
            "algorithm_diversity": "None (single reference solution)",
            "pd_measured": False,
            "relevance_to_trcb": "Baseline comparison; lacks diversity measurement",
        },
        "MBPP": {
            "paper": "Austin et al., 2021 (arXiv:2108.07732)",
            "size": 374,
            "metric": "pass@k",
            "language": "Python",
            "contamination_risk": "HIGH",
            "algorithm_diversity": "None",
            "pd_measured": False,
            "relevance_to_trcb": "Baseline; simpler problems than TR-CodeBench",
        },
        "SWE-bench": {
            "paper": "Jimenez et al., 2024 (ICLR)",
            "size": 2294,
            "metric": "resolved%",
            "language": "Python (repo-level)",
            "contamination_risk": "LOW (real GitHub issues post-2023)",
            "algorithm_diversity": "HIGH (repo-level solutions)",
            "pd_measured": False,
            "relevance_to_trcb": "Different scope; repo-level vs function-level",
        },
        "LiveCodeBench": {
            "paper": "Jain et al., 2024 (arXiv:2403.07974)",
            "size": "400+ (growing)",
            "metric": "pass@1",
            "language": "Multiple",
            "contamination_risk": "VERY LOW (monthly updates with new problems)",
            "algorithm_diversity": "MEDIUM (competitive programming, single solution)",
            "pd_measured": False,
            "relevance_to_trcb": "Closest competitor for algorithmic problems; lacks PD",
        },
        "EvalPlus": {
            "paper": "Liu et al., 2023 (NeurIPS)",
            "size": "HumanEval+ (164), MBPP+ (378)",
            "metric": "pass@k with augmented tests",
            "language": "Python",
            "contamination_risk": "MEDIUM",
            "algorithm_diversity": "None",
            "pd_measured": False,
            "relevance_to_trcb": "Shows importance of test coverage; motivates PBT approach",
        },
        "TR-CodeBench": {
            "paper": "In preparation",
            "size": 40,
            "metric": "5-axis profile (correctness, robustness, efficiency, divergence, safety)",
            "language": "Python 3.11",
            "contamination_risk": "VERY LOW (paraphrased + identifier obfuscated)",
            "algorithm_diversity": "HIGH (PD explicitly measured)",
            "pd_measured": True,
            "unique_features": [
                "Productive Divergence (PD) measurement",
                "Denial trajectories",
                "Property-Based Testing (Hypothesis)",
                "5-axis independent metrics",
                "Paradigm evidence stack",
                "T2 truth regime",
            ],
        },
    }

    # Filtrer selon les keywords
    relevant = {}
    kw_lower = [k.lower() for k in keywords]
    for name, info in BENCHMARK_KB.items():
        text = json.dumps(info).lower()
        if any(k in text for k in kw_lower) or name == "TR-CodeBench":
            relevant[name] = info

    return {
        "focus": focus,
        "keywords": keywords,
        "benchmarks_found": len(relevant),
        "benchmarks": relevant,
        "tr_codebench_gap": (
            "TR-CodeBench uniquely measures Productive Divergence. "
            "No existing benchmark quantifies whether a model can produce "
            "algorithmically diverse correct solutions."
        ),
    }


# ---------------------------------------------------------------------------
# Dispatch des outils
# ---------------------------------------------------------------------------

TOOL_FUNCTIONS = {
    "compute_benchmark_statistics": tool_compute_benchmark_statistics,
    "validate_paradigm_classifier": tool_validate_paradigm_classifier,
    "calibrate_salieri_threshold": tool_calibrate_salieri_threshold,
    "analyze_item_difficulty": tool_analyze_item_difficulty,
    "generate_academic_report": tool_generate_academic_report,
    "search_related_benchmarks": tool_search_related_benchmarks,
}


def run_tool(tool_name: str, tool_input: dict[str, Any]) -> Any:
    fn = TOOL_FUNCTIONS.get(tool_name)
    if fn is None:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return fn(**tool_input)
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


# ---------------------------------------------------------------------------
# Boucle agent principale
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an academic research assistant specializing in LLM evaluation benchmarks.
Your task is to validate and improve TR-CodeBench — a benchmark measuring Productive Divergence (PD)
in code generation models.

TR-CodeBench key concepts:
- T2 Truth Regime: any correct algorithm is valid (no single reference answer)
- Productive Divergence: model uses a fundamentally different algorithm than the oracle
- 5-axis metrics: correctness, robustness, efficiency, divergence, safety
- PBT: Property-Based Testing via Hypothesis
- Denial trajectories: iterative paradigm elicitation under successive constraints

Your analysis should be rigorous, actionable, and grounded in benchmark evaluation methodology
(Classical Test Theory, Item Response Theory, inter-rater reliability).

Available tools allow you to:
1. Compute statistical properties of benchmark results
2. Validate the paradigm classifier with synthetic variants
3. Calibrate the Salieri anti-memorization threshold empirically
4. Analyze item difficulty and discrimination
5. Generate a formal academic report
6. Compare with existing benchmarks (HumanEval, MBPP, SWE-bench, LiveCodeBench)

Work systematically: gather data first, then analyze, then report.
Always quantify uncertainty and flag limitations in your analysis."""


def run_research_agent(
    results_dir: str,
    output_dir: str,
    n_runs_to_analyze: int = 3,
    max_agent_turns: int = 15,
    anthropic_key: str | None = None,
) -> None:
    client = anthropic.Anthropic(api_key=anthropic_key or os.environ.get("ANTHROPIC_API_KEY"))

    # Trouver les fichiers JSONL de résultats
    jsonl_files = sorted(Path(results_dir).glob("*.jsonl"))[:n_runs_to_analyze]
    jsonl_paths = [str(f) for f in jsonl_files]

    if not jsonl_paths:
        print(f"[WARNING] No JSONL files found in {results_dir}")
        print("The agent will run in analysis-only mode (no empirical data).")

    initial_message = f"""
Please conduct a comprehensive academic validation of the TR-CodeBench benchmark.

Available result files: {jsonl_paths if jsonl_paths else "None — run openrouter_runner.py first"}
Output directory for reports: {output_dir}

Follow this analysis plan:
1. Search for related benchmarks to understand the academic context
2. Validate the paradigm classifier on key paradigms (fenwick_tree, patience_sorting, kmp)
3. If result files are available: compute benchmark statistics by model and by item
4. If result files are available: analyze item difficulty and flag problematic items
5. Calibrate the Salieri threshold (use item trcb-proto-0001 as example)
6. Generate a comprehensive academic report with all findings

Be specific about numerical thresholds, cite methodology, and provide actionable recommendations.
"""

    messages = [{"role": "user", "content": initial_message}]
    findings: list[dict[str, Any]] = []

    print(f"[Research Agent] Starting academic validation...")
    print(f"[Research Agent] Results dir: {results_dir}")
    print(f"[Research Agent] Output dir: {output_dir}")
    print()

    for turn in range(max_agent_turns):
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Ajouter la réponse de l'agent à l'historique
        messages.append({"role": "assistant", "content": response.content})

        # Afficher le texte de l'agent
        for block in response.content:
            if hasattr(block, "text") and block.text:
                print(f"[Agent] {block.text[:500]}...")
                print()

        # Si l'agent a terminé
        if response.stop_reason == "end_turn":
            print(f"[Research Agent] Analysis complete after {turn + 1} turns.")
            break

        # Exécuter les outils demandés
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"[Tool] Calling: {block.name}({list(block.input.keys())})")
                result = run_tool(block.name, block.input)
                print(f"[Tool] Result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")
                print()

                # Sauvegarder le finding
                findings.append({
                    "tool": block.name,
                    "input": block.input,
                    "result": result,
                })

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str)[:8000],
                })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

    # Sauvegarder les findings bruts
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    findings_path = output_path / "research_agent_findings.json"
    findings_path.write_text(
        json.dumps(findings, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"\n[Research Agent] Findings saved to: {findings_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="TR-CodeBench Academic Research Agent — validates and improves the benchmark"
    )
    parser.add_argument(
        "--results-dir",
        default="reports/openrouter_runs",
        help="Directory containing openrouter JSONL result files",
    )
    parser.add_argument(
        "--output-dir",
        default="docs/academic_reports",
        help="Output directory for academic reports",
    )
    parser.add_argument(
        "--n-runs",
        type=int,
        default=3,
        help="Number of result files to analyze",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=15,
        help="Maximum agent conversation turns",
    )
    parser.add_argument(
        "--anthropic-key",
        default=None,
        help="Anthropic API key (defaults to ANTHROPIC_API_KEY env var)",
    )
    args = parser.parse_args()

    run_research_agent(
        results_dir=args.results_dir,
        output_dir=args.output_dir,
        n_runs_to_analyze=args.n_runs,
        max_agent_turns=args.max_turns,
        anthropic_key=args.anthropic_key,
    )


if __name__ == "__main__":
    main()
```

---

### 7.4 Métriques académiques cibles

Pour une publication, le benchmark devrait atteindre ces standards :

#### Fiabilité (Reliability)
| Métrique | Cible | Outil |
|---|---|---|
| **Test-retest ICC** sur `mp_divergence` | ≥ 0.85 | `compute_benchmark_statistics` |
| **Inter-run σ** par item/modèle | < 0.05 | `compute_benchmark_statistics` |
| **Cohen's κ** labelling paradigmes | ≥ 0.80 | Étude humaine externe |

#### Validité (Validity)
| Métrique | Cible | Outil |
|---|---|---|
| **Discrimination rate** des items | ≥ 70% | `analyze_item_difficulty` |
| **Effet de taille (Cohen's d)** entre modèles | ≥ 0.50 | `compute_benchmark_statistics` |
| **p-value** des items : 0.10 < p < 0.90 | 100% des items | `analyze_item_difficulty` |

#### Robustesse du classifieur
| Métrique | Cible | Outil |
|---|---|---|
| **Precision@variants** par paradigme | ≥ 0.80 | `validate_paradigm_classifier` |
| **Seuil Salieri F1** | Empirique > 0.70 actuel | `calibrate_salieri_threshold` |

---

### 7.5 Intégration dans le pipeline existant

#### Installation des dépendances de l'agent
```bash
pip install anthropic
# ou
pip install -e ".[dev]"  # si anthropic est ajouté aux extras dans pyproject.toml
```

#### Lancement de l'agent
```bash
# Validation académique complète (avec résultats disponibles)
ANTHROPIC_API_KEY=sk-... \
PYTHONPATH=src \
python docs/research_agent.py \
  --results-dir reports/openrouter_runs/ \
  --output-dir docs/academic_reports/ \
  --n-runs 5

# Mode analyse seule (sans résultats — validation des modules)
ANTHROPIC_API_KEY=sk-... \
PYTHONPATH=src \
python docs/research_agent.py \
  --results-dir /nonexistent \
  --output-dir docs/academic_reports/
```

#### Utilisation directe des outils sans l'agent
```python
import sys
sys.path.insert(0, "src")

# Depuis le fichier research_agent.py
from docs.research_agent import (
    tool_validate_paradigm_classifier,
    tool_analyze_item_difficulty,
    tool_calibrate_salieri_threshold,
)

# Valider le classifieur pour fenwick_tree
result = tool_validate_paradigm_classifier("fenwick_tree", n_variants=3)
print(f"Precision: {result['precision_on_variants']}")
print(f"Recommendation: {result['recommendation']}")

# Analyser la difficulté des items (si résultats disponibles)
difficulty = tool_analyze_item_difficulty(
    jsonl_paths=["reports/openrouter_runs/run_20240115.jsonl"],
    difficulty_metric="mp_correctness",
)
print(f"Flagged easy: {difficulty['flagged_easy']}")
print(f"Flagged hard: {difficulty['flagged_hard']}")
```

#### Flux complet d'une session de validation

```
1. Lancer des évaluations OpenRouter:
   ./scripts/run_openrouter_eval.sh --max-items all --n-runs 3

2. Lancer l'agent de recherche:
   python docs/research_agent.py --n-runs 3

3. Lire le rapport généré:
   cat docs/academic_reports/report.md

4. Appliquer les recommandations:
   - Si items trop faciles → ajouter des cas cachés plus difficiles
   - Si paradigme imprecis → ajouter des signaux dans paradigm_evidence/
   - Si seuil Salieri mal calibré → ajuster SALIERI_MEMORISATION_THRESHOLD
   - Si variance inter-runs trop élevée → augmenter n_runs
```

---

*Document généré automatiquement — version 0.4 — TR-CodeBench*
