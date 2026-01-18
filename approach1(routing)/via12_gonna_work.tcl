########################################################################
# strapSeed_fill_deleteIfSameNet_GROUP3_PER_CORNER_RESET_autoviaSeedR90.tcl
#
# Uses:
#   - REPORT_FILE: m2_grid_report.txt  (contains Yc=.. BB=(..)-(..))
#   - DEVICE_FILE: 1st_script_op.txt (device list with BBOX_UR_Y column)
#
# Behavior:
#   - Straps processed top-to-bottom (skip first+last).
#   - Device "top-right-corner cluster" = device TOP-Y groups derived from DEVICE_FILE
#     (grouping by URY with ROW_TOL). When strap belongs to NEW cluster => RESET group.
#   - GROUP rule (size 3): no duplicate net names inside current group.
#   - Optional: forbid immediate repeats globally (net != lastAcceptedNet).
#   - SEED SEARCH:
#       * createVia ONLY for searching, oriented R90
#       * on REJECT: delete via + delete&recreate strap (clears net contamination)
#       * on ACCEPT: delete search createVia, then place REAL seed using autoVia -point
#   - If no acceptable net after scan: delete strap.
#   - Fill with autoVia -box using accepted net.
########################################################################

# ----------------------------
# USER SETTINGS
# ----------------------------
set REPORT_FILE "/home/users/svgplayout2601mofikry/gonna_work/m2_grid_report.txt"
set DEVICE_FILE "/home/users/svgplayout2601mofikry/gonna_work/1st_script_op.txt"

# LPP used for the strap rectangles (must match your straps)
set LPP_M2 {M2 drawing}

# Via def for seed SEARCH stage (createVia)
set VIA_DEF_NAME "VIA12"

# --- Seed search window anchors (as you requested) ---
# Search from (xur - X_FROM_RIGHT) walking left until (xll + X_FROM_LEFT)
set X_FROM_LEFT  0.02
set X_FROM_RIGHT 0.02

# Seed scan step in X (moves LEFT by this amount each try)
set STEP_X         0.016
set MAX_SEED_TRIES 500

# --- Fill strategy (autoVia -box) ---
set FILL_BOX_W     0.080
set FILL_BOX_H     0.060
set FILL_STEP_X    0.080
set MAX_FILL_BOXES 800

# --- Grouping rules ---
set GROUP_SIZE 3

# Optional extra strict rule:
# 1 = forbid immediate repeat globally (even across group reset / row reset)
# 0 = only enforce uniqueness inside current group
set FORBID_IMMEDIATE_REPEAT 0

# --- Row clustering (device TOP-Y) ---
set ROW_TOL 0.01

# These are the possible offsets used by your strap generator script.
# Used only to infer which device TOP-Y cluster a strap belongs to.
set END_OFFSET 0.100
set OFFSETS_LIST [list 0.101 0.172 0.249 0.393 0.463 0.533]  ;# adjust if you changed them
set ALL_OFFSETS [concat $END_OFFSET $OFFSETS_LIST]

# ----------------------------
# HELPERS
# ----------------------------
proc _safeDestroy {obj} {
    if {$obj eq ""} { return }
    catch { db::destroy $obj }
    catch { le::delete $obj }
}

proc isNumber {s} {
    return [regexp {^[+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)$} $s]
}

proc quantKey {y tol} {
    return [expr {round($y / $tol) * $tol}]
}

proc _tryGetNetName {obj} {
    if {$obj eq ""} { return "" }
    foreach expr {
        {db::getAttr net.name -of $obj}
        {db::getAttr netName  -of $obj}
        {db::getAttr net      -of $obj}
    } {
        set v ""
        if {![catch {set v [eval $expr]}]} {
            if {$v eq ""} { continue }
            if {[string match "oa:*" $v]} {
                set nm ""
                if {![catch {set nm [db::getAttr name -of $v]}]} {
                    if {$nm ne ""} { return $nm }
                }
            } else {
                return $v
            }
        }
    }
    return ""
}

proc _parseReportStraps {fname} {
    set fp [open $fname r]
    set out {}
    while {[gets $fp line] >= 0} {
        if {[regexp {Yc=([-\d\.]+)\s+BB=\(([-\d\.]+)\s+([-\d\.]+)\)-\(([-\d\.]+)\s+([-\d\.]+)\)} \
                $line -> yc xll yll xur yur]} {
            lappend out [list $yc $xll $yll $xur $yur]
        }
    }
    close $fp
    return $out
}

proc _sortStrapsTopToBottom {strapList} {
    return [lsort -real -decreasing -index 0 $strapList]
}

