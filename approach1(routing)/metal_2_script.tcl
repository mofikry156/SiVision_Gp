########################################################################
# place_m2_grid_perCorner_probe3rdStrap_netSwitch_CREATEVIA_reportLikeOld.tcl
#
# Report format matches your OLD style:
#   ROW i/n  TOP=...  off=...  Yc=...  BB=(x0 y0)-(x1 y1)
#
# PLUS: for every ROW (top-right corner / row cluster), it prints which
# approach was chosen:
#   # ROW i APPROACH=1  (probe net='...')
# or
#   # ROW i APPROACH=2  (probe net='')
#
# Logic (REVERSED as you asked):
#   - For each MIDDLE row:
#       Probe on the "3rd strap" location (offset index 2 of FIRST_OFFSETS)
#       using le::createVia at (x1 - 0.009, yC), orient R90.
#       If probe via has a net  -> use FIRST_OFFSETS  (APPROACH=1)
#       Else                   -> use SECOND_OFFSETS (APPROACH=2)
#   - First and last rows always use endOffset only (EDGE rows).
########################################################################

# ----------------------------
# USER SETTINGS
# ----------------------------
set inFile  "/home/users/svgplayout2601mofikry/gonna_work/1st_script_op.txt"
set outFile "/home/users/svgplayout2601mofikry/gonna_work/m2_grid_report.txt"

set strapHeight 0.03
set rowTol      0.01
set xInset      0.101
set endOffset   0.100

# FIRST approach offsets (use when probe RETURNS a net)
set FIRST_OFFSETS  [list 0.116 0.190 0.253 0.391 0.449 0.510]

# SECOND approach offsets (use when probe returns NO net)
set SECOND_OFFSETS [list 0.059 0.118 0.178 0.309 0.377 0.458]

# Probe config (3rd strap => index 2)
set PROBE_OFFSET_IDX 2
set PROBE_X_FROM_RIGHT 0.009

# Via config
set VIA_DEF_NAME "VIA12"
set VIA_ORIENT   R90

# LPP
set LPP_M2 {M2 drawing}

# ----------------------------
# HELPERS
# ----------------------------
proc isNumber {s} { return [regexp {^[+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)$} $s] }
proc quantKey {y tol} { return [expr {round($y / $tol) * $tol}] }

proc _safeDestroy {obj} {
    if {$obj eq ""} { return }
    catch { db::destroy $obj }
    catch { le::delete  $obj }
}

proc deleteFig {fig} {
    if {$fig eq ""} { return }
    if {[llength [info commands db::isObject]] && ![db::isObject $fig]} { return }
    catch { db::destroy $fig }
    catch { le::delete $fig }
}

proc resolveM2LPP {design} {
    set candidates [list {M2 drawing} "M2 drawing" "M2:drawing" "M2"]
    foreach lpp $candidates {
        set testBox [list [list 0 0] [list 0.001 0.001]]
        set fig ""
        if {![catch { set fig [le::createRectangle $testBox -design $design -lpp $lpp] }]} {
            deleteFig $fig
            return $lpp
        }
    }
    error "Could not resolve M2 LPP. Add your PDK layer name to candidates."
}

proc createM2Strap {design lpp x0 y0 x1 y1} {
    set box [list [list $x0 $y0] [list $x1 $y1]]
    set fig ""
    if {[catch { set fig [le::createRectangle $box -design $design -lpp $lpp] } err]} {
        puts "WARN: createM2Strap failed: $err  BB=($x0 $y0)-($x1 $y1)"
        return ""
    }
    return $fig
}

proc tryGetNetName {obj} {
    if {$obj eq ""} { return "" }
    set nm ""
    catch { set nm [db::getAttr net.name -of $obj] }
    return $nm
}

proc sanityViaDef {design viaDefName} {
    set t ""
    if {[catch { set t [le::createVia -design $design -definition $viaDefName -origin {0 0} -orient R0] } err]} {
        error "VIA_DEF_NAME '$viaDefName' invalid in your tech: $err"
    }
    deleteFig $t
}

