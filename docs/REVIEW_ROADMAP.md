# TR-CodeBench — Revue empirique & académique + Feuille de route

> Document de supervision de recherche. Daté du 2026-05-24. Ancré dans le code réel
> du dépôt (`src/trcodebench/`), le run live à 40 items
> (`reports/openrouter_runs/openrouter_eval_20260524T135547Z`), le notebook
> d'analyse (`notebooks/trcb_analysis.ipynb`), et le position paper
> *« Hallucination Is Relative: Evaluating LLM Divergence Under Truth-Regime Contracts »* (UAI 2026).
>
> Convention de lecture : **(A)** = établi dans la littérature ou le code, **(B)** =
> contribution propre du benchmark, **(C)** = spéculation / travail futur. Les
> références non présentes dans la bibliographie du position paper sont marquées
> *« à vérifier »*.

---

## 0. Résumé exécutif

**Thèse à défendre (reformulée).** TR-CodeBench est l'instanciation *exécutable* du
cadre du position paper. Là où le position paper mesure, sur du texte, quand la
divergence devient hallucination (H) plutôt que productive divergence (PD) sous un
régime de vérité **documentaire** (oracle = Wikipédia, vérification NLI bruitée),
TR-CodeBench fait la même chose sous un régime de vérité **exécutable** : l'oracle
est du code testable, donc la frontière H / PD est instrumentable. C'est l'angle
fort, et il répond directement aux *open problems* #5 (« Controlling H without
collapsing PD ») et #6 (« Benchmarks crossing task × CI × TR ») de ton agenda.

**Verdict.** L'idée est publiable ; l'exécution empirique ne l'est pas encore. Le
benchmark, dans son run actuel, discrimine essentiellement *correct vs incorrect*.
Le signal qui fait sa singularité — la Productive Divergence — ne se déclenche
presque jamais : sur 320 évaluations, `genuine_divergence = True` n'apparaît que
**2 fois (0,6 %)**. Tant que la PD ne discrimine pas les modèles compétents, le
papier reste un benchmark de pass-rate avec une couche décorative.

**Note provisoire (inchangée sur le fond, révisée à la hausse sur la maturité du code).**

| Dimension | Note /10 | Commentaire |
| --- | --- | --- |
| Idée scientifique | 7 | Divergence vérifiable sous oracle exécutable = niche réelle |
| Implémentation (ingénierie) | 6.5 | Pipeline complet, denial + evidence stack, 40 items, run live fait |
| Validation empirique | 4 | PD quasi inerte, 1 seul run, 37 % d'erreurs API, seuils non calibrés |
| Maturité publication | 4.5 | Validité de construit non démontrée ; comparaison SOTA à formaliser |

**Trois priorités absolues (P0).**

1. **Rendre la PD discriminante** : refondre la métrique de divergence (aujourd'hui
   cosinus binaire AST, dépendant du nommage) et calibrer ses seuils sur des
   distributions réelles. C'est *le* verrou.
