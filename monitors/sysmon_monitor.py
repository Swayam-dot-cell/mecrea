# monitors/sysmon_monitor.py
import time
import logging
from datetime import datetime
try:
    import win32evtlog
    import win32evtlogutil
except ImportError as e:
    raise RuntimeError("pywin32 is required: pip install pywin32") from e

logger = logging.getLogger("blue_team")

CHANNEL = "Microsoft-Windows-Sysmon/Operational"

def _format_ts(evt):
    try:
        return evt.TimeGenerated.Format()
    except Exception:
        return datetime.utcnow().isoformat()

def _get_inserts(evt):
    return list(evt.StringInserts) if getattr(evt, "StringInserts", None) else []

def _lookup_user(sid):
    try:
        res = win32evtlogutil.LookupAccountSid(None, sid)
        if isinstance(res, tuple):
            return res[0]
        return str(res)
    except Exception:
        return None

def _normalize_event(evt):
    eid = evt.EventID & 0xFFFF
    inserts = _get_inserts(evt)
    base = {
        "source": "sysmon",
        "timestamp": _format_ts(evt),
        "event_id": eid,
        "record_number": getattr(evt, "RecordNumber", None),
        "computer": getattr(evt, "ComputerName", None),
        "user": _lookup_user(getattr(evt, "Sid", None)) if getattr(evt, "Sid", None) else None,
        "raw_inserts": inserts
    }

    # Event type mapping
    if eid == 1:  # ProcessCreate
        base.update({
            "event_type": "process_create",
            "process": inserts[0] if len(inserts) > 0 else None,
            "process_id": inserts[1] if len(inserts) > 1 else None,
            "command_line": inserts[2] if len(inserts) > 2 else None,
            "current_directory": inserts[3] if len(inserts) > 3 else None,
            "user_from_insert": inserts[4] if len(inserts) > 4 else None,
            "parent_process": inserts[5] if len(inserts) > 5 else None,
            "hash": inserts[8] if len(inserts) > 8 else None
        })
    elif eid == 2:  # ProcessTerminate
        base.update({
            "event_type": "process_terminate",
            "process_id": inserts[1] if len(inserts) > 1 else None,
            "process": inserts[0] if len(inserts) > 0 else None
        })
    elif eid == 3:  # NetworkConnect
        base.update({
            "event_type": "network_connect",
            "src_ip": inserts[0] if len(inserts) > 0 else None,
            "src_port": inserts[1] if len(inserts) > 1 else None,
            "dst_ip": inserts[2] if len(inserts) > 2 else None,
            "dst_port": inserts[3] if len(inserts) > 3 else None,
            "process": inserts[4] if len(inserts) > 4 else None
        })
    elif eid in (11, 12, 13, 23, 15, 16):  # FileCreate/Delete/StreamHash/ExecutableDetected
        op_map = {11:"create", 12:"delete", 13:"streamhash", 15:"executed", 23:"delete_detected"}
        base.update({
            "event_type": "file_op",
            "file_operation": op_map.get(eid, str(eid)),
            "file_path": inserts[0] if len(inserts) > 0 else None,
            "process": inserts[1] if len(inserts) > 1 else None,
            "user_from_insert": inserts[4] if len(inserts) > 4 else None,
            "hash": inserts[8] if len(inserts) > 8 else None
        })
    else:
        base.update({"event_type": f"sysmon_event_{eid}", "detail": inserts})

    return base

def monitor_sysmon(callback, poll_interval=1.0):
    """Blocking: continuously read Sysmon eventlog and call callback(event_dict)"""
    handle = None
    try:
        handle = win32evtlog.OpenEventLog(None, CHANNEL)
    except Exception as e:
        logger.error(f"Unable to open Sysmon event channel '{CHANNEL}': {e}")
        return

    try:
        total = win32evtlog.GetNumberOfEventLogRecords(handle)
        oldest = win32evtlog.GetOldestEventLogRecord(handle)
        last_record = oldest + total
    except Exception:
        last_record = 0

    logger.info("Sysmon monitor started, listening for new events")
    flags = win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

    while True:
        try:
            events = win32evtlog.ReadEventLog(handle, flags, 0)
            if not events:
                time.sleep(poll_interval)
                continue
            for e in events:
                if getattr(e, "RecordNumber", 0) <= last_record:
                    continue
                last_record = getattr(e, "RecordNumber", last_record)
                try:
                    nd = _normalize_event(e)
                    callback(nd)
                except Exception as ex:
                    logger.exception("Failed to normalize Sysmon event: %s", ex)
        except Exception as ex:
            logger.exception("Sysmon monitor read error: %s", ex)
            time.sleep(2)
