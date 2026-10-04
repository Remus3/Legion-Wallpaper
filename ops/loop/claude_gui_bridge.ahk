#Requires AutoHotkey v2.0
#SingleInstance Force
SetTitleMatchMode 2
; gemini-headless-upgrade GUI bridge (the HANDS). The ONLY GUI actor.
; LW port of the RC bridge under the RC 81636382 collision contract:
; live targeting is PID-ONLY (no title fallback) - RC's launcher self-defers
; while any Legion Wallpaper bridge is alive, and each repo's launcher kills
; only its own cmdline-scoped bridge instances.
; Polls control\gemini.ready; slash lines typed, plain lines PASTED as one block
; (ingest P1-6) into the TARGET window after a process check; ack =
; deleting gemini.ready. Target is FILE-DRIVEN (config not code):
;   control\ahk_mode.txt    = "dry" (type into Notepad LW-LOOP-DRYRUN) or "live"
;   control\target_hwnd.txt = HWND of the Claude window titled "Image". ONE
;                             claude.exe process owns MULTIPLE project windows
;                             (Image/RC/...), so pid alone is AMBIGUOUS - the
;                             hwnd pins the exact window. target_pid.txt is
;                             informational only (launcher writes both).
; Live mode with a missing/empty target_hwnd.txt ABORTS the bridge outright.
; Exits when control\STOP appears.

CTL := "C:\Legion Wallpaper\ops\loop\control"
READY := CTL "\gemini.ready"
TYPED := CTL "\typed.flag"
STOPF := CTL "\STOP"
MODEF := CTL "\ahk_mode.txt"
HWNDF := CTL "\target_hwnd.txt"
DRY_TITLE := "LW-LOOP-DRYRUN"
LINE_PAUSE := 1500
; Extra settle AFTER a /clear commits: the session reset repaints the TUI, and a
; follow-up slash-send at bare LINE_PAUSE raced it - /gemini-headless-upgrade could
; land mid-clear and get eaten (operator 2026-07-16).
CLEAR_PAUSE := 4000

LogMsg(s) {
    global CTL
    FileAppend(FormatTime(, "yyyy-MM-dd HH:mm:ss") " " s "`n", CTL "\ahk_bridge.log")
}

Target() {
    global MODEF, HWNDF, DRY_TITLE
    mode := FileExist(MODEF) ? Trim(FileRead(MODEF)) : "live"
    if (mode = "dry")
        return DRY_TITLE
    hwnd := FileExist(HWNDF) ? Trim(FileRead(HWNDF)) : ""
    if (hwnd = "") {
        LogMsg("ABORT: live mode with no target_hwnd.txt (hwnd-only policy, no title/pid fallback)")
        ExitApp
    }
    return "ahk_id " hwnd
}

; TARGET CHECK (ingest P1-6): text sent into a plain shell EXECUTES, so the
; window must belong to the expected process before anything is sent: claude.exe
; in live mode, notepad.exe for the dry-run window. Unsure = REFUSE: gemini.ready
; is left in place, so the controller reads "not consumed" and journals a failed
; result instead of a send that never reached a Claude session.
ExpectedProcess() {
    global MODEF
    mode := FileExist(MODEF) ? Trim(FileRead(MODEF)) : "live"
    return (mode = "dry") ? "notepad.exe" : "claude.exe"
}

TargetOk(win) {
    try proc := WinGetProcessName(win)
    catch
        proc := ""
    want := ExpectedProcess()
    if (StrLower(proc) != want) {
        LogMsg("REFUSE: target [" win "] is process [" proc "], expected [" want "] - nothing sent")
        return false
    }
    return true
}

; SINGLE PASTE (ingest P1-6): a multi-line directive typed line by line submits
; each line as its own fragment and the session answers only the last one. Plain
; lines are therefore delivered as ONE clipboard paste; the operator's clipboard
; is saved first and restored after. Enter is sent SEPARATELY after a pause so it
; never lands inside the paste.
PasteBlock(text) {
    saved := ClipboardAll()
    A_Clipboard := ""
    A_Clipboard := text
    if !ClipWait(2) {
        A_Clipboard := saved
        LogMsg("paste FAILED: clipboard did not take the text")
        return false
    }
    Send("^v")
    Sleep 600
    A_Clipboard := saved
    saved := ""
    return true
}

SubmitEnter() {
    Sleep 350
    Send("{Enter}")
    ; SECOND Enter (operator-observed 2026-07-26: text landed in the composer
    ; but was never submitted). Something transient (autocomplete, paste-mode, a
    ; hint row) can eat the first Enter; on an empty composer Enter is a no-op.
    Sleep 250
    Send("{Enter}")
}

LogMsg("ahk bridge start (LW)")
Loop {
    if FileExist(STOPF) {
        LogMsg("STOP seen, exit")
        ExitApp
    }
    if FileExist(READY) {
        content := FileRead(READY)
        lines := StrSplit(content, "`n", "`r")
        win := Target()
        if !WinExist(win) {
            LogMsg("target window not found: " win)
            Sleep 1500
            continue
        }
        if !TargetOk(win) {
            Sleep 5000
            continue
        }
        WinActivate(win)
        WinWaitActive(win, , 5)
        Sleep 500
        if !TargetOk("A") {
            Sleep 5000
            continue
        }
        sent := 0
        block := ""
        for idx, lineText in lines {
            if (idx = 1)                 ; skip CYCLE=n header
                continue
            if (SubStr(lineText, 1, 1) = "/") {
                if (Trim(block) != "") {
                    if PasteBlock(RTrim(block, "`n"))
                        SubmitEnter(), sent += 1
                    Sleep LINE_PAUSE
                }
                block := ""
                ; Slash-command line: commit the leading "/" on its own and pause so
                ; the Claude TUI slash-menu opens BEFORE the command word arrives
                ; (RC 2026-06-06: "clear/" not "/clear"). A trailing space closes
                ; the palette so Enter submits (2026-07-17).
                SendText("/")
                Sleep 400
                SendText(SubStr(lineText, 2))
                SendText(" ")
                SubmitEnter()
                sent += 1
                Sleep LINE_PAUSE
                if (Trim(lineText) = "/clear")
                    Sleep CLEAR_PAUSE
            } else {
                block .= lineText "`n"
            }
        }
        if (Trim(block) != "") {
            if PasteBlock(RTrim(block, "`n"))
                SubmitEnter(), sent += 1
        }
        FileDelete(READY)              ; READY consumed = the "typed" signal the controller waits on
        LogMsg("sent " sent " message(s) into [" win "]")
    }
    Sleep 1000
}
