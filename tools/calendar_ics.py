"""Kalender-Abos (iCalendar) für Checkball: data/turniere.ics, data/opengyms.ics, data/alles.ics.

Wird von export_data.py nach jedem Export aufgerufen. Nur öffentliche Einträge (dieselbe Liste wie items.json).
"""
import datetime
import re

SITE_URL = "https://checkballberlin.github.io"
TZ = "Europe/Berlin"
WD = ["SU", "MO", "TU", "WE", "TH", "FR", "SA"]  # 0 = Sonntag wie im Datenmodell
VTIMEZONE = [
    "BEGIN:VTIMEZONE", "TZID:Europe/Berlin",
    "BEGIN:DAYLIGHT", "TZOFFSETFROM:+0100", "TZOFFSETTO:+0200", "TZNAME:CEST",
    "DTSTART:19700329T020000", "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU", "END:DAYLIGHT",
    "BEGIN:STANDARD", "TZOFFSETFROM:+0200", "TZOFFSETTO:+0100", "TZNAME:CET",
    "DTSTART:19701025T030000", "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU", "END:STANDARD",
    "END:VTIMEZONE",
]


def esc(s):
    return str(s or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r", "").replace("\n", "\\n")


def fold(line):
    b = line.encode("utf-8")
    if len(b) <= 75:
        return line
    out, cur = [], b""
    for ch in line:
        e = ch.encode("utf-8")
        if len(cur) + len(e) > (75 if not out else 74):
            out.append(cur.decode("utf-8"))
            cur = b""
        cur += e
    out.append(cur.decode("utf-8"))
    return "\r\n ".join(out)


def parse(s):
    if not isinstance(s, str):
        return None, False
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}))?", s)
    if not m:
        return None, False
    y, mo, d = int(m[1]), int(m[2]), int(m[3])
    if m[4]:
        return datetime.datetime(y, mo, d, int(m[4]), int(m[5])), True
    return datetime.date(y, mo, d), False


def hm(s):
    m = re.match(r"^(\d{1,2}):(\d{2})$", s or "")
    return (int(m[1]), int(m[2])) if m else None


def fmt_dt(dt):
    return dt.strftime("%Y%m%dT%H%M%S")


def describe(item):
    parts = []
    if item.get("summary"):
        parts.append(item["summary"])
    for k, label in (("audience", "Für"), ("price", "Kosten"), ("organizer", "Veranstalter")):
        if item.get(k):
            parts.append(f"{label}: {item[k]}")
    if item.get("regUrl"):
        parts.append(f"Anmeldung: {item['regUrl']}")
    if item.get("sourceUrl"):
        parts.append(f"Quelle: {item['sourceUrl']}")
    parts.append(f"Alle Termine: {SITE_URL} · Angaben ohne Gewähr")
    return "\n".join(parts)