# Parse DEVICE_FILE and build a set of TOP-Y row keys (quantized URY)
# DEVICE_FILE columns:
# INST_NAME ORIGIN_X ORIGIN_Y BBOX_LL_X BBOX_LL_Y BBOX_UR_X BBOX_UR_Y
proc _buildDeviceRowTopYSet {deviceFile rowTol} {
    array set rowTopY {}
    set fp [open $deviceFile r]
    set lineNo 0
    while {[gets $fp line] >= 0} {
        incr lineNo
        set line [string trim $line]
        if {$line eq ""} { continue }
        if {[string match "INST_NAME*" $line]} { continue }
        if {[string match "#*" $line]} { continue }

        set parts [regexp -all -inline {\S+} $line]
        if {[llength $parts] < 7} { continue }

        set ury [lindex $parts 6]
        if {![isNumber $ury]} { continue }

        set k [quantKey $ury $rowTol]
        if {![info exists rowTopY($k)]} {
            set rowTopY($k) $ury
        } else {
            if {$ury > $rowTopY($k)} { set rowTopY($k) $ury }
        }
    }
    close $fp
    return [array get rowTopY]
}

# Infer which device TOP-Y row key this strap belongs to by trying yc+offsets
proc _inferStrapRowKey {yc rowTol allOffsets deviceRowMap} {
    array set rows $deviceRowMap
    foreach off $allOffsets {
        set topY [expr {$yc + $off}]
        set k [quantKey $topY $rowTol]
        if {[info exists rows($k)]} {
            return $k
        }
    }
    return ""
}

# Find strap rect by bbox match
proc _findStrapRectByBBox {design lpp xll yll xur yur} {
    set tol 0.0005
    set sh [db::getShapes -of $design -lpp $lpp -filter {%type=="Rect"}]
    db::foreach s $sh {
        set bb ""
        if {[catch {set bb [db::getAttr bBox -of $s]}]} { continue }
        set llx [lindex [lindex $bb 0] 0]
        set lly [lindex [lindex $bb 0] 1]
        set urx [lindex [lindex $bb 1] 0]
        set ury [lindex [lindex $bb 1] 1]
        if {abs($llx-$xll) < $tol && abs($lly-$yll) < $tol && abs($urx-$xur) < $tol && abs($ury-$yur) < $tol} {
            return $s
        }
    }
    return ""
}

# Recreate strap rectangle (clears net contamination)
proc _recreateStrap {design lpp xll yll xur yur oldObj} {
    _safeDestroy $oldObj
    set box [list [list $xll $yll] [list $xur $yur]]
    set newObj ""
    if {[catch { set newObj [le::createRectangle $box -design $design -lpp $lpp] } err]} {
        puts "WARN: failed to recreate strap rect BB=($xll $yll)-($xur $yur) err=$err"
        return ""
    }
    return $newObj
}

# createVia seed at point, with orientation (R90 here)
proc _createViaPointOrient {design pt viaDefName orient} {
    set v ""
    if {[catch { set v [le::createVia -design $design -definition $viaDefName -origin $pt -orient $orient] } err]} {
        return ""
    }
    return $v
}

# autoVia seed/fill
proc _autoViaPoint {design pt netFilter} {
    set v ""
    if {$netFilter eq ""} {
        catch {
            set v [le::autoVia -point $pt -design $design \
                -sameNetOnly true -createMetalShape false \
                -allowStackedVia true -fitToOverlappedArea true]
        }
    } else {
        catch {
            set v [le::autoVia -point $pt -design $design \
                -nets $netFilter -sameNetOnly true -createMetalShape false \
                -allowStackedVia true -fitToOverlappedArea true]
        }
    }
    return $v
}

proc _autoViaBox {design box netFilter} {
    set v ""
    catch {
        set v [le::autoVia -box $box -design $design \
            -nets $netFilter \
            -sameNetOnly true \
            -createMetalShape false \
            -allowStackedVia true \
            -fitToOverlappedArea true]
    }
    return $v
}