2. **Un protocole de mesure défendable** : runs répétés (≥ 3 seeds), modèles qui
   répondent réellement (le run actuel a 37,5 % d'erreurs API), fiabilité inter-run.
3. **Prouver que chaque axe mesure ce qu'il prétend** : matrice de validation par
   item (oracle / naïf / alternative valide / quasi-copie / dangereux / quasi-correct)
   et gold set humain de paradigmes.

**Ce que ce document corrige par rapport aux revues antérieures (faites sur docs, pas sur code).**
`pyproject.toml` **n'est plus vide** (1386 octets, restauré le 24 mai) ; les
**baselines naïves existent** (`candidates/`, 4 items) ; le **run live à 40 items
est fait**. Les revues précédentes traitaient ces points comme « à faire » : ils
sont partiellement traités. Le vrai front ouvert n'est plus l'ingénierie, c'est la
**validité de mesure**.

---

## 1. Cadre conceptuel : TR-CodeBench comme régime de vérité exécutable

### 1.1 Du position paper au code

Le position paper formalise un régime de vérité `TR(p) = (O, σ, κ)` : un oracle `O`,
une latitude stylistique `σ`, une licence d'invention `κ`. Une hallucination est une
**violation de régime** ; une PD est un écart **autorisé, utile et conforme**. En
texte, `κ` désigne l'invention de *faits*. En code, il faut spécialiser ce vocabulaire,
sinon « invention » devient ambigu.

**Proposition — `TR-Code(p) = (O_exec, Σ, Κ_alg, C, S, A)`** *(B)* :

| Élément | Définition | Réalisé dans le code ? |
| --- | --- | --- |
| `O_exec` | oracle exécutable : tests publics + cachés + PBT | ✅ `evaluate.py`, `hidden_tests.py` |
| `Σ` | latitude stylistique (nommage, type hints, structure) | implicite (neutralisée par Salieri) |
| `Κ_alg` | **licence d'invention algorithmique** : autoriser un paradigme ≠ oracle | ✅ `known_valid_paradigms` |
| `C` | contrat de complexité asymptotique | ✅ `optimization_constraints`, stress test |
| `S` | contrat de sécurité (imports/API interdits) | ✅ `static_checks.py` |
| `A` | contrat de signature/API | ✅ `task.signature`, `allowed_imports` |

La clé théorique : en code, `κ` ne porte **pas** sur la vérité sémantique (qui reste
stricte — la solution doit être correcte) mais sur **le chemin algorithmique**. La
liberté créative est déplacée du *quoi* (résultat, non négociable) vers le *comment*
(stratégie, espace ouvert). C'est exactement ce qui rend le cas « code » plus propre
que le cas « texte » : la nouveauté peut diverger sans jamais mentir.

### 1.2 Le bon cadrage : « controlled divergence », pas « hallucination créative »

Je recommande d'éviter, comme thèse centrale, la formule *« le côté créatif des
hallucinations »*. Dans ton propre cadre, une hallucination **reste** une violation
de régime ; ce n'est pas une hallucination « réussie ». Ce que tu mesures, c'est le
**mécanisme génératif commun** — la capacité à diverger — qui devient H s'il casse le
contrat, ou PD s'il reste valide. La phrase pivot du papier devrait être *(B)* :

> *TR-CodeBench evaluates when code-generation divergence becomes productive rather
> than hallucinatory under an executable truth regime.*

Cette formulation te distingue nettement de Sun et al. (« Hallucinating LLM Could Be
Creative ») et de Banerjee et al. 2025 (« Does Less Hallucination Mean Less
Creativity? ») : eux posent la corrélation ; toi tu poses la **frontière** et tu la
rends **vérifiable**.

### 1.3 Taxonomie des sorties (à exposer comme verdict unique)

Le profil 5 axes est bon mais il manque un **verdict lisible** par run, qui matérialise
la taxonomie du position paper appliquée au code *(B)* :

| Verdict `tr_verdict` | Condition | Lecture |
| --- | --- | --- |
| `TR_VIOLATION` | échec correctness OU `safety=0` OU complexité hors contrat | hallucination de code (H_code) |
| `VALID_CONVERGENT` | correct + efficace + sûr, mais paradigme ≈ oracle | résout, ne diverge pas |
| `PRODUCTIVE_DIVERGENCE` | correct + efficace + sûr + paradigme distinct **confirmé** | PD_code |
| `INVALID_DIVERGENCE` | diverge mais casse un contrat (complexité, sécurité, signature) | divergence non productive |
| `UNDETERMINED` | divergence non décidable (classifier abstient) | à arbitrer (humain / LLM-judge) |

Ce verdict rend le papier directement présentable (une colonne, cinq valeurs) et
force à nommer le cas `INVALID_DIVERGENCE`, aujourd'hui invisible : un modèle qui
abandonne KMP pour une approche originale mais O(n·m) doit être distingué d'un modèle
canonique correct.

---

## 2. Forces réelles (ancrées dans le code)

1. **Régime de vérité exécutable multi-paradigmes.** Chaque item déclare 3–4
   `known_valid_paradigms` (moyenne 3,02 sur 40 items), un oracle scellé, des tests
   publics + cachés + une stratégie Hypothesis, et des `denial_constraints`. C'est une
   structure de dataset que ni HumanEval, EvalPlus, LiveCodeBench, ni BigCodeBench ne
   possèdent *(B)*.

2. **La complexité comme dimension de scoring.** Le stress test empirique
   (`hidden_tests.py`, ratios `t(large)/t(small)` vs `ratio_max`) est conceptuellement
   l'apport le plus différenciant : aucun benchmark mainstream ne pénalise une
   solution O(n²) là où O(n log n) est attendu *(B)*. (Réserve majeure en §3.)

3. **Trajectoires de déni.** `denial/` ré-interroge le modèle sous contraintes
   successives de paradigme/construct interdit, puis vérifie correctness **et** respect
   de la contrainte par AST (`verify_denial.py`). C'est la bonne réponse à la limite
   « PD = distance à *un* oracle » : on mesure l'**espace de solutions atteignable**,
   pas la distance à la référence. C'est aussi l'adaptation directe du *denial
   prompting* de NeoGauge/NeoCoder (Lu et al., arXiv:2407.09007) à un régime vérifiable.

4. **Profil multi-axes plutôt que score composite.** La migration de `scoring.py`
   (composite déprécié) vers `metrics_profile.py` (5 axes indépendants) est une bonne
   décision académique : elle évite de masquer les échecs derrière une pondération
   arbitraire. À finaliser (le notebook d'analyse rapporte encore le composite — §4).

5. **Pile d'évidence multi-couches.** `paradigm_evidence/` (AST + structural +
   dataflow + behavioral, fusion pondérée → accept/judge/abstain) attaque la fragilité
   du classifier sur les 4 paradigmes les plus durs. L'architecture est saine ; reste à
   la valider contre une vérité terrain (§5).

---

## 3. Diagnostic empirique — run du 24 mai (40 items)

Source : `openrouter_eval_20260524T135547Z` + `trcb_analysis.ipynb`. **8 modèles ×
40 items × 1 run = 320 évaluations**, dont **200 réponses valides** et **120 erreurs
API (37,5 %)**.

### 3.1 Chiffres clés

| Indicateur | Valeur | Lecture |
| --- | --- | --- |
| Erreurs API | 120 / 320 (37,5 %) | 3 modèles *free* à 0 % — données effectives ≈ 5 modèles |
| Correctness = 1 | 109 / 320 | 88 % (Laguna) → 0 % (modèles en échec API) |
| `mp_divergence` > 0 | 24 / 320 (7,5 %) | la PD reste rare, comme en v0.3 |
| `genuine_divergence` = True | **2 / 320 (0,6 %)** | le bonus de divergence ne se déclenche quasi jamais |
| Hallucinations (réponses valides) | 85 / 200 (**42 %**) | tests publics OK mais cachés/PBT/statique KO |
| Runs répétés (seeds) | **1** | aucune fiabilité test-retest possible |

Classement par modèle (notebook, §9) :

| Modèle | Correction | Optim. | PD score | Genuine PD | Score (composite) |
| --- | --- | --- | --- | --- | --- |
| poolside/laguna-m.1 | 0.875 | 0.875 | 0.135 | **0.000** | 0.755 |
| openrouter/owl-alpha | 0.550 | 0.525 | 0.034 | 0.000 | 0.471 |
| openai/gpt-oss-20b | 0.525 | 0.525 | 0.071 | 0.000 | 0.456 |
| qwen3-235b-a22b | 0.500 | 0.450 | 0.062 | 0.025 | 0.437 |
| mistral-small-24b | 0.275 | 0.250 | 0.075 | 0.025 | 0.249 |
| deepseek-v4-flash / gemma-4 / lfm-2.5 | 0.000 | — | — | — | 0.000 (API) |

### 3.2 Quatre constats qui conditionnent la suite

**Constat 1 — Le benchmark discrimine surtout correct/incorrect.** L'écart dominant
est entre ~0,85 (correct canonique) et 0 (incorrect). À l'intérieur de l'espace des
solutions correctes, la discrimination est embryonnaire. C'est exactement le verdict
de la §11.6 de la SPEC, désormais confirmé sur 40 items et non plus 10.

**Constat 2 — Le maillon faible est le classifier, prouvé par les chiffres.** Sur
109 solutions correctes : `paradigm_distance` moyen = **0,189**, soit *juste* sous le
seuil cosmétique de 0,20 ; **79/109 (72 %)** sont filtrées par le gate
`paradigm_distance < 0.20`, et **23/109 (21 %)** par le gate `salieri_overlap > 0.70`.
Le gate de distance fait donc tout le travail — et il est posé exactement au milieu de
la distribution. Un seuil non calibré au centre de la masse est un seuil qui décide par
hasard. **`genuine_divergence` à 0,6 %** confirme que la détection disjointe de
paradigmes (candidat ∩ oracle = ∅, les deux non vides) échoue presque toujours, faute
de couverture du classifier.

**Constat 3 — Le discriminant de complexité reste inerte en conditions réelles.** Le
notebook (§7) rapporte `complexity_ratio_ok = True` pour **120/120** solutions mesurées,
ratios entre 0,80 et 2,71, **médiane 1,03**, et avertit lui-même : *« si tous les
ratios sont proches de 1, les tailles de stress test sont peut-être trop petites pour
discriminer O(n²) de O(n log n) »*. Les baselines naïves trippent bien le mécanisme en
test unitaire (4 items), mais **aucun modèle n'a produit de solution naïve en live**,
donc l'axe efficiency n'a jamais discriminé négativement un modèle. Pire : `efficiency`
est `null` pour **38/109 (35 %)** des solutions correctes (mesure indéterminée). Un axe
non mesuré pour un tiers des cas n'est pas encore une métrique.

**Constat 4 — Pas de fiabilité, données polluées.** Un seul `run_index`, donc aucune
mesure de variance inter-run ; 37,5 % d'erreurs API ; 3 modèles à 0 %. Aucune
conclusion comparative n'est statistiquement défendable en l'état.

> **Signal intéressant mais à ne pas surinterpréter (n=2).** Le meilleur modèle en
> correction (Laguna, 88 %) a **zéro** divergence genuine ; les 2 cas genuine viennent
> de modèles plus faibles (Qwen3, Mistral). Cette dissociation correction ↔ divergence
> fait écho au position paper (les lesson plans hallucinent le plus sans scorer le plus
> haut en créativité), mais avec n=2 c'est du bruit. À retester proprement — c'est
> précisément le genre d'effet que le benchmark *doit* pouvoir mesurer s'il est valide.

---

## 4. Validité de construit — axe par axe

| Axe | Problème de validité (ancré dans `metrics_profile.py`) | Gravité |
| --- | --- | --- |
| `correctness` | OK. Gate binaire public ∧ hidden. | — |
| `safety` | `safety = 0` dès que `hidden_pass_rate < 1.0`. Or `correctness` exige déjà hidden = 1. **`safety` est donc quasi redondant avec `correctness`** : il n'apporte un signal indépendant que via `static_violation`/`crash`. À isoler (cf. ci-dessous). | moyenne |
| `robustness` | `0.7·pbt_gate + 0.3·pbt_rate` avec **défauts `pbt_gate=True`, `pbt_rate=1.0`** : si la donnée PBT manque, robustness = 1.0 (gonflement silencieux). | moyenne |
| `efficiency` | `null` pour 35 % des solutions correctes ; ratios ≈ 1 → non discriminant en live (Constat 3). | **haute** |
| `divergence` | proxy le plus fragile : cosinus sur 13 features binaires majoritairement **dépendantes du nommage** (`lps`, `pi`, `z`, `base`, `mod`…). Faux négatifs systématiques (Constat 2). Seuils non calibrés. | **critique** |

**Recommandations de séparation des axes** *(C)* :

- `safety` doit mesurer uniquement *contract_safety* (imports/API interdits, crash,
  I/O, réseau, mutation externe), **sans** réutiliser `hidden_pass_rate`. Sinon
  l'axe n'est pas indépendant — défaut rédhibitoire pour un argument multi-axes.
- `robustness` : remplacer les défauts optimistes par `null` quand la PBT n'a pas
  tourné, et exclure ces `null` de l'agrégat (comme efficiency/divergence).
- Renommer pour aligner code et cadre TR : `divergence → algorithmic_divergence`,
  `salieri_overlap → oracle_overlap`, `hallucination_flag → tr_violation_flag`.

> **Dette à corriger en priorité analytique** : le notebook `trcb_analysis.ipynb`
> rapporte encore le **composite déprécié** (`0.50×correct + 0.20×pbt + 0.15×optim +
> 0.15×pd − 0.25×halluc`) et un `pd_score` à 3 axes, alors que la métrique principale
> est le profil 5 axes. L'artefact d'analyse doit refléter la métrique du papier.

---

## 5. Concevoir une métrique de Productive Divergence robuste (le cœur)

C'est ici que se joue la contribution. Aujourd'hui, `divergence = HM(paradigm_distance,
1 − salieri_overlap)` avec gates. Trois faiblesses : (i) `paradigm_distance` est un
cosinus binaire fragile ; (ii) la nouveauté est mesurée **vs un seul oracle**, pas vs
l'espace des solutions ni une distribution humaine ; (iii) les seuils sont posés à
l'intuition.

### 5.1 Définir PD par les critères canoniques de créativité

La créativité = **nouveauté × utilité/appropriateness sous contraintes** (Runco &
Jaeger 2012 ; Diedrich et al. 2015 ; Acar et al. 2019, tous dans ta biblio). CreativityPrism
(Hou et al., arXiv:2510.20091) opérationnalise en trois dimensions : *quality, novelty,
diversity*. Transposé au code *(B)* :

| Dimension créativité | Version TR-Code | Signal |
| --- | --- | --- |
| Quality / usefulness | correct + robuste + efficace + sûr | axes 1/2/3/5 |
| Novelty | paradigme distinct, faible recouvrement, distance structurelle | distance multi-signaux |
| Diversity | nombre de paradigmes valides distincts atteints sous déni | trajectoire de déni |
| Appropriateness | respect de signature, imports, complexité, régime TR | gates |

Formule conceptuelle proposée *(C)* :

```
PD_code = validity_gate × usefulness_gate × novelty_score × (1 + diversity_bonus)
  validity_gate   = correctness × robustness × contract_safety        (∈ {0,1}-ish)
  usefulness_gate = efficiency                                          (régime de complexité)
  novelty_score   = f(paradigm_distance, oracle_overlap, structural_distance)
  diversity_bonus = g(unique_valid_paradigms le long de la trajectoire de déni)
```

La PD n'est **jamais** récompensée si le code échoue (la divergence invalide tombe à 0
via `validity_gate`). C'est la différence avec les benchmarks de créativité qui
récompensent la nouveauté sans grounding.

