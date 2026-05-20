# TR-CodeBench — Spécifications, Historique & Revue de Projet

> Document de référence technique exhaustif.  
> Couvre le contexte théorique, les décisions d'architecture, l'historique des versions, l'état de l'art, la revue critique et la feuille de route.  
> Dernière mise à jour : **2026-05-20** — run `openrouter_eval_20260512T220239Z` (v0.3 interne, 5 modèles × 10 items)

---

## Table des matières

1. [Contexte et motivation](#1-contexte-et-motivation)
2. [Concepts fondamentaux](#2-concepts-fondamentaux)
3. [Architecture du dépôt](#3-architecture-du-dépôt)
4. [Pipeline d'évaluation](#4-pipeline-dévaluation)
5. [Formule de score — spécification complète](#5-formule-de-score--spécification-complète)
6. [Les 10 items prototypes](#6-les-10-items-prototypes)
7. [État de l'art et positionnement](#7-état-de-lart-et-positionnement)
8. [Historique des versions et décisions](#8-historique-des-versions-et-décisions)
9. [Bugs connus et dettes techniques](#9-bugs-connus-et-dettes-techniques)
10. [Résultats des runs et observations](#10-résultats-des-runs-et-observations)
11. [Revue critique — lacunes structurelles](#11-revue-critique--lacunes-structurelles)
12. [Recommandations et feuille de route](#12-recommandations-et-feuille-de-route)

---

## 1. Contexte et motivation

### 1.1 Problème central

Les benchmarks de code pour LLM — HumanEval, EvalPlus, APPS, LiveCodeBench — mesurent essentiellement la **correctness** : le code passe-t-il les tests ? Ce critère binaire est insuffisant pour discriminer deux propriétés distinctes mais confondues dans la littérature :

- **La mémorisation** : le modèle reproduit une solution mémorisée lors de l'entraînement (GitHub, LeetCode, The Stack)
- **La compréhension structurelle** : le modèle comprend le problème assez profondément pour choisir parmi plusieurs algorithmes valides

Un modèle peut scorer 90 % sur HumanEval en mémorisant. Un modèle qui _comprend_ doit être capable de produire un algorithme efficace même sous contrainte de paradigme ou de complexité asymptotique.

### 1.2 Hypothèse du position paper

TR-CodeBench est construit autour de l'hypothèse que les LLMs performent différemment selon le **Truth Regime (TR)** d'une tâche, une dimension orthogonale à la difficulté algorithmique perçue :

- En **T1** (Truth Regime faible) : beaucoup de réponses factuellement incorrectes sont possibles. Le modèle peut halluciner des APIs, inventer des bibliothèques, dériver vers des solutions incorrectes non détectables sans oracle.
- En **T2** (Truth Regime fort) : la réponse est vérifiable par exécution contre un oracle scellé. Il existe plusieurs paradigmes algorithmiques valides mais la license d'invention factuelle est faible : tout ce qui ne compile pas ou ne passe pas les tests est faux.

TR-CodeBench est un benchmark **T2** : latitude stratégique élevée (plusieurs paradigmes acceptés), licence d'invention basse (exécution obligatoire, oracle strict).

---

## 2. Concepts fondamentaux

### 2.1 True Regime (T2)

Un item est en Truth Regime T2 lorsque :

1. La tâche possède une réponse vérifiable par exécution (oracle + tests cachés)
2. Plusieurs paradigmes algorithmiques distincts conduisent à la bonne réponse (ex. KMP, Z-algorithm, rolling hash pour la recherche de motif)
3. Une contrainte de complexité asymptotique est explicitement imposée (ex. O(n log n), pas O(n²))
4. La solution naïve évidente passe les tests courts mais échoue sur les grandes entrées

Chaque item définit dans son JSON :

- `naive_solution_complexity` : la complexité de la solution triviale à rejeter
- `reference_complexity` : la contrainte cible
- `optimization_constraints.rejects_naive` : description de ce qui est rejeté

### 2.2 Productive Divergence (PD)

La **Productive Divergence** est le signal distinctif du benchmark. Un modèle manifeste une PD lorsqu'il :

1. Produit une solution **correcte** (passe tous les tests publics et cachés)
2. Utilise un **paradigme algorithmique distinct** de celui de l'oracle de référence
3. Respecte la **contrainte de complexité** de l'item

La PD teste si le modèle a une compréhension structurelle du problème plutôt qu'une restitution mnémotechnique. Deux modèles peuvent tous deux scorer 1.0 en correctness mais l'un via KMP et l'autre via rolling hash — seul le second manifeste une PD par rapport à un oracle KMP.

**Ce que la PD n'est pas :**

- Une différence de style (type hints, nommage de variables, docstrings)
- Une réduction de la similarité Jaccard des tokens sans changement de paradigme
- Un score de nouveauté par rapport au corpus d'entraînement (ça, c'est NeoCode)

### 2.3 Relation PD ↔ True Regime

```
True Regime T2
    └── Correctness (obligatoire)
        └── Optimization (conformité à la complexité cible)
            └── Productive Divergence (paradigme distinct de l'oracle)
                              ↑
                    Signal le plus fin — nécessite T2
```

La PD n'a de sens que dans un contexte T2 : sans correctness vérifiable, n'importe quelle divergence de style peut prétendre à une PD.

---

## 3. Architecture du dépôt

```
TR-CodeBench/
├── datasets/curated/           # 10 items JSON (trcb-proto-0001 à 0010)
├── oracles/                    # Solutions de référence Python
├── tests/public/               # 5 cas publics par item (pytest)
├── strategies/                 # Stratégies Hypothesis par item
├── schemas/                    # item.schema.json — contrat JSON des items
├── src/trcodebench/
│   ├── ast_features.py         # Extraction features AST (bisect, heapq, fenwick…)
│   ├── paradigm_classifier.py  # Signatures de paradigmes + détection
│   ├── paradigm_evidence/      # Enrichissement multi-couche des paradigmes
│   ├── salieri_minhash.py      # Jaccard 5-grams de tokens normalisés
│   ├── scoring.py              # Formule de score (source of truth)
│   ├── evaluate.py             # Pipeline d'évaluation complet
│   ├── hidden_tests.py         # Générateur de cas cachés
│   ├── static_checks.py        # Vérifications AST statiques (imports bannis…)
│   ├── run_candidate.py        # Exécution du candidat en sous-processus
│   ├── load_items.py           # Chargement des items JSON
│   └── openrouter_runner.py    # Runner OpenRouter (appels API)
├── notebooks/
│   ├── openrouter_real_world_eval.ipynb  # Notebook de run live
│   └── trcb_analysis.ipynb               # Notebook d'analyse des résultats
├── reports/openrouter_runs/    # CSVs et JSONLs des runs
├── prompts/                    # Templates de prompt pour les modèles
├── scripts/                    # Scripts shell (run_openrouter_eval.sh)
├── docs/
│   └── SPEC.md                 # Ce document
└── pyproject.toml
```

### 3.1 Schéma JSON d'un item

Chaque item respecte `schemas/item.schema.json`. Champs principaux :

```json
{
	"id": "trcb-proto-0001",
	"task": {
		"function_name": "solve",
		"arguments": ["nums"],
		"description": "...",
		"prompt": "..."
	},
	"oracle": {
		"reference_solution_path": "oracles/trcb_proto_0001.py",
		"reference_complexity": "O(n log n)",
		"naive_solution_complexity": "O(n²)",
		"known_valid_paradigms": [
			"patience_sorting",
			"fenwick_tree_coordinate_compression"
		],
		"oracle_ast_features": { "...": "pré-calculé v0.2" }
	},
	"tests": {
		"public_tests": ["tests/public/trcb_proto_0001_test.py"],
		"hypothesis_strategy": "strategies.trcb_0001_strategy:make_strategy",
		"pbt_groups": null
	},
	"optimization_constraints": {
		"target_complexity": "O(n log n)",
		"rejects_naive": "O(n²) DP solution"
	}
}
```

Le champ `oracle_ast_features` (introduit en v0.2) pré-calcule les features AST de l'oracle pour éviter la re-détection dynamique à chaque évaluation.

---

## 4. Pipeline d'évaluation

### 4.1 Vue d'ensemble (`evaluate.py`)

```
candidat.py
  ↓
static_checks         → violations statiques (imports bannis, APIs interdites)
  ↓
public suite          → 5 cas publics contre oracle
  ↓
hidden suite          → 30 cas générés par hidden_tests.py
  ↓
PBT suite             → Hypothesis @given × N (via strategy_factory)
  ↓
complexity_profile    → ratio t(large) / t(small) vs ratio_max par complexité cible
  ↓
ast_features          → extraction bisect, heapq, fenwick, kmp, deque, union_find…
  ↓
paradigm_classifier   → detect_paradigms() → is_genuine_divergence()
  ↓
salieri_minhash       → Jaccard 5-grams tokens normalisés (anti-copie oracle)
  ↓
scoring.py            → score ∈ [0, 1]
```

### 4.2 Modules en détail

#### `ast_features.py`

Extrait les features algorithmiques d'un code source Python via `ast.parse`. Features détectées :

| Feature                  | Méthode de détection                                                              |
| ------------------------ | --------------------------------------------------------------------------------- |
| `recursion`              | `_RecursionVisitor` : appel récursif à la fonction courante                       |
| `heapq`                  | Import `heapq` ou appel `heappush` / `heappop`                                    |
| `bisect`                 | Import `bisect` ou appel `bisect_left` / `bisect_right`                           |
| `deque`                  | Import `collections` + usage `deque`                                              |
| `dict_memo`              | Variable nommée `memo`, `cache`, ou `lru_cache`                                   |
| `union_find`             | Variables `parent`/`rank`/`find`/`union` ET motif `find`                          |
| `fenwick`                | Mot-clé `fenwick` OU patterns `i & -i`, `idx & -idx`, `index & -index`, `bit & -` |
| `kmp_prefix_table`       | Variables `prefix`, `lps`, `pi`, `border`, `failure`                              |
| `rolling_hash`           | Mot-clé `rolling` OU (`hash` + `base` + `mod` dans les variables)                 |
| `z_algorithm`            | Mot-clé `z_algorithm` OU (`z` + `left` + `right` dans les variables)              |
| `adjacency_list`         | Variables `graph`, `adj`, `neighbors`, `adjacency`                                |
| `coordinate_compression` | Pattern `sorted(set(` OU (`rank` + `values`)                                      |
| `nested_loops`           | Comptage des boucles imbriquées                                                   |

#### `paradigm_classifier.py`

Définit `PARADIGM_SIGNATURES` : un dictionnaire de 30 paradigmes → conditions sur les features AST.

Exemples de signatures :

```python
"kmp":                          {"kmp_prefix_table": True},
"rolling_hash_with_verification": {"rolling_hash": True},
"monotonic_deque":              {"deque": True, "adjacency_list": False},
"fenwick_tree":                 {"fenwick": True, "coordinate_compression": False},
"union_find":                   {"union_find": True},
"topological_dp":               {"deque": True, "adjacency_list": True, "recursion": False},
"dijkstra_heap":                {"heapq": True, "adjacency_list": True},
```

Fonctions principales :

- `paradigm_distance(candidate_features, oracle_features)` → distance cosinus entre vecteurs de features (12 features binaires + `nested_loops` normalisé)
- `detect_paradigms(features, known_paradigms)` → filtre les paradigmes connus qui matchent les features
- `is_genuine_divergence(candidate_features, oracle_features, known_paradigms)` → `(bool, list[str], list[str])`

La divergence est genuine si et seulement si `candidate_paradigms ∩ oracle_paradigms = ∅`, avec les deux ensembles non vides.

#### `salieri_minhash.py`

Calcule la similarité Jaccard entre le candidat et l'oracle sur des 5-grammes de tokens Python normalisés. Les tokens `NAME`, `NUMBER`, `STRING` sont remplacés par leur type (`NAME`, `NUM`, `STR`) pour neutraliser les renommages de variables. Seuil de mémorisation : `SALIERI_MEMORISATION_THRESHOLD = 0.70`.

**Rôle réel** : anti-plagiat de l'oracle du dépôt. Ne détecte pas la contamination depuis le corpus d'entraînement.

#### `hidden_tests.py`

Génère les cas cachés à partir des oracles. Taille par défaut : `n ∈ [100, 500]`. Tailles de stress test pour le profil de complexité :

| Complexité cible | small_size | large_size | ratio_max |
| ---------------- | ---------- | ---------- | --------- |
| O(n log n)       | 1 000      | 10 000     | 30.0      |
| O(n + m)         | 1 000      | 10 000     | 20.0      |
| O((n + m) log n) | 500        | 5 000      | 35.0      |
| O(n)             | 1 000      | 10 000     | 15.0      |
| O((u + q) log n) | 1 000      | 10 000     | 35.0      |
| O(log n)         | 10 000     | 1 000 000  | 5.0       |

---

## 5. Système de métriques — spécification complète

### 5.0 Profil multi-axes (v0.3+, principal)

> **Depuis v0.3, TR-CodeBench reporte un profil de 5 métriques indépendantes** au lieu d'un score composite unique. Chaque axe est interprétable seul et agrégeable séparément.

| Axe             | Clé JSON      | Échelle          | Ce qu'il mesure                                     |
| --------------- | ------------- | ---------------- | --------------------------------------------------- |
| **Correctness** | `correctness` | 0 ou 1 (binaire) | Tous les tests publics + cachés passent             |
| **Robustness**  | `robustness`  | [0, 1] continu   | Résistance au PBT (property-based testing)          |
| **Efficiency**  | `efficiency`  | [0, 1] ou `null` | Conformité au régime de complexité attendu          |
| **Divergence**  | `divergence`  | [0, 1] ou `null` | Divergence de paradigme vs l'oracle                 |
| **Safety**      | `safety`      | 0 ou 1 (binaire) | Absence de crash, violation statique, hallucination |

**Propriétés clés :**

- Chaque axe est **indépendant** : on peut comparer deux modèles sur un axe précis
- `null` signifie "non évaluable" (ex: efficiency si correctness = 0)
- Agrégation par modèle = moyenne par axe (les `null` sont exclus)
- Pas de pondération arbitraire entre les axes

```python
# Sortie JSON (metrics_profile)
{
  "correctness": 1.0,
  "robustness": 0.92,
  "efficiency": 0.78,
  "divergence": 0.45,
  "safety": 1.0
}
```

#### Calcul de chaque axe

```python
# Correctness (gate binaire)
correctness = 1.0 if public_pass_rate == 1.0 AND hidden_pass_rate == 1.0 else 0.0

# Robustness
robustness = 0.7 × pbt_gate_passed + 0.3 × pbt_group_pass_rate

# Efficiency (continu, utilise le ratio brut)
if correctness < 1.0 or complexity_ratio_ok is None:
    efficiency = null
elif complexity_ratio_ok == False:
    efficiency = 0.0
else:
    efficiency = clamp(1.0 − ratio / ratio_max, 0, 1)

# Divergence (continu, avec gates)
if correctness < 1.0:
    divergence = null
elif complexity_ratio_ok == False:
    divergence = 0.0
elif salieri_overlap > 0.70 or paradigm_distance < 0.20:
    divergence = 0.0
else:
    divergence = HM(paradigm_distance, 1 − salieri_overlap)
    if is_genuine_divergence: divergence = min(1.0, divergence × 1.2)

# Safety (binaire inversé)
safety = 0.0 if (static_violation OR crash OR hidden_pass_rate < 1.0) else 1.0
```

### 5.1 Métriques brutes

| Métrique              | Type        | Description                                          |
| --------------------- | ----------- | ---------------------------------------------------- |
| `public_pass_rate`    | float [0,1] | Taux de réussite sur les 5 cas publics               |
| `hidden_pass_rate`    | float [0,1] | Taux de réussite sur les ≥ 30 cas cachés             |
| `pbt_gate_passed`     | bool        | Tous les groupes PBT passent                         |
| `pbt_group_pass_rate` | float [0,1] | Proportion de groupes PBT réussis                    |
| `static_violation`    | bool        | Violation AST statique (import banni, API interdite) |
| `crash`               | bool        | Exception non attrapée lors de l'exécution           |
| `timeout`             | bool        | Dépassement du timeout (1 s par cas)                 |
| `salieri_overlap`     | float [0,1] | Jaccard 5-grams tokens normalisés vs oracle          |
| `paradigm_distance`   | float [0,1] | Distance cosinus features AST candidat/oracle        |
| `productivity_score`  | float [0,1] | HM(efficiency_from_ratio, pbt_pass_rate)             |
| `complexity_ratio_ok` | bool ∣ None | t_large/t_small ≤ ratio_max (None si indéterminé)    |

### 5.2 Score composite legacy (DEPRECATED)

> ⚠️ Le score composite ci-dessous est conservé pour backward-compatibility mais **ne constitue plus la métrique principale**. Utiliser `metrics_profile` pour toute nouvelle analyse.

```python
# Correctness
correctness_score = 1.0 if public_pass_rate == 1.0 AND hidden_pass_rate == 1.0 else 0.0

# Robustness (PBT)
robustness_score = 0.7 × pbt_gate_passed + 0.3 × pbt_group_pass_rate
effective_correctness = min(correctness_score, 0.65) if NOT pbt_gate_passed else correctness_score

# Optimization
optimization_score = 1.0 if correctness_score AND complexity_ratio_ok else 0.0
# (si complexity_ratio_ok is None et pas de timeout → 1.0 par défaut)

# Productive Divergence
pd_score = HM(paradigm_distance, productivity_score, 1 − salieri_overlap)
           si correctness_score = 1
              AND complexity_ratio_ok ≠ False
              AND salieri_overlap ≤ 0.70
              AND paradigm_distance ≥ 0.20
           sinon 0

# Score final
hallucination_flag = static_violation OR crash OR hidden_pass_rate < 1.0

raw = 0.50 × effective_correctness
    + 0.20 × robustness_score
    + 0.15 × optimization_score
    + 0.15 × pd_score
    − 0.25 × hallucination_flag

score = clamp(raw, 0, 1)
# Plafond : si complexity_ratio_ok = False → score ≤ 0.60
```

### 5.3 Niveaux de score attendus

| Situation                              | Score attendu           |
| -------------------------------------- | ----------------------- |
| Incorrect (echec tests)                | 0.00                    |
| Violation statique                     | ≤ 0.00 (pénalité −0.25) |
| Correct + PBT + optimal + pas de PD    | **0.85**                |
| Correct + PBT + optimal + PD partielle | 0.85–0.95               |
| Correct + PBT + optimal + PD genuine   | **~1.00**               |
| Correct + mauvaise complexité          | ≤ 0.60 (plafonné)       |

La masse des solutions correctes sans PD détectée converge vers **0.85**. C'est la signature la plus fréquente dans les runs actuels.

### 5.4 Seuils

```python
SALIERI_MEMORISATION_THRESHOLD = 0.70   # Au-dessus : trop similaire à l'oracle → pd_score = 0
PARADIGM_COSMETIC_THRESHOLD    = 0.20   # En dessous : distance trop faible → pd_score = 0
```

---

## 6. Les 10 items prototypes

| ID                | Problème                                    | Complexité cible | Paradigme oracle (principal)    | Known valid paradigms                                                          |
| ----------------- | ------------------------------------------- | ---------------- | ------------------------------- | ------------------------------------------------------------------------------ |
| `trcb-proto-0001` | LIS                                         | O(n log n)       | `patience_sorting`              | patience_sorting, fenwick_tree_coordinate_compression                          |
| `trcb-proto-0002` | Plus court chemin (poids positifs)          | O((n+m) log n)   | `dijkstra_heap`                 | dijkstra_heap, a_star_with_zero_heuristic, bucketed_dijkstra_for_small_weights |
| `trcb-proto-0003` | Planification d'intervalles                 | O(n log n)       | `greedy_by_finish_time`         | greedy_by_finish_time, sweep_line_variant, lazy_heap                           |
| `trcb-proto-0004` | Plus court sous-tableau de somme ≥ cible    | O(n)             | `monotone_queue_generalization` | monotone_queue_generalization, two_pointers, block_prefix_suffix               |
| `trcb-proto-0005` | Connectivité par union-find                 | near-linear      | `union_find`                    | union_find, component_labeling_after_build, dfs_memoization                    |
| `trcb-proto-0006` | Recherche exacte de motif                   | O(n+m)           | `kmp`                           | kmp, rolling_hash_with_verification, z_algorithm                               |
| `trcb-proto-0007` | Maximum de fenêtre glissante                | O(n)             | `monotonic_deque`               | monotonic_deque, block_prefix_suffix, dynamic_programming_with_sorting         |
| `trcb-proto-0008` | Plus long chemin dans un DAG                | O(n+m)           | `topological_dp`                | topological_dp, dfs_memoization, relaxation_in_known_topological_order         |
| `trcb-proto-0009` | Mises à jour ponctuelles + sommes de plages | O(log n)         | `fenwick_tree`                  | fenwick_tree, segment_tree, sqrt_decomposition                                 |
| `trcb-proto-0010` | Ordonnancement par heap                     | O(n log n)       | `greedy_heap`                   | greedy_heap, balanced_tree_scheduler, event_sweep_with_priority_queue          |

---

## 7. État de l'art et positionnement

### 7.1 Grille comparative

| Benchmark            | Correctness | Tests cachés | Complexité vérifiée | Diversité paradigmes      | Anti-contamination | Tâches réelles    |
| -------------------- | ----------- | ------------ | ------------------- | ------------------------- | ------------------ | ----------------- |
| HumanEval (2021)     | ✓           | —            | —                   | —                         | —                  | Synthétique       |
| EvalPlus (2023)      | ✓           | ✓ (×80)      | —                   | —                         | —                  | Synthétique       |
| LiveCodeBench (2024) | ✓           | ✓            | —                   | —                         | ✓ (post-cutoff)    | Compétitif        |
| APPS (2021)          | ✓           | ✓            | —                   | —                         | —                  | Compétitif        |
| SWE-bench (2024)     | ✓           | ✓            | —                   | —                         | ✓                  | Maintenance repo  |
| BigCodeBench (2024)  | ✓           | ✓            | —                   | —                         | —                  | Bibliothèques     |
| NeoCode (2025)       | ✓           | —            | —                   | ✓ (diversité output)      | ✓ (post-cutoff)    | Algorithmique     |
| **TR-CodeBench**     | **✓**       | **✓**        | **✓ (heuristique)** | **✓ (heuristique, 50 %)** | **Partielle**      | **Algorithmique** |

### 7.2 Apports différenciants

**Apport 1 — Contrainte de complexité comme dimension de scoring.**
Aucun benchmark mainstream ne pénalise explicitement une solution O(n²) quand O(n log n) est attendu. TR-CodeBench tente de le faire via un stress test empirique + `optimization_score`. C'est conceptuellement la contribution la plus différenciante.

**Apport 2 — Taxonomie des paradigmes valides par item.**
Le champ `known_valid_paradigms` est une annotation sémantique absente des autres benchmarks. Même si son exploitation est insuffisante en v0.2, c'est une contribution de structure de dataset pour la recherche.

**Apport 3 — PBT comme signal de robustesse.**
EvalPlus multiplie les exemples mais reste example-based. TR-CodeBench intègre Hypothesis pour une couverture dirigée par stratégie. C'est un signal de robustesse plus riche que les exemples supplémentaires d'EvalPlus.

### 7.3 TR-CodeBench vs NeoCode — la distinction théorique

| Dimension          | NeoCode                                               | TR-CodeBench                                     |
| ------------------ | ----------------------------------------------------- | ------------------------------------------------ |
| Mesure             | Divergence _distributionnelle_ vs corpus entraînement | Divergence _structurelle_ vs oracle de référence |
| Anti-contamination | Post-cutoff (robuste)                                 | Anti-copie oracle seulement (partielle)          |
| Sémantique         | Token-level diversity                                 | Paradigme algorithmique                          |
| Vérification       | Pass rate                                             | Pass rate + complexité + PD                      |

**La différence théorique est réelle.** NeoCode mesure "est-ce que le modèle restitue quelque chose de nouveau par rapport à l'entraînement ?". TR-CodeBench mesure "est-ce que le modèle utilise un algorithme structurellement différent de l'oracle de référence ?". Ce sont deux questions distinctes.

**La différence pratique est actuellement faible.** Avec 50 % de couverture du classifier de paradigmes, les deux benchmarks distinguent surtout "correct vs incorrect" et "similaire vs différent superficiellement".

---

## 8. Historique des versions et décisions

### 8.1 v0.1 — Prototype initial (run `20260512T130403Z`)

**Périmètre :** 3 modèles × 10 items (gpt-oss-20b, laguna-m.1:free, qwen3-235b-a22b-2507)

**Formule de score v0.1 :**

```python
pd_candidate = bool(correctness_score and metrics.get("salieri_overlap", 1.0) < 0.70)
optimization_score = 1.0 if correctness_score and not metrics.get("timeout", False) else 0.0
```

**Problèmes identifiés :**

_Bug 1 — `pd_candidate` mesure de la nouveauté cosmétique, pas le paradigme._
`salieri_overlap` est un Jaccard sur des n-grammes de 5 tokens normalisés. Un candidat qui ajoute des type hints (`List[int]` vs `list[int]`), renomme des variables, ou insère un docstring voit son overlap baisser sous 0.70 sans changer de paradigme. **Taux de faux positifs observé : ~60 %.**

Preuves concrètes :

- `trcb-proto-0007` (gpt-oss-20b) : oracle = `monotonic_deque`, candidat = `collections.deque` identique → salieri=0.432 → pd=True (**FAUX**)
- `trcb-proto-0006` (gpt-oss-20b) : oracle = KMP avec `prefix[]`, candidat = KMP avec `lps[]` + docstring → salieri=0.276 → pd=True (**FAUX**)
- `trcb-proto-0008` (gpt-oss-20b) : les deux utilisent Kahn's algorithm → salieri=0.507 → pd=True (**FAUX**)

_Bug 2 — `optimization_score` est un proxy de timeout, pas de complexité._
Les cas cachés utilisent des tailles n ∈ [100, 500]. Un O(n²) DP passe 1 s de timeout sur n=500. Le mécanisme ne vérifie pas empiriquement la classe de complexité.

_Bug 3 — `known_valid_paradigms` et `ast_features` calculés mais non utilisés dans `compute_score()`._

**Décision prise :** refonte du scoring pour v0.2.

### 8.2 Plan d'implémentation v0.2

Cinq étapes planifiées et exécutées :

1. **Créer `paradigm_classifier.py`** avec `PARADIGM_SIGNATURES`, `detect_paradigms()`, `paradigm_distance()`, `is_genuine_divergence()`
2. **Modifier `scoring.py`** : remplacer `pd_candidate` binaire par `pd_score` continu = HM(paradigm_distance, productivity_score, originality) ; conditionner sur seuils salieri et paradigm_distance
3. **Modifier `evaluate.py`** : appeler le classifier de paradigmes, calculer `productivity_score`, ajouter `complexity_profile` (ratio empirique t_large/t_small)
4. **Modifier `hidden_tests.py`** : ajouter les tailles de stress test par complexité cible
5. **Mettre à jour les JSON** : ajouter `oracle_ast_features` pré-calculées pour figer la référence oracle

### 8.3 v0.2 — Post-correction (run `20260512T142518Z`)

**Périmètre :** 5 modèles × 10 items (ajout de mistral-small-24b, nemotron-3-nano-30b)

**Changements effectifs :**

- `pd_candidate` binaire → `pd_score` continu basé sur `paradigm_classifier`
- `optimization_score` → conditionné sur `complexity_ratio_ok` (ratio empirique)
- `paradigm_classifier.py` créé avec 30 paradigmes
- `productivity_score` = HM(efficiency_from_ratio, pbt_pass_rate)

**Résultat sur les 6 faux positifs v0.1 identifiés :** tous corrigés. Taux de PD genuine : 60 % → ~14 % pour les paradigmes détectables.

**Nouveaux bugs identifiés en v0.2 :**

_Bug 4 — Oracle paradigm non détecté pour item 0009 (Fenwick tree)._
`ast_features.py` détectait `" i & -i"` et `"idx & -idx"` mais pas `"index & -index"` — le pattern utilisé par l'oracle 0009. Résultat : `oracle_paradigms = []` → `is_genuine_divergence()` retournait `False` (car oracle_paradigms vide). L'item 0009 ne pouvait jamais générer de vrai signal PD.

**Correction appliquée :** `"index & -index"` ajouté dans `ast_features.py` (présent dans la version actuelle du code).

_Bug 5 — `complexity_ratio_ok = True` pour 100 % des runs mesurés._
Les ratios observés : 0.84–2.02. Les 5 modèles testés produisent tous des solutions efficaces. Le mécanisme n'a jamais été confronté à une vraie solution naïve en conditions réelles. Discrimination nulle sur le run v0.2.

**Statut :** non résolu — voir Section 9.

### 8.4 v0.3 — Run actuel (run `openrouter_eval_20260512T220239Z`)

Même base de code que v0.2, 50 évaluations (5 modèles × 10 items). Voir Section 10 pour les résultats.

---

## 9. Bugs connus et dettes techniques

### 9.1 `complexity_ratio_ok` non validé sur solutions naïves ⚠️ CRITIQUE

**Symptôme :** `complexity_ratio_ok = True` pour 100 % des 31 runs mesurés sur le run v0.3. Les ratios varient entre 0.84 et 2.02.

**Cause probable :** les 5 modèles testés produisent tous des solutions efficaces. Le stress test n'a jamais vu une vraie solution O(n²) en conditions réelles.

**Impact :** `optimization_score` vaut 1.0 pour toutes les solutions correctes. Le mécanisme de discrimination de régime n'a aucun pouvoir discriminant dans les runs actuels.

**Correction recommandée :**

```python
# Dans tests/unit/test_evaluator.py — ajouter :
def test_naive_lis_fails_complexity():
    result = evaluate_candidate("trcb-proto-0001", "candidates/naive_lis_o_n2.py")
    assert result["score"]["optimization_score"] == 0.0
    assert result["metrics"]["complexity_ratio_ok"] == False
```

Il faut au moins une solution naïve O(n²) par item avec contrainte O(n log n) dans la suite de tests.

### 9.2 Couverture du classifier à 50 % ⚠️

Sur 30 paradigmes définis dans `known_valid_paradigms` des 10 items, ~15 ne sont pas détectables par `paradigm_classifier.py` :

| Paradigme non détectable         | Raison                                                                |
| -------------------------------- | --------------------------------------------------------------------- |
| `rolling_hash_with_verification` | Variables `base`, `mod` peuvent être nommées n'importe comment        |
| `z_algorithm`                    | Indistinguable de KMP à l'AST (même structure de features)            |
| `segment_tree`                   | Peut s'écrire itérativement ou récursivement ; features insuffisantes |
| `dfs_memoization`                | Indistinguable d'une DP récursive générique                           |
| `sweep_line_variant`             | Aucune feature caractéristique                                        |
| `prefix_sums_binary_search`      | `bisect` présent aussi dans `patience_sorting`                        |
| `block_prefix_suffix`            | Aucune feature signature                                              |
| `component_labeling_after_build` | Confondu avec `dfs_memoization`                                       |

**Impact :** 79 % des solutions correctes obtiennent 0.85 sans signal PD, même si le paradigme est objectivement différent de l'oracle.

### 9.3 PBT non shrinkable

`evaluate.py` appelle `strategy.example()` N fois via `@given`. Hypothesis est utilisé comme générateur d'exemples, pas comme moteur de vérification avec shrinking. Pas de directed search, pas de stateful testing. La couverture dépend entièrement de la qualité des stratégies écrites à la main.

### 9.4 README divergent du code

`README.md` décrit l'ancien scoring binaire `pd_candidate`. Le code actif utilise `pd_score` continu depuis v0.2. Cette divergence est une dette de documentation qui rend le benchmark difficile à citer dans un papier.

### 9.5 Sandbox social, pas technique

`run_candidate.py` exécute le candidat en sous-processus avec timeout. Pas d'isolation réseau, pas de chroot, pas de cgroups, pas de seccomp. La séparation entre données visibles (prompt) et données cachées (hidden tests, oracle) repose sur la discipline du développeur.

---

## 10. Résultats des runs et observations

### 10.1 Run v0.3 — `openrouter_eval_20260512T220239Z`

**Résumé global (50 évaluations) :**

| Métrique                   | Valeur         |
| -------------------------- | -------------- |
| Total runs                 | 50             |
| Correctness = 1.0          | 32 / 50 (64 %) |
| PD score > 0               | 4 / 50 (8 %)   |
| Hallucinations             | 8 / 50 (16 %)  |
| Mean score                 | 0.540          |
| complexity_ratio_ok = True | 31 / 50 (62 %) |

**Par modèle :**

| Modèle                          | Moy. score | Correct | PD > 0 |
| ------------------------------- | ---------- | ------- | ------ |
| laguna-m.1:free                 | 0.864      | 10/10   | 2/10   |
| gpt-oss-20b                     | 0.833      | 10/10   | 1/10   |
| qwen3-235b-a22b-2507            | 0.771      | 9/10    | 1/10   |
| nemotron-3-nano-30b-a3b:free    | 0.230      | 3/10    | 0/10   |
| mistral-small-24b-instruct-2501 | 0.000      | 0/10    | 0/10   |

**Distribution des scores :**

| Score     | Runs | Interprétation                                |
| --------- | ---- | --------------------------------------------- |
| 0.00      | 18   | Solutions incorrectes ou violations statiques |
| 0.60      | 2    | Plafonné — contrainte de complexité violée    |
| 0.85      | 26   | Masse des solutions correctes canoniques      |
| 0.91–0.93 | 4    | PD partielle détectée                         |

### 10.2 Observations clés

**Observation 1 — Le benchmark distingue surtout "correct vs incorrect".**
L'écart dominant est entre 0.85 et 0.00. La discrimination à l'intérieur de l'espace des solutions correctes est embryonnaire (0.85 vs 0.91–0.93).

**Observation 2 — mistral-small-24b produit 0/10 de solutions correctes.**
Ce modèle génère systématiquement des solutions incorrectes ou avec violations statiques. Il peut servir de baseline basse mais son signal est binaire.

**Observation 3 — PD genuine reste rare (4/50 runs, 8 %).**
Les 4 cas PD>0 viennent de laguna-m.1:free (2), gpt-oss-20b (1), qwen3 (1). Tous utilisent un paradigme différent de l'oracle sur des items où le classifier couvre la divergence.

**Observation 4 — Aucune solution naïve n'a été produite.**
`complexity_ratio_ok = True` pour 100 % des solutions correctes. Le mécanisme de True Regime n'a jamais été activé négativement sur ce run.

---

## 11. Revue critique — lacunes structurelles

### 11.1 La pénalité de régime est insuffisante

Une solution O(n²) correcte plafonne à 0.60. L'écart 0.85 (bon régime) − 0.60 (mauvais régime) = 0.25 est faible pour un benchmark dont la proposition centrale est le régime algorithmique.

**Option :** augmenter la pondération `optimization` :

```
# Option plus agressive :
score = 0.50 × correctness + 0.20 × pbt + 0.25 × optimization + 0.05 × pd
```

### 11.2 Le classifier de paradigmes est incomplet (50 % de couverture)

Sur 30 paradigmes valides définis dans les 10 items, 15 ne sont jamais détectables. Voir Section 9.2.

### 11.3 L'anti-contamination est partielle

`salieri_minhash` détecte la copie de l'oracle du dépôt, pas la mémorisation depuis le corpus d'entraînement. Pour des problèmes classiques (LIS, Dijkstra, KMP), le risque de contamination depuis GitHub ou The Stack est élevé et non mesuré. LiveCodeBench résout ce problème avec des problèmes post-cutoff.

### 11.4 La vérité terrain de l'oracle n'est pas toujours gelée

Si `oracle_ast_features` n'est pas présent dans le JSON, `evaluate.py` re-détecte les features de l'oracle à chaque run depuis le code source. Un bug dans `ast_features.py` peut changer rétrospectivement la classification de l'oracle.

### 11.5 PD mesure la divergence de l'oracle, pas de l'espace des solutions

Même si le classifier était parfait, il répond uniquement à "le candidat utilise-t-il un paradigme différent de _cet_ oracle ?". Si deux modèles produisent tous deux Z-algorithm (paradigme non détecté), ils sont pénalisés de la même façon quelle que soit leur vraie divergence inter-candidats.

### 11.6 Verdict sur la PD

**TR-CodeBench ne mesure pas encore de la Productive Divergence au sens théorique fort.** Il mesure une approximation composite : `paradigm_distance` (cosinus sur features AST) × `productivity_score` × `originality` (1 − Jaccard). C'est mieux que NeoCode car il y a une couche sémantique, mais ce n'est pas encore une mesure formelle de divergence de paradigme. Le benchmark est à mi-chemin entre "nouveau dataset de diversité algorithmique" et "benchmark de régime de vérité".

---

## 12. Recommandations et feuille de route

### 12.1 Priorité 1 — Valider le discriminant de complexité (immédiat)

Créer `candidates/naive_lis_o_n2.py` (DP O(n²)) et ajouter un test d'intégration :

```python
def test_naive_lis_complexity_rejected():
    r = evaluate_candidate("trcb-proto-0001", "candidates/naive_lis_o_n2.py")
    assert r["score"]["optimization_score"] == 0.0
    assert r["metrics"]["complexity_ratio_ok"] == False
```

Faire de même pour les items 0002 (Dijkstra vs Bellman-Ford O(nm)), 0006 (KMP vs brute-force O(nm)), 0009 (Fenwick vs tableau direct O(n) par requête).

### 12.2 Priorité 2 — Étendre le classifier à 80 % de couverture

**Signatures structurelles améliorées :**

- `z_algorithm` : absence de `prefix/lps` + présence de tableau `z[]` + variables `l` et `r` (left/right)
- `segment_tree` : récursion + au moins 2 boucles imbriquées OU pattern `build_tree`/`update_tree`
- `rolling_hash_with_verification` : `hash` + multiplication par une puissance + modulo prime

**LLM-judge léger pour les paradigmes ambigus :**

```python
# Dans paradigm_classifier.py — extension optionnelle
def llm_detect_paradigm(source: str, candidates: list[str], model: str = "haiku") -> str | None:
    """Fallback LLM judge pour paradigmes AST-ambigus."""
    ...
```

### 12.3 Priorité 3 — Pré-calculer et geler `oracle_ast_features`

Pour chaque item, calculer une fois les features AST de l'oracle et les stocker dans `oracle["oracle_ast_features"]`. Cela fixe la référence oracle indépendamment des évolutions de `ast_features.py`.

### 12.4 Priorité 4 — Aligner README et code

La section "Scoring V0.2" du README doit décrire la formule continue avec `pd_score = HM(...)` et supprimer toute référence à `pd_candidate`.

### 12.5 Priorité 5 — Items post-cutoff (moyen terme)

Pour distinguer TR-CodeBench de NeoCode sur l'anti-contamination, introduire 20–30 % d'items post-cutoff dans la cible de 100 items :

- Nouveaux algorithmes publiés après le cutoff des modèles testés
- Variantes procédurales générées avec seed documenté
- Problèmes issus de compétitions récentes non indexées

### 12.6 Roadmap de scaling vers 100 items

Ordre d'expansion recommandé :

1. Valider + hardener les 10 items paramétriques existants (tests naïves, oracle gelées)
2. Ajouter 30 items algorithmiques paramétriques (mêmes structure, nouveaux domaines)
3. Ajouter 25 fonctions isolées extraites de repos Python réels
4. Ajouter 20 tâches de refactoring / optimisation de PR
5. Ajouter 10 tâches post-cutoff
6. Ajouter 5 honeypots hors score principal (détection de triche / hallucination)

---

## Annexes

### A. Décisions d'architecture notables

| Décision                                    | Alternatives considérées   | Raison du choix                                                                       |
| ------------------------------------------- | -------------------------- | ------------------------------------------------------------------------------------- |
| Exécution locale (pas de sandbox cloud)     | Docker, E2B, Modal         | Simplicité du prototype, pas de coût infra                                            |
| Distance cosinus pour `paradigm_distance`   | Hamming, Euclidien         | Insensible à la magnitude des vecteurs — adapté aux features binaires                 |
| Jaccard 5-grams de tokens pour Salieri      | AST fingerprint, embedding | Robuste aux renommages, léger, implémentable sans modèle                              |
| HM à 3 composantes pour `pd_score`          | Somme pondérée             | La moyenne harmonique impose un minimum non nul sur toutes les composantes            |
| `known_valid_paradigms` dans le JSON        | Ontologie centralisée      | Permet la spécificité par item — un paradigme valide pour 0006 ne l'est pas pour 0001 |
| Hypothesis comme générateur (pas shrinking) | Shrinking activé           | Benchmark = détection d'erreur, pas débogage → shrinking inutile, coûteux             |

### B. Références

- **HumanEval** : Chen et al., "Evaluating Large Language Models Trained on Code", 2021
- **EvalPlus** : Liu et al., "Is Your Code Generated by ChatGPT Really Correct?", NeurIPS 2023
- **LiveCodeBench** : Jain et al., "LiveCodeBench: Holistic and Contamination Free Evaluation", 2024
- **SWE-bench** : Jimenez et al., "SWE-bench: Can Language Models Resolve Real-World GitHub Issues?", ICLR 2024
- **BigCodeBench** : Zhuo et al., "BigCodeBench: Benchmarking Code Generation with Diverse Function Calls and Complex Instructions", 2024
- **NeoCode** : benchmark de diversité distributionnelle post-cutoff (référence à compléter)
- **Hypothesis** : MacIver et al., "Hypothesis: A new approach to property-based testing", JOSS 2019

### C. Glossaire

| Terme                          | Définition                                                                                                                       |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| **T2 / Truth Regime**          | Régime de vérité fort : réponse vérifiable par exécution, plusieurs paradigmes valides, latitude stratégique élevée              |
| **PD / Productive Divergence** | Solution correcte + optimale + utilisant un paradigme distinct de l'oracle                                                       |
| **Salieri overlap**            | Jaccard similarity sur 5-grams de tokens Python normalisés (proxy anti-copie oracle)                                             |
| **paradigm_distance**          | Distance cosinus entre vecteurs de features AST candidat/oracle                                                                  |
| **productivity_score**         | HM(efficiency_from_ratio, pbt_pass_rate)                                                                                         |
| **oracle**                     | Solution de référence choisie par le créateur d'item — n'est pas "la bonne réponse" mais la référence pour mesurer la divergence |
| **known_valid_paradigms**      | Liste par item des paradigmes algorithmiques acceptables déclarés                                                                |
| **hallucination_flag**         | Violation statique OU crash OU hidden_pass_rate < 1.0                                                                            |
| **complexity_ratio_ok**        | `True` si t(large)/t(small) ≤ ratio_max, `False` sinon, `None` si mesure indéterminée                                            |

---

_Document généré le 2026-05-20 à partir de l'analyse du dépôt TR-CodeBench, des runs `20260512T130403Z` (v0.1), `20260512T142518Z` (v0.2) et `20260512T220239Z` (v0.3), et du code source des modules `scoring.py`, `evaluate.py`, `paradigm_classifier.py`, `ast_features.py`, `salieri_minhash.py`._