# ----------------------------
# MAIN
# ----------------------------
proc run_strapSeed_fill_deleteIfSameNet_GROUP3_PER_CORNER_RESET {} {
    set design [ed]
    if {$design eq ""} { error "No edit design ([ed]) found." }

    # Sanity-check via def quickly (R0 just for existence)
    if {[catch {set _t [le::createVia -design $design -definition $::VIA_DEF_NAME -origin {0 0}]} err]} {
        error "VIA_DEF_NAME '$::VIA_DEF_NAME' invalid in your tech: $err"
    } else {
        _safeDestroy $_t
    }

    if {![file exists $::DEVICE_FILE]} {
        error "DEVICE_FILE not found: $::DEVICE_FILE"
    }
    set deviceRowMap [_buildDeviceRowTopYSet $::DEVICE_FILE $::ROW_TOL]
    array set _devRows $deviceRowMap
    puts "INFO: Parsed device rows: [llength [array names _devRows]] unique TOP-Y clusters from DEVICE_FILE."

    set straps [_parseReportStraps $::REPORT_FILE]
    set n [llength $straps]
    if {$n < 3} { error "Parsed only $n straps from report (need >=3)." }
    set straps [_sortStrapsTopToBottom $straps]

    puts "INFO: Parsed $n straps. Will skip first+last in order."

    set groupNets {}
    set lastAcceptedNet ""
    set currentRowKey ""

    set keptStraps 0
    set deletedStraps 0
    set warn 0
    set totalFillCalls 0

    for {set i 0} {$i < $n} {incr i} {
        lassign [lindex $straps $i] yc xll yll xur yur

        if {$i == 0} {
            puts "Strap#[expr {$i+1}] skipped (first)."
            continue
        }
        if {$i == [expr {$n-1}]} {
            puts "Strap#[expr {$i+1}] skipped (last)."
            continue
        }

        # Row/corner cluster detection => reset group logic
        set rowKey [_inferStrapRowKey $yc $::ROW_TOL $::ALL_OFFSETS $deviceRowMap]
        if {$rowKey ne "" && $rowKey ne $currentRowKey} {
            puts "INFO: Row cluster changed (device TOP-Y key $currentRowKey -> $rowKey). Resetting group logic."
            set currentRowKey $rowKey
            set groupNets {}
            set lastAcceptedNet ""
        }

        set strapObj [_findStrapRectByBBox $design $::LPP_M2 $xll $yll $xur $yur]
        if {$strapObj eq ""} {
            incr warn
            puts "WARN: Strap#[expr {$i+1}] cannot find M2 rect by bbox; skipping."
            continue
        }

        set y $yc

        # Search window anchors
        set xStart [expr {$xur - $::X_FROM_RIGHT}]
        set xStop  [expr {$xll + $::X_FROM_LEFT}]

        if {$xStart <= $xStop} {
            puts "WARN: Strap#[expr {$i+1}] bad anchor window xStop=$xStop xStart=$xStart. Deleting strap."
            _safeDestroy $strapObj
            incr deletedStraps
            continue
        }

        puts "Strap#[expr {$i+1}] yc=$y rowKey=$currentRowKey groupNets='$groupNets' lastAccepted='$lastAcceptedNet'"

        # -------- Seed SEARCH: createVia (R90) only ----------
        set acceptedNet ""
        set seedX ""

        set tries 0
        for {set x $xStart} {$x >= $xStop} {set x [expr {$x - $::STEP_X}]} {
            incr tries
            if {$tries > $::MAX_SEED_TRIES} { break }

            set pt [list $x $y]
            set vSearch [_createViaPointOrient $design $pt $::VIA_DEF_NAME R90]
            if {$vSearch eq ""} { continue }

            set net [_tryGetNetName $strapObj]
            if {$net eq ""} { set net [_tryGetNetName $vSearch] }

            if {$net eq ""} {
                _safeDestroy $vSearch
                set strapObj [_recreateStrap $design $::LPP_M2 $xll $yll $xur $yur $strapObj]
                if {$strapObj eq ""} { break }
                continue
            }

            set reject 0
            if {$::FORBID_IMMEDIATE_REPEAT && $lastAcceptedNet ne "" && $net eq $lastAcceptedNet} {
                set reject 1
            }
            if {!$reject && [lsearch -exact $groupNets $net] != -1} {
                set reject 1
            }

            if {$reject} {
                _safeDestroy $vSearch
                set strapObj [_recreateStrap $design $::LPP_M2 $xll $yll $xur $yur $strapObj]
                if {$strapObj eq ""} { break }
                continue
            }

            # ACCEPT: remember, then DELETE search via (createVia)
            set acceptedNet $net
            set seedX $x
            _safeDestroy $vSearch
            break
        }

        if {$acceptedNet eq ""} {
            puts "  FAIL: no acceptable seed net found after scan. Deleting strap."
            _safeDestroy $strapObj
            incr deletedStraps
            continue
        }

        puts "  OK: accepted net='$acceptedNet' at seedX=$seedX (placing autoVia seed now)"

        # -------- REAL seed placement: autoVia -point ----------
        set ptFinal [list $seedX $y]
        _autoViaPoint $design $ptFinal $acceptedNet

        # -------- Fill stage: autoVia -box ----------
        set boxCount 0
        for {set bx $xStart} {$bx >= $xStop} {set bx [expr {$bx - $::FILL_STEP_X}]} {
            incr boxCount
            if {$boxCount > $::MAX_FILL_BOXES} {
                incr warn
                puts "WARN: Strap#[expr {$i+1}] hit MAX_FILL_BOXES, stop fill."
                break
            }

            set x1 [expr {$bx - $::FILL_BOX_W}]
            set x2 $bx
            if {$x1 < $xll} { set x1 $xll }
            if {$x2 < $x1} { continue }

            set y1 [expr {$y - ($::FILL_BOX_H/2.0)}]
            set y2 [expr {$y + ($::FILL_BOX_H/2.0)}]
            set box [list [list $x1 $y1] [list $x2 $y2]]

            _autoViaBox $design $box $acceptedNet
            incr totalFillCalls
        }

        # Update tracking
        set lastAcceptedNet $acceptedNet
        lappend groupNets $acceptedNet
        if {[llength $groupNets] >= $::GROUP_SIZE} {
            set groupNets {}
        }

        incr keptStraps
    }

    puts "DONE: keptStraps=$keptStraps deletedStraps=$deletedStraps fillCalls=$totalFillCalls warns=$warn"
}

# Run
run_strapSeed_fill_deleteIfSameNet_GROUP3_PER_CORNER_RESET