### 5.2 Signaux de nouveauté à tester (sortir du cosinus binaire)

| Signal | Pourquoi | Coût | État |
| --- | --- | --- | --- |
| Features AST | léger, déjà là | faible | ✅ |
| Distance CFG (graphe de flot de contrôle) | distingue mieux les structures de contrôle que l'AST plat | moyen | ⏳ |
| PDG (program dependence graph) | sépare deux paradigmes visuellement proches | élevé | ⏳ |
| Courbe de scaling runtime | vérifie la complexité observée (lie efficiency et novelty) | moyen | partiel |
| Sondes comportementales | observe la réponse sur familles d'inputs ciblées | moyen | ✅ `behavioral_probes.py` |
| Détection de clone (type-2/3) | détecte copie/paraphrase au-delà du Jaccard | moyen | ⏳ |
| Label humain de paradigme | étalon partiel (gold set) | élevé | ❌ |
| LLM-judge contraint | *fallback* uniquement, jamais seul | faible | ⏳ (prévu) |

L'idée n'est pas d'empiler les modules — tu en as déjà assez — mais de **fusionner**
ces signaux dans `paradigm_evidence` et de **valider** que le score automatique corrèle
avec le label humain.

### 5.3 Calibration des seuils (P0 analytique)

Les seuils `SALIERI = 0.70` et `PARADIGM_COSMETIC = 0.20` sont arbitraires, et le run
montre que 0,20 tombe au centre de la distribution (mean 0,189). Procédure *(C)* :

