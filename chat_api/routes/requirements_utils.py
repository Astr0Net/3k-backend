import json


def normalize_requirements(req, raw_text: str, max_items: int = 6):
    """
    requirements در DB: JSON
    ممکن است list/dict/str/None باشد.
    """
    if isinstance(req, str) and req.strip():
        try:
            req = json.loads(req)
        except Exception:
            req = None

    if isinstance(req, list):
        return [str(x).strip() for x in req if str(x).strip()][:max_items]

    if isinstance(req, dict):
        candidate = req.get("skills") or req.get("items") or req.get("requirements") or []
        if isinstance(candidate, list):
            return [str(x).strip() for x in candidate if str(x).strip()][:max_items]

    # fallback از raw_text
    items = []
    for l in (raw_text or "").splitlines():
        l = (l or "").strip()
        if l.startswith(("•", "-", "*", "–")):
            items.append(l.lstrip("•-*– ").strip())
        if len(items) >= max_items:
            break
    return items