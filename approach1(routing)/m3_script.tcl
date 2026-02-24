########################################################################
# place_m3_by_unique_nets_from_m2_txt.tcl
# (FULL OTA height + detect power/ground + distributed over overlap span)
#
# Pattern: signal, power, ground, signal, power, ground, ...
# Gap rule: gap >= MIN_M3_GAP, and if more space exists, distribute it (bigger gap)
#
# IMPORTANT (final clarified requirement):
#   - M2 is horizontal, M3 pillars vertical.
#   - Start of M3 grid X-span = MAX XLL among M2 metals  (ignore deep-left outliers)
#   - End   of M3 grid X-span = MIN XUR among M2 metals  (ignore deep-right outliers)
#   => This gives the COMMON OVERLAP WINDOW in X.
########################################################################

# ----------------------------
# USER SETTINGS
# ----------------------------
set IN_M2_FILE  "/home/users/svgplayout2601mofikry/gonna_work/current_m2_metals_with_nets.txt"
set OUT_M3_FILE "/home/users/svgplayout2601mofikry/gonna_work/m3_coords.txt"
set IN_OTA_FILE "/home/users/svgplayout2601mofikry/gonna_work/1st_script_op.txt"

# Create pillars on M3
set LPP_M3 {M3 drawing}

# Use M2 shapes in the DB for segType/sigType classification
set LPP_M2 {M2 drawing}

# Pillar width and minimum allowed gap between adjacent pillars (edge-to-edge)
set M3_WIDTH   0.04
set MIN_M3_GAP 0.026

# Skip nets named NO_NET if present
set SKIP_NO_NET 1

# ----------------------------
# HELPERS
# ----------------------------
proc isNumber {s} {
    return [regexp {^[+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)$} $s]
}

proc _getEditDesign {} {
    set ctx [de::getActiveContext]
    if {$ctx eq ""} { return "" }
    set d ""
    catch { set d [db::getAttr editDesign -of $ctx] }
    return $d
}

proc _readM2DumpFile {fname} {
    # returns list of records: {net xll yll xur yur yc}
    set fp [open $fname r]
    set recs {}

    while {[gets $fp line] >= 0} {
        set line [string trim $line]
        if {$line eq ""} { continue }
        if {[string match "IDX*" $line]} { continue }
        if {[string match "-----*" $line]} { continue }
        if {[string match "SUMMARY:*" $line]} { continue }

        if {[regexp {^\s*([0-9]+)\s+(\S+)\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)\s*$} \
                $line -> idx net xll yll xur yur yc]} {

            if {![isNumber $xll] || ![isNumber $yll] || ![isNumber $xur] || ![isNumber $yur] || ![isNumber $yc]} {
                continue
            }
            lappend recs [list $net $xll $yll $xur $yur $yc]
        }
    }

    close $fp
    return $recs
}

proc _openOutTxt {fname} {
    set fp [open $fname w]
    puts $fp [format "%-6s %-24s %12s %12s %12s %12s %12s %12s %10s %10s" \
        "IDX" "NET" "XLL" "YLL" "XUR" "YUR" "Xc" "Yspan" "pitch" "gap"]
    puts $fp [string repeat "-" 150]
    return $fp
}

proc _readOtaBBoxY {fname} {
    # Returns {otaYBL otaYTR}
    if {![file exists $fname]} {
        error "IN_OTA_FILE not found: $fname"
    }
    set fp [open $fname r]
    set yBL ""
    set yTR ""
    while {[gets $fp line] >= 0} {
        set line [string trim $line]
        if {[regexp {OTA_BOTTOM_LEFT\s*=\s*\(\s*([-\d\.]+)\s*,\s*([-\d\.]+)\s*\)} $line -> x y]} {
            set yBL $y
        }
        if {[regexp {OTA_TOP_RIGHT\s*=\s*\(\s*([-\d\.]+)\s*,\s*([-\d\.]+)\s*\)} $line -> x y]} {
            set yTR $y
        }
    }
    close $fp

    if {$yBL eq "" || $yTR eq ""} {
        error "Failed to parse OTA_BOTTOM_LEFT / OTA_TOP_RIGHT Y from: $fname"
    }
    return [list $yBL $yTR]
}