1. Construire trois populations par item : (a) copies/paraphrases de l'oracle, (b)
   solutions indépendantes **même** paradigme, (c) solutions indépendantes **autre**
   paradigme.
2. Tracer les distributions de `paradigm_distance` et `oracle_overlap` sur ces trois
   populations.
3. Choisir les seuils par courbe ROC/PR (maximiser la séparation b ↔ c), et **rapporter
   l'AUC** dans le papier. Un seuil justifié empiriquement vaut dix seuils intuitifs.

### 5.4 Valider le classifier — gold set humain (P0)

`tests/unit/test_paradigm_classifier.py` teste surtout des variantes *positives* : c'est
un **rappel sur exemples synthétiques**, pas une précision. Il faut :

- un gold set de **200–400 solutions** (modèles + humaines + synthétiques), annotées par
  **2 annotateurs** : paradigme principal/secondaire, complexité, statut PD ;
- accord inter-annotateur (Cohen κ ou Krippendorff α, cible ≥ 0,75) ;
- précision / rappel / F1 **par paradigme** + matrice de confusion ;
- des *hard negatives* : même style de code / paradigme différent, et inversement ;
- ne conserver dans la métrique principale que les paradigmes détectés de façon fiable
  (F1 ≥ 0,80), les autres passant par `judge`/`abstain`.

