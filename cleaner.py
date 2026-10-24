import re
import pandas as pd

SEASON_RE = re.compile(r"^(\d{2}|\d{4})\s*[/\-–]\s*(\d{2}|\d{4})$")


def full_year(s: str, pivot: int = 70) -> str:
    """Turn a 2-digit year into 4 digits. Values >= pivot -> 19xx, below -> 20xx."""
    if len(s) == 4:
        return s
    return ("19" if int(s) >= pivot else "20") + s


def clean_season(value, pivot: int = 70):
    """26/27, 2026/2027, 2026-27 -> 2026/27. Unrecognised values are returned unchanged."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return value
    m = SEASON_RE.match(str(value).strip())
    if not m:
        return value
    return f"{full_year(m.group(1), pivot)}/{m.group(2)[-2:]}"


def detect_dayfirst(series: pd.Series) -> bool:
    """Look for a value that proves day/month or month/day order; default day first."""
    for v in series.astype(str):
        m = re.match(r"^\s*(\d{1,2})[/.\-](\d{1,2})[/.\-]\d{2,4}", v)
        if m:
            if int(m.group(1)) > 12:
                return True
            if int(m.group(2)) > 12:
                return False
    return True


def sort_by_date(df: pd.DataFrame, date_col: str, ascending: bool, dayfirst: bool) -> pd.DataFrame:
    parsed = pd.to_datetime(df[date_col], dayfirst=dayfirst, errors="coerce", format="mixed")
    out = df.assign(_d=parsed).sort_values("_d", ascending=ascending, kind="stable", na_position="last")
    return out.drop(columns="_d").reset_index(drop=True)