# Parse OTA + device rows (also returns parsed-good/bad like old script)
proc parseDeviceFile {fname rowTol} {
    set fp [open $fname r]

    set otaLLX ""; set otaLLY ""
    set otaURX ""; set otaURY ""

    array set rowTopY {}

    set good 0
    set bad  0

    while {[gets $fp line] >= 0} {
        set line [string trim $line]
        if {$line eq ""} { continue }

        if {[regexp {^#\s*OTA_BOTTOM_LEFT\s*=\s*\(\s*([-\d\.]+)\s*,\s*([-\d\.]+)\s*\)} $line -> x y]} {
            set otaLLX $x
            set otaLLY $y
            continue
        }
        if {[regexp {^#\s*OTA_TOP_RIGHT\s*=\s*\(\s*([-\d\.]+)\s*,\s*([-\d\.]+)\s*\)} $line -> x y]} {
            set otaURX $x
            set otaURY $y
            continue
        }

        if {[string match "INST_NAME*" $line]} { continue }
        if {[string match "#*" $line]} { continue }

        set parts [regexp -all -inline {\S+} $line]
        if {[llength $parts] < 7} { incr bad; continue }

        set ury [lindex $parts 6]
        if {![isNumber $ury]} { incr bad; continue }

        set k [quantKey $ury $rowTol]
        if {![info exists rowTopY($k)] || $ury > $rowTopY($k)} {
            set rowTopY($k) $ury
        }
        incr good
    }
    close $fp

    return [list $otaLLX $otaLLY $otaURX $otaURY [array get rowTopY] $good $bad]
}

# ----------------------------
# MAIN
# ----------------------------
proc run_place_m2_grid_perCorner_probe3rdStrap_reportLikeOld {} {
    set ctx    [de::getActiveContext]
    set design [db::getAttr editDesign -of $ctx]
    if {$design eq ""} { error "No edit design found." }

    if {![file exists $::inFile]} {
        error "Input file not found: $::inFile"
    }

    sanityViaDef $design $::VIA_DEF_NAME
    set lppM2 [resolveM2LPP $design]

    lassign [parseDeviceFile $::inFile $::rowTol] otaLLX otaLLY otaURX otaURY rowMap good bad
    array set rowTopY $rowMap

    if {$otaLLX eq "" || $otaURX eq "" || ![isNumber $otaLLX] || ![isNumber $otaURX]} {
        error "Could not parse OTA_BOTTOM_LEFT / OTA_TOP_RIGHT from file footer."
    }

    set keys [lsort -real [array names rowTopY]]
    set nRows [llength $keys]

    set x0 [expr {$otaLLX + $::xInset}]
    set x1 [expr {$otaURX - $::xInset}]
    if {$x1 <= $x0} {
        error "Bad X span after inset: x0=$x0 x1=$x1 (check xInset vs OTA width)"
    }

    set rp [open $::outFile "w"]

    # --- Header like old report ---
    puts $rp "# place_m2_grid_from_bboxfile.tcl report (per-corner PROBE on 3rd strap, createVia, REVERSED)"
    puts $rp "# inFile=$::inFile"
    puts $rp "# otaLL=($otaLLX,$otaLLY) otaUR=($otaURX,$otaURY)"
    puts $rp "# rowTol=$::rowTol strapHeight=$::strapHeight"
    puts $rp "# FIRST_OFFSETS=$::FIRST_OFFSETS"
    puts $rp "# SECOND_OFFSETS=$::SECOND_OFFSETS"
    puts $rp "# probe: idx=$::PROBE_OFFSET_IDX xFromRight=$::PROBE_X_FROM_RIGHT (from strap right edge)"
    puts $rp "# via: def=$::VIA_DEF_NAME orient=$::VIA_ORIENT"
    puts $rp "# lppM2=$lppM2"
    puts $rp "# parsed good=$good bad=$bad rows=$nRows"
    puts $rp ""

    # --- Rows ---
    for {set i 0} {$i < $nRows} {incr i} {
        set key  [lindex $keys $i]
        set topY $rowTopY($key)

        # Decide offsets + record approach per row
        set approach "EDGE"
        set probeNet ""

        if {$i == 0 || $i == ($nRows - 1)} {
            set useOffsets [list $::endOffset]
            set approach "EDGE"
        } else {
            # Probe at FIRST_OFFSETS[2]
            set probeOff [lindex $::FIRST_OFFSETS $::PROBE_OFFSET_IDX]
            set yC    [expr {$topY - $probeOff}]
            set y0_p  [expr {$yC - $::strapHeight/2.0}]
            set y1_p  [expr {$yC + $::strapHeight/2.0}]

            set probeStrap [createM2Strap $design $lppM2 $x0 $y0_p $x1 $y1_p]

            set probeX [expr {$x1 - $::PROBE_X_FROM_RIGHT}]
            set vProbe ""
            catch {
                set vProbe [le::createVia \
                    -design     $design \
                    -definition $::VIA_DEF_NAME \
                    -origin     [list $probeX $yC] \
                    -orient     $::VIA_ORIENT
                ]
            }

            if {$vProbe ne ""} {
                set probeNet [tryGetNetName $vProbe]
            }

            # cleanup probe objs
            deleteFig $vProbe
            deleteFig $probeStrap

            # REVERSED decision:
            if {$probeNet ne ""} {
                set useOffsets $::FIRST_OFFSETS
                set approach "APPROACH1"
            } else {
                set useOffsets $::SECOND_OFFSETS
                set approach "APPROACH2"
            }
        }

        # --- Per-row decision line (so you can see approach for every "top right corner") ---
        if {$approach eq "EDGE"} {
            puts $rp [format "# ROW %d/%d  TOP=%.3f  APPROACH=EDGE (endOffset only)" \
                $i [expr {$nRows-1}] $topY]
        } else {
            puts $rp [format "# ROW %d/%d  TOP=%.3f  %s (probeNet='%s')" \
                $i [expr {$nRows-1}] $topY $approach $probeNet]
        }

        # Final strap placement + OLD-style rows in report
        foreach off $useOffsets {
            set yc_final [expr {$topY - $off}]
            set y0_f     [expr {$yc_final - $::strapHeight/2.0}]
            set y1_f     [expr {$yc_final + $::strapHeight/2.0}]
            createM2Strap $design $lppM2 $x0 $y0_f $x1 $y1_f

            puts $rp [format "ROW %d/%d  TOP=%.3f  off=%.3f  Yc=%.3f  BB=(%.3f %.3f)-(%.3f %.3f)" \
                $i [expr {$nRows-1}] $topY $off $yc_final $x0 $y0_f $x1 $y1_f]
        }

        puts $rp ""  ;# blank line between corners/rows (optional, delete if you want tight output)
    }

    close $rp
    puts "DONE. Report: $::outFile"
}

run_place_m2_grid_perCorner_probe3rdStrap_reportLikeOld