---

## 6. Réponse directe : « ajouter des problèmes à plusieurs bonnes réponses et plus de potentiel créatif ? »

**Réponse courte : oui sur le principe, mais ton dataset le fait déjà — la priorité
n'est pas d'en ajouter, c'est de rendre exploitable celui que tu as.**

Constat : **les 40 items déclarent déjà ≥ 3 paradigmes valides** (moyenne 3,02, un item
à 4) et **tous** ont des `denial_constraints` avec `expected_alternatives`. Le benchmark
est donc *déjà construit* sur des problèmes à solutions multiples. Le run montre pourtant
0,6 % de divergence genuine. **Le goulot n'est pas le nombre de bonnes réponses possibles,
c'est : (a) la détection des paradigmes effectivement produits, et (b) le fait que les
modèles convergent presque tous vers la solution canonique.** Ajouter des items à
solutions multiples *avant* de corriger (a) et (b) ne ferait qu'augmenter le bruit.

Cela dit, trois extensions augmenteraient réellement le **potentiel créatif mesurable** :

1. **Élargir l'écart entre paradigmes valides d'un même item** *(C)*. Aujourd'hui
   `kmp / z_algorithm / rolling_hash` partagent beaucoup de structure (d'où la confusion
   AST). Privilégier des items dont les paradigmes valides sont *structurellement
   éloignés* (ex. : DP itérative vs mémoïsation récursive vs branch-and-bound ; ou
   tri vs structure de données vs sweep-line) maximise la `paradigm_distance` réelle et
   donne au signal une chance d'exister.

2. **Une classe d'items « espace de solutions ouvert » avec ancrage oracle faible** *(C)*.
   Items où l'oracle n'est qu'*un* représentant parmi une famille large, et où la
   métrique de nouveauté se calcule **vs la distribution des solutions des modèles**
   (diversity@k, à la NeoGauge/CreativityPrism) plutôt que vs l'oracle. Cela répond
   directement à la limite §11.5 (« divergence de l'oracle, pas de l'espace »).

3. **Quelques tâches d'optimisation / refactoring** *(C)*. Inspiré de BigCodeBench
   (appels multi-bibliothèques, instructions complexes) et SWE-bench (repo-level) : des
   tâches où plusieurs *designs* sont acceptables, encore vérifiables par tests, mais
   moins « une seule courbe de complexité optimale ». C'est là que la PD a le plus de
   place pour s'exprimer sans dégénérer en bruit.

Métriques à ajouter pour exploiter le multi-solutions *(C)* : `unique_valid_paradigms@k`
(diversité intra-modèle sur k échantillons), `solution_space_coverage` (part des
paradigmes valides déclarés effectivement atteints), `denial_pass_rate` (déjà
implémenté). **Ne pas** simplement multiplier les items : multiplier la **diversité
atteignable et détectable**.

---

## 7. Booster la Productive Divergence — protocole de boosters

Objectif : identifier ce qui augmente la PD **sans augmenter les violations de régime**.
Étude contrôlée `booster × modèle × item × run`. La variable créative doit devenir un
champ explicite du run (pont direct avec le position paper, où CI est une IV) *(B)* :

```json
"creativity_condition": {
  "ci_level": "none | mild | strong",
  "constraint_type": "none | forbidden_api | forbidden_paradigm | forbidden_structure",
  "target": "algorithmic_divergence"
}
```

