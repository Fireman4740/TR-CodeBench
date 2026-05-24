# TR-CodeBench T2 Prompt Template

## ORACLE

Python 3.11 will execute your returned code against public tests, hidden tests, property-based tests, and a sealed reference oracle. Hidden tests are not shown.

## STYLE LATITUDE

Multiple correct algorithmic paradigms are allowed. You may choose any strategy that respects the function signature and constraints.

## INVENTION LICENSE

Do not invent APIs, packages, files, network calls, or runtime assumptions. Use only the allowed imports listed in the task.

## TASK

{{statement}}

Signature:

```python
{{signature}}
```

Allowed imports: `{{allowed_imports}}`

Forbidden imports: `{{forbidden_imports}}`

Optimization constraints: `{{optimization_constraints}}`

## OUTPUT RULES

Return only Python code defining the requested function. After the code, include comments named `COMPLEXITY` and `PARADIGM`.