def vevent(item, stamp, today):
    rec = item.get("recurring") if isinstance(item.get("recurring"), dict) else None
    if rec and (rec.get("freq") == "irregular" or not hm(rec.get("from"))) and parse(item.get("start"))[0] is not None:
        rec = None  # einmaliges Open Gym mit Datum
    lines = ["BEGIN:VEVENT", f"UID:{item['id']}@checkballberlin.github.io", f"DTSTAMP:{stamp}"]
    if rec:
        days = rec.get("weekdays") if isinstance(rec.get("weekdays"), list) else ([rec["weekday"]] if isinstance(rec.get("weekday"), int) else [])
        days = [d for d in days if isinstance(d, int) and 0 <= d <= 6]
        t0, t1 = hm(rec.get("from")), hm(rec.get("to"))
        if not days or rec.get("freq") == "irregular" or not t0:
            return None
        first = today
        while (first.isoweekday() % 7) not in days:
            first += datetime.timedelta(days=1)
        start = datetime.datetime.combine(first, datetime.time(*t0))
        end = datetime.datetime.combine(first, datetime.time(*t1)) if t1 else start + datetime.timedelta(hours=2)
        if rec.get("freq") == "monthly-first":
            rule = f"RRULE:FREQ=MONTHLY;BYDAY=1{WD[days[0]]}"
        else:
            rule = "RRULE:FREQ=WEEKLY;BYDAY=" + ",".join(WD[d] for d in days)
        until, _ = parse(rec.get("until") or "")
        if isinstance(until, datetime.date):
            rule += ";UNTIL=" + until.strftime("%Y%m%d") + "T235959Z"
        lines += [f"DTSTART;TZID={TZ}:{fmt_dt(start)}", f"DTEND;TZID={TZ}:{fmt_dt(end)}", rule]
    else:
        s, s_time = parse(item.get("start"))
        if s is None:
            return None
        e, e_time = parse(item.get("end"))
        if s_time:
            if not (e and e_time) or e <= s:
                e = s + datetime.timedelta(hours=3)
            lines += [f"DTSTART;TZID={TZ}:{fmt_dt(s)}", f"DTEND;TZID={TZ}:{fmt_dt(e)}"]
        else:
            sd = s if isinstance(s, datetime.date) and not isinstance(s, datetime.datetime) else s.date()
            ed = e.date() if isinstance(e, datetime.datetime) else (e or sd)
            if ed < sd:
                ed = sd
            lines += [f"DTSTART;VALUE=DATE:{sd.strftime('%Y%m%d')}", f"DTEND;VALUE=DATE:{(ed + datetime.timedelta(days=1)).strftime('%Y%m%d')}"]
    prefix = {"turnier": "🏆 ", "gym": "🏀 ", "event": "📅 "}.get(item.get("type"), "")
    lines.append("SUMMARY:" + esc(prefix + item.get("title", "")))
    loc = ", ".join(x for x in (item.get("venue"), item.get("address")) if x)
    if loc:
        lines.append("LOCATION:" + esc(loc))
    lines.append("DESCRIPTION:" + esc(describe(item)))
    url = item.get("regUrl") or item.get("sourceUrl")
    if url:
        lines.append("URL:" + url)
    if item.get("status") == "geplant":
        lines.append("STATUS:TENTATIVE")
    if item.get("type") == "turnier":
        lines += ["BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:" + esc("Morgen: " + item.get("title", "")), "TRIGGER:-P1D", "END:VALARM"]
    lines.append("END:VEVENT")
    return lines


def build(items, name, types, out_path):
    now = datetime.datetime.now(datetime.timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    today = datetime.date.today()
    cutoff = today - datetime.timedelta(days=60)
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Checkball Berlin//Kalender//DE", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             "X-WR-CALNAME:" + esc(name), "X-WR-TIMEZONE:" + TZ,
             "X-WR-CALDESC:" + esc("3x3-Basketball in Berlin, jeden Tag aktualisiert. " + SITE_URL),
             "REFRESH-INTERVAL;VALUE=DURATION:PT6H", "X-PUBLISHED-TTL:PT6H"] + VTIMEZONE
    n = 0
    for it in items:
        if it.get("type") not in types:
            continue
        end, _ = parse(it.get("end") or it.get("start") or "")
        if end is not None and (not it.get("recurring") or (it.get("recurring") or {}).get("freq") == "irregular"):
            ed = end.date() if isinstance(end, datetime.datetime) else end
            if ed < cutoff:
                continue
        ev = vevent(it, stamp, today)
        if ev:
            lines += ev
            n += 1
    lines.append("END:VCALENDAR")
    out_path.write_text("\r\n".join(fold(l) for l in lines) + "\r\n", encoding="utf-8")
    return n


def write_all(items, out_dir):
    a = build(items, "Checkball · 3x3-Turniere Berlin", {"turnier"}, out_dir / "turniere.ics")
    b = build(items, "Checkball · Open Gyms Berlin", {"gym"}, out_dir / "opengyms.ics")
    c = build(items, "Checkball · 3x3 Berlin (alles)", {"turnier", "gym", "event"}, out_dir / "alles.ics")
    return a, b, c