| Booster | Hypothèse | Risque | Appui SOTA |
| --- | --- | --- | --- |
| Denial prompting | ↑ changements de paradigme | ↑ échecs de contrainte | NeoGauge/NeoCoder (Lu et al. 2407.09007) — **déjà implémenté ici** |
| Multi-sample + clustering | trouve plus d'alternatives valides | coût API | diversity@k (CreativityPrism) |
| Algorithm-first prompting | planifier le paradigme avant de coder | explications fausses (mismatch code/claim) | diverge-then-converge (Sun et al. 2024) |
| « Avoid canonical solution » | ↓ copie de l'oracle | dérive vers solutions inefficaces | — |
| Paradigm menu | propose des paradigmes sans code | guide trop fortement | — |
| Self-verification | ↓ H après divergence | reconverge vers canonique | Banerjee et al. 2025 (vérif. préserve la divergence) |
| Test-guided repair | ↑ validité après génération créative | lisse la diversité | — |
| Pairwise contrastive (2 solutions différentes) | bon signal de flexibilité intra-modèle | coût | — |
| Temperature sweep | ↑ variété | faible levier en texte | position paper (T non significatif sur H) ; **à retester sur code** |

Point d'attention SOTA : NeoCoder montre que des méthodes de raisonnement avancées
(MCTS, self-correction) **n'augmentent pas forcément** la créativité. Ton étude doit
donc mesurer non pas « plus de créativité » mais « **PD préservée sous vérification** »
— c'est ton avantage, parce que ton régime est exécutable.

Un pont conceptuel fort *(B)* : évaluer aussi la **cohérence explication ↔ code**. Un
modèle qui *prétend* utiliser un paradigme que son code n'implémente pas commet une
*explanation-code mismatch* — c'est l'analogue exact du claim-level checking du position
paper, transposé au code. C'est une contribution originale facile à ajouter.

---

## 8. Plan expérimental principal (pour rendre le papier solide)

Démontrer que **TR-CodeBench mesure une capacité distincte de la correctness**.

- **Unités** : `(modèle, item, run_index, condition)`.
- **Facteurs** : régime TR (strict / T2 / déni) × intention créative (none/mild/strong)
  × prompt (standard / avoid-oracle / paradigm-menu / denial).
- **Modèles** : 6–10, dont 2 frontier, 2 open-weight forts, 1 petit, 1 baseline faible —
  **et qui répondent** (résoudre le problème des 37 % d'erreurs API : retries, modèles
  payants, quotas).
- **Runs** : 3–5 par condition, température fixée, top_p fixé, seed si dispo.
- **Variables dépendantes** : correctness, robustness, efficiency, divergence, safety,
  `unique_valid_paradigms`, `denial_pass_rate`, `invalid_divergence_rate`, oracle_overlap.

Analyses minimales et seuils visés :