proc _classifyNetFromShapes {design net lpp} {
    # Returns: "power" | "ground" | "signal" | "unknown"
    set shapes {}
    catch { set shapes [db::getShapes -of $design -lpp $lpp] }

    if {[llength $shapes] == 0} {
        return "unknown"
    }

    db::foreach sh $shapes {
        set shNet ""
        catch { set shNet [db::getAttr net.name -of $sh] }
        if {$shNet ne $net} { continue }

        set t ""
        catch { set t [db::getAttr net.segType -of $sh] }
        if {$t eq ""} {
            catch { set t [db::getAttr net.sigType -of $sh] }
        }

        set t [string tolower [string trim $t]]
        if {$t ne ""} {
            if {[string match "*power*"  $t]} { return "power"  }
            if {[string match "*ground*" $t]} { return "ground" }
            if {[string match "*signal*" $t]} { return "signal" }
        }
    }
    return "unknown"
}

# ----------------------------
# MAIN
# ----------------------------
proc place_m3_by_unique_nets_from_m2_txt {} {
    set design [_getEditDesign]
    if {$design eq ""} {
        error "No active edit design found. Open a layout and make it active."
    }
    if {![file exists $::IN_M2_FILE]} {
        error "IN_M2_FILE not found: $::IN_M2_FILE"
    }

    set recs [_readM2DumpFile $::IN_M2_FILE]
    if {[llength $recs] == 0} {
        error "Parsed 0 records from IN_M2_FILE. Check file formatting."
    }

    # FULL OTA height
    lassign [_readOtaBBoxY $::IN_OTA_FILE] otaYBL otaYTR
    if {$otaYTR <= $otaYBL} {
        error "Invalid OTA Y span parsed: otaYBL=$otaYBL otaYTR=$otaYTR"
    }

    # ------------------------------------------------------------
    # Unique nets + compute OVERLAP X window from M2 dump:
    #   xStart = MAX XLL  (ignore deep-left)
    #   xEnd   = MIN XUR  (ignore deep-right)
    # ------------------------------------------------------------
    set xStart ""   ;# max XLL
    set xEnd ""     ;# min XUR
    set uniqueNets {}

    foreach r $recs {
        lassign $r net xll yll xur yur yc

        if {$::SKIP_NO_NET && $net eq "NO_NET"} { continue }

        if {$xStart eq "" || $xll > $xStart} { set xStart $xll }
        if {$xEnd   eq "" || $xur < $xEnd}   { set xEnd   $xur }

        if {[lsearch -exact $uniqueNets $net] == -1} {
            lappend uniqueNets $net
        }
    }

    if {[llength $uniqueNets] == 0} {
        error "No nets found (after SKIP_NO_NET filtering)."
    }
    if {$xStart eq "" || $xEnd eq ""} {
        error "Failed to compute overlap X window (xStart/xEnd)."
    }

    set span [expr {$xEnd - $xStart}]
    if {$span <= 0.0} {
        error "No common overlap X region: xStart(maxXLL)=$xStart  xEnd(minXUR)=$xEnd  span=$span"
    }

    # ------------------------------------------------------------
    # Classify nets into signal / power / ground (from DB M2 shapes)
    # ------------------------------------------------------------
    set sigNets {}
    set pwrNets {}
    set gndNets {}

    foreach net $uniqueNets {
        set t [_classifyNetFromShapes $design $net $::LPP_M2]
        if {$t eq "power"} {
            lappend pwrNets $net
        } elseif {$t eq "ground"} {
            lappend gndNets $net
        } else {
            lappend sigNets $net
        }
    }

    # ------------------------------------------------------------
    # Build order: signal, power, ground, ...
    # ------------------------------------------------------------
    set orderedNets {}
    set ip 0
    set ig 0
    set np [llength $pwrNets]
    set ng [llength $gndNets]

    foreach s $sigNets {
        lappend orderedNets $s
        if {$np > 0} {
            lappend orderedNets [lindex $pwrNets $ip]
            set ip [expr {($ip + 1) % $np}]
        }
        if {$ng > 0} {
            lappend orderedNets [lindex $gndNets $ig]
            set ig [expr {($ig + 1) % $ng}]
        }
    }

    # If no signals exist, just alternate pwr/gnd
    if {[llength $orderedNets] == 0} {
        set i 0
        while {$i < [expr {max($np,$ng)}]} {
            if {$np > 0} { lappend orderedNets [lindex $pwrNets [expr {$i % $np}]] }
            if {$ng > 0} { lappend orderedNets [lindex $gndNets [expr {$i % $ng}]] }
            incr i
        }
    }

    set uniqueNets $orderedNets
    set N [llength $uniqueNets]
    if {$N == 0} { error "After ordering, nothing to place." }

    # ------------------------------------------------------------
    # Distribute across overlap span with minimum gap
    # ------------------------------------------------------------
    set W $::M3_WIDTH
    set minGap $::MIN_M3_GAP
    set halfW [expr {$W/2.0}]

    if {$N == 1} {
        set gapUsed 0.0
        set pitch 0.0
        set startXc [expr {$xStart + $span/2.0}]
    } else {
        set idealGap [expr {($span - $N*$W)/double($N-1)}]
        set gapUsed $idealGap

        if {$gapUsed < $minGap} {
            set gapUsed $minGap
            puts "WARN: Cannot fit N=$N pillars with W=$W and minGap=$minGap inside overlap span=$span."
            puts "WARN: Using gap=$gapUsed anyway; grid may extend past xEnd."
        }

        set pitch [expr {$W + $gapUsed}]
        set startXc [expr {$xStart + $halfW}]   ;# start at xStart (maxXLL)
    }

    puts "INFO: M2 overlap X-window: xStart(maxXLL)=$xStart  xEnd(minXUR)=$xEnd  span=$span"
    puts "INFO: N=$N  M3_WIDTH=$W  minGap=$minGap  gapUsed=$gapUsed  pitch=$pitch"
    puts "INFO: FULL OTA HEIGHT: OTA_YBL=$otaYBL OTA_YTR=$otaYTR"

    set fpOut [_openOutTxt $::OUT_M3_FILE]

    set created 0
    for {set k 0} {$k < $N} {incr k} {
        set net [lindex $uniqueNets $k]

        if {$N == 1} {
            set xc $startXc
        } else {
            set xc [expr {$startXc + $k*$pitch}]
        }

        set y1 $otaYBL
        set y2 $otaYTR

        set m3_xll [expr {$xc - $halfW}]
        set m3_xur [expr {$xc + $halfW}]
        set m3_yll $y1
        set m3_yur $y2

        set box [list [list $m3_xll $m3_yll] [list $m3_xur $m3_yur]]

        if {[catch { le::createRectangle $box -design $design -lpp $::LPP_M3 -net $net } err]} {
            puts "WARN: failed to create M3 for net=$net err=$err"
            continue
        }

        incr created
        puts $fpOut [format "%-6d %-24s %12.6f %12.6f %12.6f %12.6f %12.6f %6.3f..%6.3f %10.6f %10.6f" \
            $created $net $m3_xll $m3_yll $m3_xur $m3_yur $xc $y1 $y2 $pitch $gapUsed]
    }

    puts $fpOut ""
    puts $fpOut [format "SUMMARY: created=%d orderedNets=%d span=%.6f M3_WIDTH=%.6f gapUsed=%.6f minGap=%.6f OTA_YBL=%.6f OTA_YTR=%.6f xStart(maxXLL)=%.6f xEnd(minXUR)=%.6f" \
        $created $N $span $W $gapUsed $minGap $otaYBL $otaYTR $xStart $xEnd]
    close $fpOut

    puts "DONE: created $created M3 rectangles. Output coords: $::OUT_M3_FILE"
}

# Run
place_m3_by_unique_nets_from_m2_txt
