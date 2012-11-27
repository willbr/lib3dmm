#NoTrayIcon
#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.

click(location,count=1) {
    global pos
    x := pos[location][1]
    y := pos[location][2]

    SetMouseDelay, -1

    CoordMode, Mouse, Screen
    MouseGetPos, oldx, oldy

    WinActivate, ahk_class 3DMOVIE

    CoordMode, Mouse, Relative
    Send, {Click %x% %y% %count%}

    CoordMode, Mouse, Screen
    MouseMove, %oldx%, %oldy%
}


pos := {}
pos["next-frame"] := [250, 450]
pos["next-scene"] := [250, 475]
pos["play"] := [315, 460]
pos["actors"] := [200, 40]
pos["props"] := [200, 40]
pos["sounds"] := [400, 40]
pos["words"] := [600, 40]

arg0 = %0%
arg1 = %1%
arg2 = %2%

if (arg2 > 0) {
    count := arg2
} else {
    count := 1
}

try {
    click(arg1, count)
} catch e {
    msgbox, command "%arg1%" failed
}