| Analyse | Cible | Statut actuel |
| --- | --- | --- |
| Difficulté d'item (p) | éviter p < .10 et p > .90 | à calculer |
| Discrimination item-total | positive, significative pour la majorité | à calculer (l'écart-type ne suffit pas) |
| Fiabilité test-retest (ICC) | ICC ≥ .75 acceptable, ≥ .85 bon | **impossible (1 run)** |
| F1 du classifier vs gold set | ≥ .80 | non mesuré |
| Calibration seuils (ROC/PR) | AUC rapportée | non fait |
| Ablation pipeline | chaque module ajoute du signal | non fait |
| GLMM (effets aléatoires modèle + item) | variance prompt vs modèle | non fait |
| Corrélation PD_auto ↔ label humain | significative | non fait |

**Ablation à produire** (argument à la EvalPlus : montrer que la couche change le
diagnostic) :

| Configuration | Question |
| --- | --- |
| tests publics seuls | surestime-t-on la correction ? |
| + hidden | combien d'erreurs capturées ? |
| + PBT | combien de quasi-correctes tombent ? |
| + complexity stress | combien de naïves rejetées ? |
| + paradigm classifier | combien de PD détectées ? |
| + evidence stack | combien de faux négatifs récupérés ? |
| + denial trajectories | combien de modèles changent vraiment de stratégie ? |

L'argument statistique cible : *« TR-CodeBench change le classement des modèles après
contrôle de la correctness »*. Sans cela, un reviewer dira que c'est un benchmark de
pass-rate déguisé.

---

## 9. Positionnement vs état de l'art

Grille actualisée (corrigée du run réel) :

| Benchmark | Correct. | Tests cachés | Complexité | Diversité paradigmes | Anti-contam. | Créativité explicite |
| --- | --- | --- | --- | --- | --- | --- |
| HumanEval (Chen 2021) | ✓ | — | — | — | — | — |
| EvalPlus (Liu, NeurIPS 2023) | ✓ | ✓ (×80) | — | — | — | — |
| LiveCodeBench (Jain 2024) | ✓ | ✓ | — | — | ✓ post-cutoff | — |
| SWE-bench (Jimenez 2024) | ✓ | ✓ | — | — | partielle | — |
| BigCodeBench (Zhuo 2024) | ✓ | ✓ | — | — | — | — |
| NeoGauge/NeoCoder (Lu 2407.09007) | ✓ | — | — | ✓ (distrib./denial) | ✓ post-cutoff | ✓ (convergent/divergent) |
| CreativityPrism (Hou 2510.20091) | partiel | — | — | ✓ (quality/novelty/diversity) | — | ✓ (holistique) |
| RACE *(à vérifier)* | ✓ | — | ✓ (efficiency) | — | — | readability/maintainability |
| Mercury *(à vérifier)* | ✓ | ✓ | ✓ (efficiency, percentile runtime) | — | — | — |
| **TR-CodeBench** | ✓ | ✓ | ✓ (heuristique, inerte en live) | ✓ (heuristique, ~0,6 % genuine) | partielle (anti-copie oracle) | **PD sous oracle exécutable** |

Positionnement à écrire *(B)* :

> *Existing code benchmarks evaluate functional correctness (HumanEval, EvalPlus),
> contamination-free recency (LiveCodeBench), repository-level resolution (SWE-bench),
> library use (BigCodeBench), code quality (RACE), or efficiency (Mercury).
> Creativity-oriented work (NeoGauge, CreativityPrism) rewards novelty/diversity but
> rarely conditions on an executable truth regime. TR-CodeBench targets a narrower,
> undermeasured capability: **algorithmic flexibility under executable verification** —
> can a model produce a correct, efficient, safe solution that diverges structurally
> from a sealed oracle?*

Distinction explicite à maintenir : NeoGauge mesure la divergence **distributionnelle**
(vs corpus/solutions humaines, post-cutoff) ; TR-CodeBench mesure la divergence
**structurelle vs un oracle exécutable** sous contraintes asymptotiques et taxonomie de
paradigmes par item. Ne **pas** revendiquer « premier benchmark de créativité du code ».
Revendiquer : *« among the first to operationalize algorithmic divergence against
executable oracles with an explicit truth-regime contract »* — et même cela demande une
revue biblio complète.

Sur l'anti-contamination : renommer Salieri en *oracle-copy detection*. Salieri détecte
la copie de l'oracle local, **pas** la mémorisation depuis l'entraînement. LiveCodeBench
a l'argument fort (post-cutoff) ; toi pas encore.

---

## 10. Feuille de route priorisée

> État réel au 2026-05-24 : `pyproject.toml` restauré ✅ ; baselines naïves (4 items) ✅ ;
> `paradigm_evidence/` + `denial/` ✅ ; `oracle_ast_features` gelées ✅ ; run live 40 items ✅.
> Le front s'est déplacé de l'ingénierie vers la **validité de mesure**.

### P0 — Bloquants avant toute soumission

1. **Rendre la PD discriminante.** Refondre `paradigm_distance` (ajouter CFG + clone
   detection + fusion evidence), **calibrer les seuils par ROC/PR** (§5.3), corriger les
   faux négatifs du classifier. Cible : `genuine_divergence` passe de 0,6 % à un taux
   qui sépare les modèles.
2. **Gold set humain de paradigmes** (§5.4) : 200–400 solutions, 2 annotateurs, κ, F1
   par paradigme.
3. **Protocole de run défendable** : éliminer les 37 % d'erreurs API (retries/modèles
   payants), **≥ 3 runs/condition**, rapporter ICC + corrélations inter-run.
4. **Matrice de validation par item** : pour chaque item, oracle / naïf / alternative
   valide / quasi-copie / dangereux / quasi-correct. Aujourd'hui 4 baselines naïves / 40.
   Cible : 1 naïve + 1 alternative valide + 1 paraphrase par item.
5. **Séparer `safety` de `correctness`** et neutraliser les défauts optimistes de
   `robustness` (§4).

### P1 — Pour un papier solide

6. Ajouter le **verdict TR global** + le champ `creativity_condition` (§1.3, §7).
7. **Ablation complète** du pipeline (§8).
8. **Étude des boosters** de PD (§7) : denial / avoid-canonical / algorithm-first /
   multi-sample / self-verify / repair, mesurées sur PD **et** sur H.
9. Migrer l'analyse (`trcb_analysis.ipynb`) du composite déprécié vers le profil 5 axes
   + verdict ; rapporter intervalles de confiance bootstrap.
10. **Normaliser la taxonomie des paradigmes** : noms canoniques, alias, granularité
    (un paradigme ≠ une famille ≠ une variante d'implémentation) ; corriger les
    incohérences de familles (`string`/`strings`, `graph`/`graph_dp`) et la dérive de
    schéma (`oracle_paradigm_features` vs `oracle_ast_features`).

### P2 — Pour viser une bonne conférence

11. **20–30 % d'items post-cutoff / procéduraux** (générateurs à seed documenté) pour un
    vrai argument anti-contamination (cf. LiveCodeBench).
12. **Classe d'items « espace de solutions ouvert »** + tâches d'optimisation/refactoring
    (§6) ; métriques `diversity@k`, `solution_space_coverage`.
13. **Cohérence explication ↔ code** (explanation-code mismatch) comme pont avec le
    position paper claim-level (§7).
14. Comparaison empirique explicite vs EvalPlus / LiveCodeBench / NeoGauge sur un
    sous-ensemble partagé, si faisable.

---

## 11. Risques reviewers & parades

| Risque reviewer | Parade |
| --- | --- |
| « C'est un benchmark de pass-rate avec une couche cosmétique. » | Ablation + montrer que la PD change le classement après contrôle de la correctness (§8). |
| « La métrique de divergence est ad hoc / non validée. » | Gold set humain + F1 + calibration ROC/PR + corrélation auto↔humain (§5). |
| « Vous confondez créativité et diversité de surface. » | Définir PD = nouveauté × utilité × conformité ; `validity_gate` tue la divergence invalide (§5.1). |
| « Anti-contamination surévaluée. » | Renommer en oracle-copy ; ajouter items post-cutoff (P2). |
| « Seuils arbitraires. » | Distributions + ROC/PR rapportées (§5.3). |
| « Pas de fiabilité statistique. » | ≥ 3 runs, ICC, GLMM, bootstrap (§8). |
| « NeoCoder fait déjà la créativité du code. » | Distinction structurelle vs distributionnelle + oracle exécutable + contrainte asymptotique (§9). |

---

## 12. Checklist avant soumission

- [ ] PD discriminante (genuine_divergence > bruit) et seuils calibrés (ROC/PR, AUC rapportée)
- [ ] Gold set humain de paradigmes + F1 par paradigme + matrice de confusion
- [ ] Run propre : ≥ 3 seeds, < 5 % d'erreurs API, ≥ 6 modèles répondants
- [ ] Fiabilité inter-run (ICC) + GLMM (variance modèle vs item)
- [ ] Matrice de validation par item (oracle / naïf / alternative / paraphrase / dangereux / quasi-correct)
- [ ] `safety` indépendant de `correctness` ; `robustness` sans défauts optimistes
- [ ] Verdict TR global + `creativity_condition` exposés dans les sorties
- [ ] Ablation complète du pipeline
- [ ] Analyse migrée sur le profil 5 axes (plus de composite)
- [ ] Discriminant de complexité confronté à des naïves en live (tailles de stress revues)
- [ ] Claims « first / anti-contamination / creativity » affaiblis ou justifiés
- [ ] Comparaison explicite HumanEval / EvalPlus / LiveCodeBench / BigCodeBench / NeoGauge / CreativityPrism (+ RACE/Mercury à vérifier)

---

## 13. Références

**Vérifiées (présentes dans la bibliographie du position paper).**

- Lu, Wang, Li, Jiang, Khudanpur, Jiang, Khashabi. *Benchmarking Language Model
  Creativity: A Case Study on Code Generation* (NeoGauge/NeoCoder), arXiv:2407.09007, 2025.
- Hou et al. *CreativityPrism: A Holistic Benchmark for LLM Creativity*, arXiv:2510.20091, 2025.
- Bang et al. *HalluLens: LLM Hallucination Benchmark*, arXiv:2504.17550, 2025.
- Sun et al. *Hallucinating LLM Could Be Creative*, OpenReview W48CPXEpXR, 2024.
- Banerjee et al. *Does Less Hallucination Mean Less Creativity? An Empirical
  Investigation in LLMs*, arXiv:2512.11509, 2025.
- He, Zhang, Cheng. *Shakespearean Sparks: The Dance of Hallucination and Creativity in
  LLMs' Decoding Layers*, arXiv:2503.02851, 2025.
- Ye, Gu, Zhao, Yin, Wang. *Assessing the Creativity of LLMs in Proposing Novel
  Solutions to Mathematical Problems* (CreativeMath), arXiv:2410.18336, 2024.
- DeLorenzo, Gohil, Rajendran. *CreativEval: Evaluating Creativity of LLM-Based Hardware
  Code Generation*, arXiv:2404.08806, 2024.
- Runco & Jaeger 2012 ; Diedrich et al. 2015 ; Acar et al. 2019 (définition standard de
  la créativité : nouveauté + utilité sous contraintes).
- HumanEval (Chen 2021) ; EvalPlus (Liu, NeurIPS 2023) ; LiveCodeBench (Jain 2024) ;
  SWE-bench (Jimenez, ICLR 2024) ; BigCodeBench (Zhuo 2024) — cf. SPEC §B.

**À vérifier avant citation (non présentes dans la biblio fournie).**

- *RACE* — benchmark de qualité de code (readability, maintainability, correctness,
  efficiency). Référence et auteurs à confirmer.
- *Mercury* — benchmark d'efficacité de code (percentile de runtime). Référence et
  auteurs à confirmer.

---

### Priorité finale

N'ajoute pas de nouveaux modules : tu en as assez. La priorité est de **prouver que les
modules existants mesurent vraiment ce qu'ils prétendent mesurer** — PD discriminante,
seuils calibrés, classifier validé contre l'humain, run reproductible, ablations, et
comparaison propre à NeoGauge/CreativityPrism. La question de recherche, formulée
simplement :

> *Can LLMs turn the same divergence mechanism that causes hallucination into productive
> algorithmic creativity when the truth regime is executable?*
